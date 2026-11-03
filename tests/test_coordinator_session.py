import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from teamdev import core, coordinator_session as cs, orchestrator, cli, migration, monitor


class CoordinatorRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        core.copy_assets(self.root)
        core.create_task(self.root, 'TASK-REC-001', 'Orca 회전 테스트')

    def tearDown(self):
        self.tmp.cleanup()

    def prepare(self, **kwargs):
        defaults = dict(session_id='orca-coordinator-one', next_action='Plan 문서 계속 작성', reason='단계 경계')
        defaults.update(kwargs)
        return cs.prepare(self.root, 'TASK-REC-001', **defaults)

    def test_prepare_resume_and_next_gate(self):
        self.prepare()
        self.assertEqual(cs.status(self.root, 'TASK-REC-001')['phase'], 'PREPARED')
        with self.assertRaises(core.WorkflowError):
            orchestrator.next_step(self.root, 'TASK-REC-001')
        with self.assertRaises(core.WorkflowError):
            cs.resume(self.root, 'TASK-REC-001', 'orca-two', False)
        with self.assertRaises(core.WorkflowError):
            cs.resume(self.root, 'TASK-REC-001', 'orca-coordinator-one', True)
        result = cs.resume(self.root, 'TASK-REC-001', 'orca-two', True)
        self.assertEqual(result['next_action'], 'Plan 문서 계속 작성')
        self.assertEqual(orchestrator.next_step(self.root, 'TASK-REC-001')['action'], 'ANALYZE_PLAN')
        self.assertEqual(core.status(self.root,'TASK-REC-001')['approvals'], {})
        self.assertEqual(cs.status(self.root,'TASK-REC-001')['session_id'],'orca-two')
        with self.assertRaises(core.WorkflowError):
            self.prepare(session_id='orca-coordinator-one')
        self.prepare(session_id='orca-two')

    def test_rejects_tampering_and_state_change(self):
        self.prepare()
        path=self.root/'docs/tasks/TASK-REC-001/coordinator-handoff.md'
        path.write_text(path.read_text().replace('단계 경계','임의 수정'))
        with self.assertRaises(core.WorkflowError):
            cs.resume(self.root,'TASK-REC-001','orca-two',True)

    def test_worker_running_rejected(self):
        from teamdev import core as c
        base=self.root/'docs/tasks/TASK-REC-001/activity.json'
        c.atomic_json(base,{'schema':1,'task':'TASK-REC-001','current':{'status':'RUNNING'},'history':[]})
        with self.assertRaises(core.WorkflowError):
            self.prepare()

    def test_secrets_rejected_and_no_freeze(self):
        with self.assertRaises(core.WorkflowError):
            self.prepare(summary='api_key=some-secret-token')
        self.assertEqual(cs.status(self.root,'TASK-REC-001')['phase'],'NONE')

    def test_cli_blocks_mutations_until_resume(self):
        self.prepare()
        with contextlib.redirect_stderr(io.StringIO()):
            result=cli.main(['--root',str(self.root),'plan-ready','TASK-REC-001','--actor','coordinator'])
        self.assertEqual(result,2)
        with contextlib.redirect_stdout(io.StringIO()):
            result=cli.main(['--root',str(self.root),'coordinator-resume','TASK-REC-001',
                             '--new-session-id','orca-two','--old-session-stopped'])
        self.assertEqual(result,0)

    def test_upgrade_non_destructive(self):
        f=self.root/'.opencode/agents/coordinator.md'
        f.write_text(f.read_text().split(migration.COORDINATOR_RECOVERY_MARKER)[0]+'\nCUSTOM')
        (self.root/'docs/COORDINATOR-RECOVERY.md').unlink()
        before=migration.upgrade_coordinator_recovery(self.root)
        self.assertTrue(before['changes'])
        result=migration.upgrade_coordinator_recovery(self.root,True)
        self.assertTrue(result['applied'])
        self.assertIn('CUSTOM',f.read_text())
        self.assertTrue((self.root/'docs/COORDINATOR-RECOVERY.md').exists())
        self.assertFalse(migration.upgrade_coordinator_recovery(self.root)['changes'])


if __name__=='__main__': unittest.main()
