import os
import tempfile
import unittest
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch
from teamdev import core, integrations, migration


class CrgAutoTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        core.copy_assets(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def test_empty_project_skips_without_running_graph(self):
        with patch('teamdev.integrations.shutil.which', return_value='/bin/fake'):
            state = integrations.auto_graph(self.root, apply=True, runner=lambda *a, **kw: self.fail('must not execute'))
        self.assertEqual(state['action'], 'SKIP_EMPTY')
        self.assertFalse(state['executed'])

    def test_missing_binary_fallback_even_with_code(self):
        (self.root/'app.js').write_text('console.log("ok")')
        with patch('teamdev.integrations.shutil.which', return_value=None):
            state = integrations.auto_graph(self.root, apply=True)
        self.assertEqual(state['action'], 'FALLBACK_NO_CRG')
        self.assertFalse(state['executed'])

    def test_source_present_build_and_rebuild(self):
        code = self.root/'app.js'
        code.write_text('console.log(1)')
        graph = self.root/'.code-review-graph/graph.db'
        graph.parent.mkdir()
        calls = []
        def runner(cmd, **kw):
            calls.append(cmd)
            graph.write_bytes(b'graph placeholder for local integration test')
            return CompletedProcess(cmd, 0, 'ok', '')
        with patch('teamdev.integrations.shutil.which', return_value='/bin/fake'):
            preview = integrations.auto_graph(self.root)
            self.assertEqual(preview['action'], 'BUILD')
            self.assertFalse(graph.exists())
            result = integrations.auto_graph(self.root, apply=True, runner=runner)
            self.assertEqual(result['result'], 'GRAPH_CREATED')
            self.assertEqual(calls[-1], ['code-review-graph','build'])
            self.assertEqual(integrations.auto_graph(self.root)['action'], 'READY_CANDIDATE')
            newer = graph.stat().st_mtime + 2
            os.utime(code, (newer, newer))
            self.assertEqual(integrations.auto_graph(self.root)['action'], 'REBUILD')
            self.assertTrue(integrations.auto_graph(self.root, apply=True, runner=runner)['executed'])

    def test_ignores_generated_files_and_other_project_assets(self):
        (self.root/'node_modules').mkdir()
        (self.root/'node_modules/index.js').write_text('generated')
        (self.root/'docs').mkdir(exist_ok=True)
        (self.root/'docs/README.md').write_text('docs')
        with patch('teamdev.integrations.shutil.which', return_value='/bin/fake'):
            self.assertEqual(integrations.graph_auto_status(self.root)['action'], 'SKIP_EMPTY')

    def test_existing_project_upgrade_idempotent_and_preserves_custom_skill(self):
        skill = self.root/'.opencode/skills/code-graph-analysis/SKILL.md'
        skill.write_text('custom skill')
        assert 'code-graph-analysis' not in skill.read_text()
        p = migration.upgrade_crg_auto(self.root)
        self.assertFalse(p['applied'])
        self.assertEqual(skill.read_text(), 'custom skill')
        a = migration.upgrade_crg_auto(self.root, apply=True)
        self.assertTrue(a['updated'])
        self.assertIn('custom skill', skill.read_text())
        self.assertIn('CRG On-Demand Lifecycle', skill.read_text())
        self.assertFalse(migration.upgrade_crg_auto(self.root, apply=True)['updated'])

if __name__ == '__main__':
    unittest.main()
