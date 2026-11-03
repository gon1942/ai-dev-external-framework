import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from teamdev import core, startup, migration

class StartupTests(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.root = Path(self.t.name)
        core.copy_assets(self.root)
    def tearDown(self):
        self.t.cleanup()
    def test_banner_has_phases_skills_and_no_fake_running(self):
        info = startup.snapshot(self.root)
        self.assertEqual(len(info['active']), 0)
        self.assertIn('task-orchestration', startup.render(info))
        self.assertIn('IMPLEMENTER', startup.render(info))
        self.assertFalse(info['tools']['rtk_hook_verified'])
    def test_active_task_shown_without_starting_worker(self):
        core.create_task(self.root, 'TASK-001', 'Example')
        info = startup.snapshot(self.root)
        self.assertEqual(info['active'][0]['task'], 'TASK-001')
        self.assertIn('ANALYZE_PLAN', startup.render(info))
        self.assertIn('UNTRACKED', startup.render(info))
    def test_launch_prints_then_runs_cli_only(self):
        class Proc: returncode=7
        with patch('teamdev.startup.shutil.which',return_value='/usr/bin/opencode'):
            calls=[]
            def runner(argv,**kw):
                calls.append((argv,kw['cwd']))
                return Proc()
            self.assertEqual(startup.launch(self.root,'opencode',runner=runner),7)
            self.assertEqual(calls[0][0], ['/usr/bin/opencode'])
    def test_upgrade_old_coordinator_and_idempotent(self):
        agent = self.root/'.opencode/agents/coordinator.md'
        current = agent.read_text()
        rules = migration.COORDINATOR_EDIT_RULES
        agent.write_text(current.replace(rules,'  edit: ask\n').split(migration.STARTUP_MARKER)[0])
        for rel in ['AGENTS.md','.claude/agents/coordinator.md']:
            p = self.root/rel
            p.write_text(p.read_text().split(migration.STARTUP_MARKER)[0])
        (self.root/'docs/STARTUP-DASHBOARD.md').unlink()
        preview = migration.upgrade_startup(self.root)
        self.assertFalse(preview['applied'])
        self.assertTrue(preview['changes'])
        result = migration.upgrade_startup(self.root, apply=True)
        self.assertTrue(result['applied'])
        self.assertIn(rules,agent.read_text())
        self.assertEqual(migration.upgrade_startup(self.root)['changes'],[])
    def test_custom_permission_blocks_update(self):
        agent = self.root/'.opencode/agents/coordinator.md'
        agent.write_text(agent.read_text().replace(migration.COORDINATOR_EDIT_RULES,'  edit: deny\n'))
        self.assertTrue(migration.upgrade_startup(self.root)['conflicts'])
        with self.assertRaises(core.WorkflowError):
            migration.upgrade_startup(self.root,apply=True)
        self.assertIn('  edit: deny',agent.read_text())

if __name__ == '__main__': unittest.main()
