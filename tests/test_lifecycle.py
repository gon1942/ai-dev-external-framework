import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from teamdev import core, overview, migration


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.root = Path(self.t.name)
        core.copy_assets(self.root)
        core.create_task(self.root, 'TASK-001', 'Test task')
        p = core.paths(self.root, 'TASK-001')
        for k in ('spec', 'plan'):
            p[k].write_text(p[k].read_text().replace('TODO', '실제 작업 사양과 검증 조건의 상세 설명입니다.'))
        core.plan_ready(self.root, 'TASK-001', 'planner')
        core.approve(self.root, 'TASK-001', 'human', 'plan', 'APPROVE')
        core.dispatch(self.root, 'TASK-001', 'coordinator')
        (p['evidence'] / 'log.txt').write_text('real test log')
        report = self.root / 'r.json'
        report.write_text(json.dumps({'task':'TASK-001','worker':'implementer','status':'implemented','changed_files':[],'evidence':['log.txt']}))
        core.register_report(self.root, 'TASK-001', 'coordinator', report)
        verify = self.root / 'v.json'
        verify.write_text(json.dumps({'task':'TASK-001','verifier':'verifier','result':'PASS','checks':[{'command':'test','exit_code':0}]}))
        core.verify(self.root, 'TASK-001', 'verifier', verify)
        review = self.root / 'w.json'
        review.write_text(json.dumps({'task':'TASK-001','reviewer':'reviewer','result':'PASS','blocking_findings':0}))
        core.review(self.root, 'TASK-001', 'reviewer', review)

    def tearDown(self):
        self.t.cleanup()

    def test_final_approval_moves_entire_folder_and_summary(self):
        p = core.paths(self.root, 'TASK-001')
        (p['plan'].parent / 'context-handoff.md').write_text('session handoff retained')
        before = overview.overview(self.root)
        self.assertEqual(len(before['active']), 1)
        self.assertEqual(before['active'][0]['next_action'], 'AWAIT_FINAL_APPROVAL')
        result = core.approve(self.root, 'TASK-001', 'human', 'completion', 'APPROVE')
        self.assertEqual(result['status'], 'COMPLETED')
        self.assertFalse(p['plan'].parent.exists())
        after_path = core.paths(self.root, 'TASK-001')
        self.assertTrue(after_path['plan'].is_file())
        self.assertTrue(after_path['rotation_handoff'].is_file())
        self.assertEqual(core.digest(after_path['plan']), result['approvals']['plan']['plan_sha256'])
        summary = overview.overview(self.root)
        self.assertFalse(summary['active'])
        self.assertEqual(summary['completed'][0]['next_action'], 'NONE')
        self.assertEqual(summary['completed'][0]['plan_dir'], 'docs/exec-plans/completed/TASK-001')
        with self.assertRaises(core.WorkflowError):
            core.approve(self.root, 'TASK-001', 'human', 'completion', 'APPROVE')

    def test_atomic_state_failure_restores_active(self):
        real = core.atomic_json
        with patch.object(core, 'atomic_json', side_effect=OSError('disk full')):
            with self.assertRaises(OSError):
                core.approve(self.root, 'TASK-001', 'human', 'completion', 'APPROVE')
        self.assertTrue((self.root / 'docs/exec-plans/active/TASK-001/plan.md').exists())
        self.assertEqual(core.status(self.root, 'TASK-001')['status'], 'AWAITING_FINAL_APPROVAL')

    def test_conflicting_destination_blocks(self):
        dst = self.root / 'docs/exec-plans/completed/TASK-001'
        dst.mkdir(parents=True)
        with self.assertRaises(core.WorkflowError):
            core.approve(self.root, 'TASK-001', 'human', 'completion', 'APPROVE')

    def test_legacy_archive(self):
        state, p = core._load(self.root, 'TASK-001')
        state['status'] = 'COMPLETED'
        state['approvals']['completion'] = {'actor':'human'}
        core.atomic_json(p['state'], state)
        self.assertEqual(core.archive_legacy_completed(self.root, 'TASK-001')['applied'], False)
        self.assertTrue(core.archive_legacy_completed(self.root, 'TASK-001', apply=True)['applied'])
        self.assertEqual(len(overview.overview(self.root)['completed']), 1)

    def test_permissions_merges_and_backs_up_agent(self):
        cfg = self.root / 'opencode.json'
        data = core.json_read(cfg); data.pop('permission', None); core.atomic_json(cfg, data)
        agent = self.root / '.opencode/agents/coordinator.md'
        agent.write_text(agent.read_text().replace('  bash:\n    "*": allow\n    "git commit *": ask\n    "git push *": ask\n    "git reset --hard *": deny\n    "rm -rf *": ask\n', '  bash: ask\n'))
        result = migration.upgrade_permissions(self.root)
        self.assertTrue(result['agent_patch'])
        self.assertFalse(result['applied'])
        result = migration.upgrade_permissions(self.root, apply=True)
        self.assertTrue(result['applied'])
        data = core.json_read(self.root / 'opencode.json')
        self.assertEqual(data['permission']['bash']['*'], 'allow')
        agent = (self.root / '.opencode/agents/coordinator.md').read_text()
        self.assertIn('"git push *": ask', agent)
        with self.assertRaises(core.WorkflowError):
            migration.upgrade_permissions(self.root, apply=True)

    def test_lifecycle_migration_idempotent(self):
        p = self.root / 'docs/SESSION-START.md'
        p.unlink()
        self.assertTrue(migration.upgrade_lifecycle(self.root, apply=True)['applied'])
        self.assertTrue(p.exists())
        self.assertEqual(migration.upgrade_lifecycle(self.root)['changes'], [])


if __name__ == '__main__':
    unittest.main()
