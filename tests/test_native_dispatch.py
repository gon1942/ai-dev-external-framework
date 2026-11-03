import json
import tempfile
import unittest
from pathlib import Path
from teamdev import core, orchestrator, monitor, migration


class NativeDispatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        core.copy_assets(self.root)
        core.create_task(self.root, 'LOGIN-001', 'Login')
        self.paths = core.paths(self.root, 'LOGIN-001')

    def approve(self):
        for key in ('spec', 'plan'):
            p = self.paths[key]
            p.write_text(p.read_text().replace('TODO', '상세한 승인 명세 및 검증 정책을 실제로 기술함'))
        core.plan_ready(self.root, 'LOGIN-001', 'coordinator')
        core.approve(self.root, 'LOGIN-001', 'user', 'plan', 'APPROVE')

    def test_preapproval_worker_preparation_blocks(self):
        with self.assertRaises(core.WorkflowError):
            orchestrator.prepare_worker(self.root, 'LOGIN-001', 'implementer')
        self.assertEqual(core.status(self.root, 'LOGIN-001')['status'], 'DRAFT')

    def test_dispatch_once_and_monitored_truthfully(self):
        self.approve()
        before = monitor.one(self.root, 'LOGIN-001')
        self.assertEqual(before['activity'], 'UNTRACKED')
        x = orchestrator.prepare_worker(self.root, 'LOGIN-001', 'implementer')
        self.assertEqual(x['action'], 'RUN_IMPLEMENTER')
        self.assertFalse(x['native_invoked'])
        self.assertEqual(core.status(self.root, 'LOGIN-001')['status'], 'DISPATCHED')
        y = orchestrator.prepare_worker(self.root, 'LOGIN-001', 'implementer')
        self.assertEqual(y['action'], 'RUN_IMPLEMENTER')
        hist = core.status(self.root, 'LOGIN-001')['history']
        self.assertEqual([h['action'] for h in hist].count('dispatch'), 1)
        m = monitor.one(self.root, 'LOGIN-001')
        self.assertTrue(m['launch_ready'])
        self.assertEqual(m['activity'], 'UNTRACKED')
        self.assertIsNone(m['session_id'])

    def test_reject_wrong_role_and_active_worker(self):
        self.approve()
        with self.assertRaises(core.WorkflowError):
            orchestrator.prepare_worker(self.root, 'LOGIN-001', 'verifier')
        orchestrator.prepare_worker(self.root, 'LOGIN-001', 'implementer')
        monitor.start(self.root, 'LOGIN-001', 'implementer', 'live-session')
        with self.assertRaisesRegex(core.WorkflowError, '활성 Worker'):
            orchestrator.prepare_worker(self.root, 'LOGIN-001', 'implementer')

    def test_synchronous_return_does_not_fabricate_running(self):
        self.approve()
        orchestrator.prepare_worker(self.root, 'LOGIN-001', 'implementer')
        result = monitor.observe_return(self.root, 'LOGIN-001', 'implementer', 'real-task-s1', 'FINISHED')
        self.assertEqual(result['source'], 'native-return-reported')
        snap = monitor.one(self.root, 'LOGIN-001')
        self.assertEqual(snap['activity'], 'IDLE')
        self.assertEqual(snap['last_outcome'], 'FINISHED')
        self.assertIsNone(snap['worker'])
        with self.assertRaises(core.WorkflowError):
            monitor.observe_return(self.root, 'LOGIN-001', 'implementer', 'real-task-s1', 'FINISHED')
        with self.assertRaises(core.WorkflowError):
            monitor.observe_return(self.root, 'LOGIN-001', 'implementer', 'bad', 'RUNNING')

    def test_all_role_transitions_and_returns(self):
        self.approve()
        orchestrator.prepare_worker(self.root, 'LOGIN-001', 'implementer')
        self.paths['evidence'].joinpath('test.log').write_text('mock test result')
        report = self.root / 'r.json'
        report.write_text(json.dumps({'task':'LOGIN-001','worker':'implementer','status':'implemented',
                        'changed_files':[],'evidence':['test.log']}))
        core.register_report(self.root, 'LOGIN-001', 'implementer', report)
        monitor.observe_return(self.root, 'LOGIN-001', 'implementer', 's1', 'FINISHED')
        self.assertEqual(orchestrator.prepare_worker(self.root, 'LOGIN-001', 'verifier')['action'], 'RUN_VERIFIER')
        verification = self.root / 'v.json'
        verification.write_text(json.dumps({'task':'LOGIN-001','verifier':'verifier','result':'PASS',
                                              'checks':[{'command':'python -m unittest','exit_code':0}]}))
        core.verify(self.root, 'LOGIN-001', 'verifier', verification)
        monitor.observe_return(self.root, 'LOGIN-001', 'verifier', 's2', 'FINISHED')
        self.assertEqual(orchestrator.prepare_worker(self.root, 'LOGIN-001', 'reviewer')['action'], 'RUN_REVIEWER')
        monitor.observe_return(self.root, 'LOGIN-001', 'reviewer', 's3', 'FINISHED')
        self.assertEqual(core.status(self.root, 'LOGIN-001')['status'], 'AWAITING_REVIEW')
        self.assertEqual(len(json.loads(self.paths['base'].joinpath('activity.json').read_text())['history']),3)

    def test_upgrade_append_only_idempotent(self):
        c = self.root/'.opencode/agents/coordinator.md'
        content = c.read_text()
        c.write_text(content.replace('## Native Worker Dispatch and Monitoring (v0.17)', '## Native Worker Dispatch and Monitoring (old)'))
        preview = migration.upgrade_worker_dispatch(self.root)
        self.assertIn('.opencode/agents/coordinator.md',preview['append_to'])
        result = migration.upgrade_worker_dispatch(self.root,True)
        self.assertIn('.opencode/agents/coordinator.md',result['updated'])
        self.assertEqual(migration.upgrade_worker_dispatch(self.root)['append_to'],[])
        self.assertIn('## Native Worker Dispatch and Monitoring (v0.17)',c.read_text())


if __name__ == '__main__': unittest.main()
