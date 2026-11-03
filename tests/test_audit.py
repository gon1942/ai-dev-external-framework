import json
import tempfile
import unittest
from pathlib import Path
from teamdev import core, audit, migration, skill_events, startup, cli


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        core.copy_assets(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def test_agents_and_skills_discovered_but_not_claimed_loaded(self):
        info = audit.audit(self.root)
        self.assertTrue(any(a['id']=='opencode_coordinator_entry' and a['status']=='PASS' for a in info['agents']))
        self.assertTrue(any(a['id']=='claude_coordinator_entry' and a['status']=='PASS' for a in info['agents']))
        self.assertTrue(any(a['id']=='codex_coordinator_policy' and a['status']=='CONFIG_ONLY' for a in info['agents']))
        for s in info['skills']['bundled']:
            self.assertTrue(s['source_present'])
            self.assertTrue(all(s['native_discovery_files'].values()))
            self.assertEqual(s['loaded_in_model'], 'NOT_VERIFIED')
        self.assertEqual(info['runtime_e2e'], 'NOT_VERIFIED')
        self.assertIn('NOT_VERIFIED', audit.render(info))

    def test_missing_skill_and_bad_primary_flagged(self):
        (self.root/'.opencode/skills/context-handoff/SKILL.md').unlink()
        cfg = self.root/'opencode.json'
        d = json.loads(cfg.read_text()); d['default_agent']='build'
        cfg.write_text(json.dumps(d))
        info = audit.audit(self.root)
        ids = [x['item'] for x in info['issues'] if x['severity']=='ERROR']
        self.assertIn('skill:context-handoff',ids)
        self.assertIn('opencode_coordinator_entry',ids)
        self.assertEqual(info['status'],'CHECK_REQUIRED')

    def test_external_skills_optional_and_not_assumed_loaded(self):
        skill = audit.skill_inventory(self.root)['external_recommended']['general'][0]
        self.assertEqual(skill['loaded_in_model'],'NOT_VERIFIED')
        self.assertIn('opencode',skill['discovery_files'])

    def test_task_and_startup_independent_of_model_progress(self):
        core.create_task(self.root, 'TASK-001', 'Test')
        info = audit.audit(self.root)
        self.assertEqual(info['tasks']['active'][0]['task'], 'TASK-001')
        start = startup.snapshot(self.root)
        self.assertEqual(start['runtime_checks']['native_worker_dispatch'], 'NOT_VERIFIED')
        self.assertIn('teamdev audit', startup.render(start))

    def test_skill_evidence_tamper_and_path_traversal(self):
        core.create_task(self.root, 'TASK-001','Example')
        directory = self.root/'docs/tasks/TASK-001/evidence'
        (directory/'call.log').write_text('skill tool called for analysis',encoding='utf-8')
        ev = skill_events.record(self.root,'TASK-001','code-graph-analysis','coordinator','session-a','call.log')
        self.assertFalse(ev['verified_loaded_by_runtime'])
        self.assertEqual(skill_events.list_events(self.root,'TASK-001')['events'][0]['evidence_integrity'],'MATCH')
        (directory/'call.log').write_text('modified',encoding='utf-8')
        self.assertEqual(skill_events.list_events(self.root,'TASK-001')['events'][0]['evidence_integrity'],'MISSING_OR_CHANGED')
        with self.assertRaises(core.WorkflowError):
            skill_events.record(self.root,'TASK-001','foo','coordinator','s','../../AGENTS.md')
        with self.assertRaises(core.WorkflowError):
            skill_events.record(self.root,'TASK-001','foo','reviewer','s','call.log')

    def test_upgrade_preserves_custom_text_and_is_idempotent(self):
        p = self.root/'AGENTS.md'
        p.write_text(p.read_text().split(migration.AUDIT_MARKER)[0] + '\nCUSTOM RULE\n')
        for rel in ('.opencode/agents/coordinator.md','.claude/agents/coordinator.md'):
            q = self.root/rel
            q.write_text(q.read_text().split(migration.AUDIT_MARKER)[0])
        (self.root/'docs/RUNTIME-AUDIT.md').unlink()
        self.assertTrue(migration.upgrade_audit(self.root)['changes'])
        self.assertTrue(migration.upgrade_audit(self.root,apply=True)['applied'])
        self.assertIn('CUSTOM RULE',p.read_text())
        self.assertFalse(migration.upgrade_audit(self.root)['changes'])

    def test_cli_audit_strict(self):
        self.assertEqual(cli.main(['--root',str(self.root),'audit','--strict']),0)
        (self.root/'.opencode/agents/coordinator.md').unlink()
        self.assertEqual(cli.main(['--root',str(self.root),'audit','--strict']),2)


if __name__ == '__main__': unittest.main()
