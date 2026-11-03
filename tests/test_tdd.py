import json
import tempfile
import unittest
from pathlib import Path
from teamdev import core, tdd, migration

class TddTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        core.copy_assets(self.root)

    def setup_task(self, typ='feature', task='TASK-900'):
        core.create_task(self.root,task,'TDD example',typ)
        p=core.paths(self.root,task)
        for k in ('spec','plan'):
            p[k].write_text(p[k].read_text().replace('TODO','실제 검증 가능한 상세 설명 및 단계별 구현과 검증 절차'),encoding='utf-8')
        core.plan_ready(self.root,task,'coordinator')
        core.approve(self.root,task,'human','plan','APPROVE')
        core.dispatch(self.root,task,'coordinator')
        return p

    def make_evidence(self,p,typ='feature'):
        if typ in tdd.REQUIRED:
            m={'task':'TASK-900','type':typ,'mode':'required','cycles':[{'red':{'command':'npm test','exit_code':1,'log':'red.log','expected_failure':'기대 기능 미구현으로 실패'},'green':{'command':'npm test','exit_code':0,'log':'green.log'},'refactor':{'command':'npm test','exit_code':0,'log':'refactor.log','review':'코드 정리 검토, 회귀 확인'}}]}
            logs=['red.log','green.log','refactor.log']
        else:
            c=tdd.classify(typ)
            m={'task':'TASK-900','type':typ,'mode':c['mode'],'strategy':c['strategy'],'rationale':'선택된 작업 유형에 따른 검증 방식','checks':[{'command':'npm run verify','exit_code':0,'log':'check.log'}]}
            logs=['check.log']
        for name in logs:
            (p['evidence']/name).write_text('실제 실행 결과 예시: '+name)
        (p['evidence']/'tdd-manifest.json').write_text(json.dumps(m,ensure_ascii=False))
        return ['tdd-manifest.json',*logs]

    def report(self,p,evidence):
        f=self.root/'report.json'
        f.write_text(json.dumps({'task':'TASK-900','worker':'implementer','status':'implemented','changed_files':['src/index.ts'],'evidence':evidence}))
        return core.register_report(self.root,'TASK-900','coordinator',f)

    def verify(self):
        f=self.root/'verify.json'
        f.write_text(json.dumps({'task':'TASK-900','verifier':'verifier','result':'PASS','checks':[{'command':'npm test','exit_code':0}]}))
        return core.verify(self.root,'TASK-900','verifier',f)

    def test_required_missing_manifest_blocks_report(self):
        p=self.setup_task()
        (p['evidence']/'test.log').write_text('test pass')
        with self.assertRaisesRegex(core.WorkflowError,'tdd-manifest'):
            self.report(p,['test.log'])
        self.assertEqual(core.status(self.root,'TASK-900')['stage'],'IMPLEMENT')

    def test_required_red_must_fail(self):
        p=self.setup_task()
        logs=self.make_evidence(p)
        m=json.loads((p['evidence']/'tdd-manifest.json').read_text())
        m['cycles'][0]['red']['exit_code']=0
        (p['evidence']/'tdd-manifest.json').write_text(json.dumps(m))
        with self.assertRaisesRegex(core.WorkflowError,'RED'):
            self.report(p,logs)

    def test_required_complete_flow_and_tamper(self):
        p=self.setup_task()
        logs=self.make_evidence(p)
        self.report(p,logs)
        self.assertEqual(tdd.check(self.root,'TASK-900')['status'],'EVIDENCE_VALIDATED')
        (p['evidence']/'red.log').write_text('tampered')
        with self.assertRaisesRegex(core.WorkflowError,'해시'):
            self.verify()
        (p['evidence']/'red.log').write_text('실제 실행 결과 예시: red.log')
        self.verify()
        f=self.root/'review.json'
        f.write_text(json.dumps({'task':'TASK-900','reviewer':'reviewer','result':'PASS','blocking_findings':0}))
        core.review(self.root,'TASK-900','reviewer',f)
        core.approve(self.root,'TASK-900','human','completion','APPROVE')
        self.assertTrue((self.root/'docs/exec-plans/completed/TASK-900/plan.md').is_file())

    def test_alternative_ui_and_documentation(self):
        for typ in ('ui_visual','configuration','refactoring','documentation'):
            with self.subTest(typ=typ):
                self.setUp()
                p=self.setup_task(typ)
                self.report(p,self.make_evidence(p,typ))
                self.verify()

    def test_type_changes_only_in_draft(self):
        core.create_task(self.root,'TASK-901','sample','feature')
        self.assertEqual(tdd.set_type(self.root,'TASK-901','documentation','coordinator')['mode'],'exempt')
        p=core.paths(self.root,'TASK-901')
        for k in ('spec','plan'):
            p[k].write_text(p[k].read_text().replace('TODO','충분히 구체적인 검증 계획과 수용 기준'))
        core.plan_ready(self.root,'TASK-901','coordinator')
        with self.assertRaises(core.WorkflowError):
            tdd.set_type(self.root,'TASK-901','bugfix','coordinator')

    def test_approved_policy_tamper_blocks_report(self):
        p=self.setup_task()
        logs=self.make_evidence(p)
        state=core.status(self.root,'TASK-900')
        state['tdd']['mode']='exempt'
        core.atomic_json(p['state'],state)
        with self.assertRaisesRegex(core.WorkflowError,'TDD 정책'):
            self.report(p,logs)

    def test_non_destructive_upgrade_and_idempotence(self):
        result=migration.upgrade_tdd(self.root, apply=False)
        self.assertTrue(result['changes'])
        before=(self.root/'AGENTS.md').read_text()
        migration.upgrade_tdd(self.root,apply=True)
        self.assertIn('Task-Type TDD Policy', (self.root/'AGENTS.md').read_text())
        self.assertTrue((self.root/'docs/TDD-POLICY.md').is_file())
        self.assertIn(before,(self.root/'AGENTS.md').read_text())
        second=migration.upgrade_tdd(self.root,apply=False)
        self.assertEqual(second['changes'],[])

    def test_legacy_tasks_are_not_reclassified(self):
        core.create_task(self.root,'TASK-LEGACY','legacy')
        self.assertNotIn('tdd',core.status(self.root,'TASK-LEGACY'))
        self.assertEqual(tdd.check(self.root,'TASK-LEGACY')['status'],'LEGACY_UNCLASSIFIED')

if __name__=='__main__':unittest.main()
