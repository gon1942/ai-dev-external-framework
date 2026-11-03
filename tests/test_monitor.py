import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from teamdev import core, monitor, migration, orchestrator


class MonitorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        core.copy_assets(self.root)
        core.create_task(self.root, 'TASK-501', 'Worker monitor test')
        self.p = core.paths(self.root, 'TASK-501')

    def approve_dispatch(self):
        for name in ('spec', 'plan'):
            self.p[name].write_text(self.p[name].read_text().replace('TODO', '테스트 계획과 실제 검증 근거 및 사용 범위를 확인합니다'))
        core.plan_ready(self.root, 'TASK-501', 'planner')
        core.approve(self.root, 'TASK-501', 'human', 'plan', 'APPROVE')
        core.dispatch(self.root, 'TASK-501', 'coordinator')

    def test_untracked_does_not_claim_running(self):
        self.assertEqual(monitor.one(self.root, 'TASK-501')['activity'], 'UNTRACKED')
        self.approve_dispatch()
        self.assertEqual(monitor.one(self.root, 'TASK-501')['activity'], 'UNTRACKED')

    def test_heartbeat_and_exit(self):
        self.approve_dispatch()
        started = monitor.start(self.root, 'TASK-501', 'implementer', 'session-1')
        self.assertEqual(started['status'], 'RUNNING')
        self.assertEqual(monitor.one(self.root, 'TASK-501')['activity'], 'RECENT_ACTIVITY')
        self.assertEqual(monitor.heartbeat(self.root, 'TASK-501', 'session-1')['session_id'], 'session-1')
        monitor.stop(self.root, 'TASK-501', 'session-1', 'FINISHED')
        self.assertEqual(monitor.one(self.root, 'TASK-501')['activity'], 'IDLE')
        data = json.loads((self.p['base'] / 'activity.json').read_text())
        self.assertEqual(data['history'][0]['status'], 'FINISHED')

    def test_wrong_session_rejected(self):
        self.approve_dispatch()
        monitor.start(self.root, 'TASK-501', 'implementer', 'one')
        with self.assertRaises(core.WorkflowError):
            monitor.heartbeat(self.root, 'TASK-501', 'two')
        with self.assertRaises(core.WorkflowError):
            monitor.stop(self.root, 'TASK-501', 'two', 'FINISHED')
        with self.assertRaises(core.WorkflowError):
            monitor.start(self.root, 'TASK-501', 'implementer', 'three')

    def test_approval_required(self):
        with self.assertRaises(core.WorkflowError):
            monitor.start(self.root, 'TASK-501', 'implementer', 'one')

    def test_wrong_stage_rejected(self):
        self.approve_dispatch()
        with self.assertRaises(core.WorkflowError):
            monitor.start(self.root, 'TASK-501', 'reviewer', 'one')

    def test_stale_activity(self):
        self.approve_dispatch()
        monitor.start(self.root, 'TASK-501', 'implementer', 'one')
        path = self.p['base'] / 'activity.json'
        data = json.loads(path.read_text())
        data['current']['last_heartbeat'] = '2020-01-01T00:00:00+00:00'
        path.write_text(json.dumps(data))
        self.assertEqual(monitor.one(self.root, 'TASK-501', stale_seconds=20)['activity'], 'STALE')

    def test_missing_local_pid(self):
        self.approve_dispatch()
        monitor.start(self.root, 'TASK-501', 'implementer', 'one', pid=99999999, source='cli-driver')
        with patch('teamdev.monitor._pid_alive', return_value=False):
            self.assertEqual(monitor.one(self.root, 'TASK-501')['activity'], 'PROCESS_EXITED')

    def test_upgrade_monitor_non_destructive(self):
        original = (self.root / 'AGENTS.md').read_text()
        result = migration.upgrade_monitor(self.root, apply=False)
        self.assertFalse(result['applied'])
        self.assertEqual(original, (self.root / 'AGENTS.md').read_text())
        self.assertTrue(migration.upgrade_monitor(self.root, apply=True)['applied'])
        self.assertTrue((self.root / 'docs/MONITOR.md').exists())
        self.assertTrue((self.root / '.opencode/skills/worker-activity-monitor/SKILL.md').exists())
        self.assertFalse(migration.upgrade_monitor(self.root, apply=False)['changes'])

    def test_list_tasks(self):
        self.assertEqual(len(monitor.all_tasks(self.root)), 1)
        self.assertIn('TASK-501', monitor.render(monitor.all_tasks(self.root)))

    def test_driver_records_session(self):
        self.approve_dispatch()
        class Result:
            returncode = 3
        def runner(*a, **kw):
            self.assertEqual(monitor.one(self.root, 'TASK-501')['activity'], 'RECENT_ACTIVITY')
            return Result()
        with patch('shutil.which', return_value='/bin/mock'):
            with self.assertRaises(core.WorkflowError):
                orchestrator.drive(self.root, 'TASK-501', 'opencode', execute=True, runner=runner)
        history = json.loads((self.p['base']/'activity.json').read_text())['history']
        self.assertEqual(history[-1]['status'], 'FAILED')
        self.assertEqual(monitor.one(self.root, 'TASK-501')['activity'], 'IDLE')


if __name__ == '__main__':
    unittest.main()
