import json
import tempfile
import unittest
from pathlib import Path
from teamdev import core, overview, skill_events, startup, migration, cli

class VisibilityTests(unittest.TestCase):
    def setUp(self):
        self.ctx=tempfile.TemporaryDirectory()
        self.root=Path(self.ctx.name)
        core.copy_assets(self.root)
    def tearDown(self): self.ctx.cleanup()

    def test_empty_dashboard_and_startup(self):
        board=overview.dashboard(self.root)
        self.assertEqual(board['counts'], {'pending':0,'completed':0,'approval_waiting':0,'blocked':0,'total':0})
        self.assertIn('TASK | 단계 | 상태 | 사용자 조치',startup.render(startup.snapshot(self.root)))
        self.assertEqual(cli.main(['--root',str(self.root),'session-summary']),0)

    def test_draft_and_plan_approval_action(self):
        core.create_task(self.root,'TEST-001','Example')
        board=overview.dashboard(self.root)
        self.assertEqual(board['counts']['pending'],1)
        self.assertEqual(board['tasks'][0]['next_action'],'요구사항 분석 및 Spec/Plan 작성')
        p=self.root/'docs/product-specs/TEST-001.md'
        plan=self.root/'docs/exec-plans/active/TEST-001/plan.md'
        p.write_text('## Requirement\nAC: verifiable test case.\nThe application must satisfy a clear login or output acceptance condition.',encoding='utf-8')
        plan.write_text('## Plan\nImplement a test and capture stdout and stderr. Verify via python -m unittest, rollback changes, and inspect the produced evidence.',encoding='utf-8')
        core.plan_ready(self.root,'TEST-001','coordinator')
        board=overview.dashboard(self.root)
        self.assertEqual(board['counts']['approval_waiting'],1)
        self.assertEqual(board['tasks'][0]['user_action'],'계획 승인/수정')

    def test_skill_history_stage_and_tamper(self):
        core.create_task(self.root,'TEST-001','Example')
        evidence=self.root/'docs/tasks/TEST-001/evidence/skill.log'
        evidence.write_text('skill tool was requested',encoding='utf-8')
        skill_events.record(self.root,'TEST-001','task-orchestration','coordinator','session-01','skill.log')
        out=skill_events.history(self.root)
        self.assertEqual(out['count'],1)
        self.assertEqual(out['by_stage']['ANALYZE'][0]['integrity'],'MATCH')
        self.assertFalse(out['events'][0]['verified_loaded_by_runtime'])
        evidence.write_text('altered')
        self.assertEqual(skill_events.history(self.root)['integrity_errors'],1)
        self.assertIn('증거 불일치 1건',startup.render(startup.snapshot(self.root)))
        self.assertEqual(cli.main(['--root',str(self.root),'skill-history','--task','TEST-001']),0)

    def test_orphan_task_detected_in_dashboard(self):
        self.root.joinpath('docs/exec-plans/active/ORPHAN').mkdir(parents=True)
        self.root.joinpath('docs/exec-plans/active/ORPHAN/plan.md').write_text('broken',encoding='utf-8')
        board=overview.dashboard(self.root)
        self.assertGreaterEqual(board['counts']['blocked'],1)
        self.assertTrue(any(x['status']=='BLOCKED' for x in board['tasks']))

    def test_upgrade_preserves_custom_and_idempotent(self):
        p=self.root/'AGENTS.md'
        p.write_text(p.read_text().split(migration.VISIBILITY_MARKER)[0]+'\nMY CUSTOM RULE',encoding='utf-8')
        (self.root/'docs/SKILL-HISTORY.md').unlink()
        self.assertTrue(migration.upgrade_visibility(self.root)['changes'])
        data=migration.upgrade_visibility(self.root,True)
        self.assertTrue(data['applied'])
        self.assertIn('MY CUSTOM RULE',p.read_text())
        self.assertTrue((self.root/'docs/SKILL-HISTORY.md').is_file())
        self.assertFalse(migration.upgrade_visibility(self.root)['changes'])

if __name__=='__main__':unittest.main()
