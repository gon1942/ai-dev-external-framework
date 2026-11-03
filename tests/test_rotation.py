import json
import tempfile
import unittest
from pathlib import Path
from teamdev import core


class RotationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        core.copy_assets(self.root)
        core.create_task(self.root, 'TASK-001', 'Rotation')
        self.p = core.paths(self.root, 'TASK-001')
        for key in ('spec', 'plan'):
            self.p[key].write_text(self.p[key].read_text().replace('TODO', '검증된 상세 구현 및 검증 요구사항'), encoding='utf-8')
        core.plan_ready(self.root, 'TASK-001', 'planner')
        core.approve(self.root, 'TASK-001', 'owner', 'plan', 'APPROVE')
        core.dispatch(self.root, 'TASK-001', 'coordinator')
        self.worktree = self.root / 'worktree'
        self.worktree.mkdir()

    def rotate(self, **kwargs):
        options = dict(actor='dev-a', session_id='worker-01', worktree=self.worktree,
                       next_action='실패 테스트 재현', reason='BUILD-TEST 경계',
                       completed='로그인 로직 변경', changed_files='src/login.py',
                       verification='test.log 저장', blockers='none')
        options.update(kwargs)
        return core.rotation_request(self.root, 'TASK-001', **options)

    def test_rotation_success_and_short_bootstrap(self):
        result = self.rotate()
        self.assertEqual(result['event'], 'CONTEXT_HANDOFF_REQUIRED')
        self.assertFalse(result['worker_done'])
        self.assertTrue(self.p['rotation_handoff'].is_file())
        with self.assertRaises(core.WorkflowError):
            core.rotation_resume(self.root, 'TASK-001', 'coordinator', False, 'worker-02')
        response = core.rotation_resume(self.root, 'TASK-001', 'coordinator', True, 'worker-02')
        self.assertEqual(response['next_action'], '실패 테스트 재현')
        self.assertEqual(core.status(self.root, 'TASK-001')['rotation']['sequence'], 1)
        self.assertEqual(core.status(self.root, 'TASK-001')['status'], 'DISPATCHED')
        with self.assertRaises(core.WorkflowError):
            core.rotation_resume(self.root, 'TASK-001', 'coordinator', True, 'worker-03')
        self.rotate(session_id='worker-02')

    def test_no_final_worker_done_during_rotation(self):
        self.rotate()
        report = self.root / 'report.json'
        report.write_text(json.dumps({'task':'TASK-001','worker':'dev-a','status':'implemented',
                                      'changed_files':[], 'evidence':['test.log']}))
        (self.p['evidence'] / 'test.log').write_text('PASS')
        with self.assertRaises(core.WorkflowError):
            core.register_report(self.root, 'TASK-001', 'coordinator', report)

    def test_tampered_handoff_rejected(self):
        self.rotate()
        path = self.p['rotation_handoff']
        path.write_text(path.read_text().replace('실패 테스트 재현', '다른 작업'))
        with self.assertRaises(core.WorkflowError):
            core.rotation_resume(self.root, 'TASK-001', 'coordinator', True, 'worker-02')

    def test_changed_approved_plan_rejected(self):
        self.rotate()
        self.p['plan'].write_text(self.p['plan'].read_text() + '변경')
        with self.assertRaises(core.WorkflowError):
            core.rotation_resume(self.root, 'TASK-001', 'coordinator', True, 'worker-02')

    def test_secret_rejected(self):
        with self.assertRaises(core.WorkflowError):
            self.rotate(blockers='api_key=super-secret-value')
        self.assertEqual(core.status(self.root, 'TASK-001')['rotation']['phase'], 'ACTIVE')

    def test_same_worktree_mandatory(self):
        self.rotate()
        core.rotation_resume(self.root, 'TASK-001', 'coordinator', True, 'worker-02')
        other = self.root / 'other'; other.mkdir()
        with self.assertRaises(core.WorkflowError):
            self.rotate(session_id='worker-02', worktree=other)

    def test_default_coordinator_installed(self):
        self.assertEqual(json.loads((self.root/'opencode.json').read_text())['default_agent'], 'coordinator')
        self.assertEqual(json.loads((self.root/'.claude/settings.json').read_text())['agent'], 'coordinator')
        self.assertTrue((self.root/'CLAUDE.md').exists())
        self.assertTrue(core.doctor(self.root)['ok'])


if __name__ == '__main__':
    unittest.main()
