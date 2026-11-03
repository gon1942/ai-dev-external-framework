import tempfile
import unittest
from pathlib import Path
from teamdev import core, lifecycle, overview, audit, cli

class LifecycleIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        core.copy_assets(self.root)
        core.create_task(self.root, 'TASK-101', 'example')
    def tearDown(self):
        self.tmp.cleanup()
    def check(self):
        return lifecycle.inspect(self.root, 'TASK-101')
    def test_new_task_healthy(self):
        self.assertTrue(self.check()['ok'])
    def test_missing_spec_is_error(self):
        (self.root / 'docs/product-specs/TASK-101.md').unlink()
        self.assertIn('SPEC_MISSING', self.check()['errors'])
        self.assertTrue(overview.overview(self.root)['active'][0]['error'])
    def test_missing_state_detected_not_silently_skipped(self):
        (self.root / 'docs/tasks/TASK-101/state.json').unlink()
        self.assertIn('STATE_MISSING', self.check()['errors'])
        self.assertEqual(len(overview.overview(self.root)['active']), 1)
    def test_missing_plan_detected(self):
        (self.root / 'docs/exec-plans/active/TASK-101/plan.md').unlink()
        self.assertIn('PLAN_FILE_MISSING', self.check()['errors'])
    def test_both_plan_folders_detected(self):
        (self.root / 'docs/exec-plans/completed/TASK-101').mkdir(parents=True)
        self.assertIn('DUPLICATE_PLAN', self.check()['errors'])
    def test_unfinished_archived_detected(self):
        a = self.root / 'docs/exec-plans/active/TASK-101'
        d = self.root / 'docs/exec-plans/completed/TASK-101'
        d.parent.mkdir(parents=True)
        a.rename(d)
        self.assertIn('UNFINISHED_ARCHIVED', self.check()['errors'])
    def test_completed_without_archive_and_approval(self):
        p = self.root / 'docs/tasks/TASK-101/state.json'
        s = core.json_read(p); s['stage'] = 'COMPLETE'; s['status'] = 'COMPLETED'
        core.atomic_json(p, s)
        self.assertIn('FINAL_APPROVAL_MISSING', self.check()['errors'])
        self.assertIn('COMPLETED_NOT_ARCHIVED', self.check()['errors'])
    def test_approved_plan_tamper(self):
        p = core.paths(self.root, 'TASK-101')
        for k in ('spec', 'plan'):
            p[k].write_text(p[k].read_text().replace('TODO', 'Enough actual acceptance criteria and implementation details'))
        core.plan_ready(self.root, 'TASK-101', 'coord')
        core.approve(self.root, 'TASK-101', 'human', 'plan', 'APPROVE')
        self.assertTrue(self.check()['ok'])
        p['plan'].write_text(p['plan'].read_text() + '\nunauthorized change')
        self.assertIn('APPROVED_DOC_CHANGED', self.check()['errors'])
    def test_strict_exit_and_audit_error(self):
        (self.root / 'docs/product-specs/TASK-101.md').unlink()
        self.assertEqual(cli.main(['--root', str(self.root), 'lifecycle-check', '--strict']), 2)
        self.assertTrue(any(x['severity']=='ERROR' and x['item']=='TASK-101' for x in audit.audit(self.root)['issues']))
    def test_orphan_plan_without_state_detected(self):
        (self.root / 'docs/tasks/TASK-101/state.json').unlink()
        (self.root / 'docs/tasks/TASK-101').rename(self.root / 'docs/tasks/TASK-101-hidden')
        # Hidden orphan still a separate invalid Task ID; original plan must be flagged
        rows = lifecycle.check(self.root)['tasks']
        original = [x for x in rows if x['task']=='TASK-101'][0]
        self.assertIn('STATE_MISSING', original['errors'])

if __name__ == '__main__': unittest.main()
