import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from teamdev import core, progress, migration, cli


class ProgressTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        core.copy_assets(self.root)

    def tearDown(self): self.tmp.cleanup()

    def test_empty_and_missing_task(self):
        p = progress.snapshot(self.root)
        self.assertEqual(p['counts']['pending'],0)
        self.assertIn('등록된 TASK가 없습니다',progress.render(p))
        with self.assertRaises(core.WorkflowError):
            progress.snapshot(self.root,'NOT-FOUND')

    def test_task_draft_and_read_only(self):
        core.create_task(self.root,'DEMO-001','Test demo')
        state=self.root/'docs/tasks/DEMO-001/state.json'
        original=state.read_bytes()
        p=progress.snapshot(self.root,'DEMO-001')
        self.assertEqual(p['tasks'][0]['stage'],'ANALYZE')
        self.assertEqual(p['tasks'][0]['activity'],'UNTRACKED')
        self.assertNotIn('RUNNING',progress.render(p))
        self.assertEqual(state.read_bytes(),original)
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(cli.main(['--root',str(self.root),'progress','--task','DEMO-001','--json']),0)
        self.assertEqual(json.loads(out.getvalue())['tasks'][0]['task'],'DEMO-001')

    def test_approval_action_and_phase(self):
        core.create_task(self.root,'DEMO-001','Test demo')
        spec=self.root/'docs/product-specs/DEMO-001.md'
        plan=self.root/'docs/exec-plans/active/DEMO-001/plan.md'
        spec.write_text('## Requirement\nAC: verifiable test case.\nThe application must satisfy a clear login or output acceptance condition.',encoding='utf-8')
        plan.write_text('## Plan\nImplement a test and capture stdout and stderr. Verify via python -m unittest, rollback changes, and inspect the produced evidence.',encoding='utf-8')
        core.plan_ready(self.root,'DEMO-001','coordinator')
        p=progress.snapshot(self.root,'DEMO-001')
        self.assertEqual(p['counts']['approval_waiting'],1)
        self.assertEqual(p['tasks'][0]['user_action'],'계획 승인/수정')
        self.assertIn('[PLAN]',progress.render(p))
        self.assertIn('사용자 계획 승인 대기',progress.render(p))

    def test_upgrade_adds_policy_and_is_idempotent(self):
        prompt=self.root/'.opencode/agents/coordinator.md'
        original=prompt.read_text().split(migration.PROGRESS_MARKER)[0].rstrip()+'\n\nCUSTOM DIRECTIVE\n'
        prompt.write_text(original,encoding='utf-8')
        doc=self.root/'docs/PROGRESS.md'
        doc.unlink()
        before=migration.upgrade_progress(self.root)
        self.assertFalse(before['applied'])
        self.assertTrue(before['changes'])
        applied=migration.upgrade_progress(self.root,True)
        self.assertTrue(applied['applied'])
        self.assertIn('CUSTOM DIRECTIVE',prompt.read_text())
        self.assertIn(migration.PROGRESS_MARKER,prompt.read_text())
        self.assertTrue(doc.exists())
        self.assertFalse(migration.upgrade_progress(self.root)['changes'])
        self.assertIsNotNone(applied['backup'])

    def test_no_unsupported_running_claim(self):
        core.create_task(self.root,'DEMO-001','Test demo')
        p=progress.snapshot(self.root,'DEMO-001')
        self.assertIn('Worker 실행 관측 기록 없음',progress.render(p))
        self.assertIn('RECENT_ACTIVITY ≠ 실행 중 확정',progress.render(p))

if __name__=='__main__': unittest.main()
