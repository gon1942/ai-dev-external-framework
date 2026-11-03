import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from subprocess import CompletedProcess
from teamdev import core, integrations, migration

class ToolIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        core.copy_assets(self.root)
    def tearDown(self):
        self.tmp.cleanup()

    def test_new_project_contains_tools_and_bridge_skill(self):
        self.assertTrue((self.root/'.ai-dev/tools.json').is_file())
        self.assertTrue((self.root/'.opencode/skills/code-graph-analysis/SKILL.md').is_file())
        self.assertTrue((self.root/'.claude/skills/code-graph-analysis/SKILL.md').is_file())
        self.assertTrue((self.root/'docs/TOOLS.md').is_file())

    def test_status_does_not_claim_hooks_or_freshness(self):
        with patch('teamdev.integrations.shutil.which', return_value='/bin/fake'):
            status = integrations.tool_status(self.root)
        self.assertTrue(status['rtk']['installed'])
        self.assertFalse(status['rtk']['native_hook_checked'])
        self.assertFalse(status['crg']['graph_freshness_verified'])

    def test_preview_is_side_effect_free_when_no_tools_installed(self):
        with patch('teamdev.integrations.shutil.which', return_value=None):
            for runtime in ('opencode', 'codex', 'claude'):
                result = integrations.setup_tool(self.root, 'rtk', runtime)
                self.assertFalse(result['executed'])
            self.assertFalse(integrations.setup_tool(self.root, 'crg')['executed'])
            self.assertFalse(integrations.build_graph(self.root)['executed'])

    def test_correct_rtk_agent_specific_commands(self):
        commands = []
        def runner(argv, **kw):
            commands.append(argv)
            return CompletedProcess(argv, 0, 'ok', '')
        with patch('teamdev.integrations.shutil.which', return_value='/bin/fake'):
            for runtime in ('opencode', 'codex', 'claude'):
                result = integrations.setup_tool(self.root, 'rtk', runtime, apply=True, runner=runner)
                self.assertTrue(result['executed'])
        self.assertEqual(commands, [integrations.RTK['opencode'], integrations.RTK['codex'], integrations.RTK['claude']])

    def test_external_tool_absence_blocks_apply_not_preview(self):
        with patch('teamdev.integrations.shutil.which', return_value=None):
            with self.assertRaises(core.WorkflowError):
                integrations.setup_tool(self.root, 'rtk', 'opencode', apply=True)
            with self.assertRaises(core.WorkflowError):
                integrations.build_graph(self.root, apply=True)

    def test_errors_do_not_claim_success(self):
        with patch('teamdev.integrations.shutil.which', return_value='/bin/fake'):
            with self.assertRaises(core.WorkflowError):
                integrations.setup_tool(self.root, 'crg', apply=True, runner=lambda a, **kw: CompletedProcess(a, 1, '', 'failure'))

    def test_upgrading_existing_project_preserves_custom_files(self):
        (self.root/'.ai-dev/tools.json').unlink()
        (self.root/'docs/TOOLS.md').unlink()
        agent_file = self.root/'AGENTS.md'
        agent_file.write_text('# custom AGENTS\n')
        conflict = self.root/'.opencode/skills/code-graph-analysis/SKILL.md'
        conflict.write_text('custom override')
        preview = migration.upgrade_tools(self.root)
        self.assertFalse(preview['applied'])
        self.assertEqual(agent_file.read_text(), '# custom AGENTS\n')
        applied = migration.upgrade_tools(self.root, apply=True)
        self.assertIn('.opencode/skills/code-graph-analysis/SKILL.md', applied['conflicts_preserved'])
        self.assertEqual(conflict.read_text(), 'custom override')
        self.assertTrue((self.root/'docs/TOOLS.md').exists())
        self.assertTrue((self.root/'.ai-dev/tools.json').exists())
        self.assertIn('Optional CLI/code-graph tools (v0.4)', agent_file.read_text())
        self.assertTrue(Path(applied['agents_backup']).is_file())
        again = migration.upgrade_tools(self.root, apply=True)
        self.assertFalse(again['agents_appended'])
        self.assertEqual(agent_file.read_text().count('## Optional CLI/code-graph tools (v0.4)'), 1)

if __name__ == '__main__':
    unittest.main()
