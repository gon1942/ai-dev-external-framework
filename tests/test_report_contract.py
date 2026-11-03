import json
import tempfile
import unittest
from pathlib import Path
from teamdev import core, migration
from teamdev.cli import main
from contextlib import redirect_stdout, redirect_stderr
from io import StringIO

class ReportContractTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        core.copy_assets(self.root)
        core.create_task(self.root, 'TASK-137', 'Report contract', 'documentation')
        self.p=core.paths(self.root,'TASK-137')
        for k in ('spec','plan'):
            x=self.p[k]
            x.write_text(x.read_text().replace('TODO','실제 검토된 명세 및 검증 계획'))
        core.plan_ready(self.root,'TASK-137','coordinator')
        core.approve(self.root,'TASK-137','user','plan','APPROVE')
        core.dispatch(self.root,'TASK-137','coordinator')
        # Legacy-only test focus: the report validation rules, not the TDD contract.
        state=core.json_read(self.p['state'])
        state.pop('tdd',None)
        core.atomic_json(self.p['state'],state)
        self.input=self.p['base']/'implementer-input.json'

    def write(self, **kwargs):
        d={'task':'TASK-137','status':'implemented','worker':'implementer',
           'changed_files':['test/page.js'],'evidence':['test.log']}
        d.update(kwargs)
        core.atomic_json(self.input,d)

    def test_template_empty_evidence_cannot_pass(self):
        result=core.report_template(self.root,'TASK-137','implementer',self.input)
        self.assertEqual(result['template']['evidence'],[])
        with self.assertRaisesRegex(core.WorkflowError,'report.evidence'):
            core.report_check(self.root,'TASK-137',self.input)
        with self.assertRaisesRegex(core.WorkflowError,'기존 파일'):
            core.report_template(self.root,'TASK-137','implementer',self.input)

    def test_markdown_rejected_before_json_parse(self):
        path=self.root/'report.md'
        path.write_text('# Report')
        with self.assertRaisesRegex(core.WorkflowError,'JSON|json'):
            core.register_report(self.root,'TASK-137','implementer',path)

    def test_field_errors_specific_and_non_mutating(self):
        for override,msg in [({'task':'WRONG'},'report.task'),
                             ({'status':'done'},'report.status'),
                             ({'worker':''},'report.worker'),
                             ({'changed_files':'file.js'},'report.changed_files'),
                             ({'evidence':[]},'report.evidence')]:
            with self.subTest(override=override):
                self.write(**override)
                with self.assertRaisesRegex(core.WorkflowError,msg):
                    core.report_check(self.root,'TASK-137',self.input)
                self.assertEqual(core.status(self.root,'TASK-137')['stage'],'IMPLEMENT')
                self.assertFalse(self.p['report'].exists())

    def test_evidence_path_and_symlink_escape_blocked(self):
        for value in ('../../etc/passwd','/etc/passwd','missing.log'):
            with self.subTest(value=value):
                self.write(evidence=[value])
                with self.assertRaises(core.WorkflowError):
                    core.report_check(self.root,'TASK-137',self.input)
        source=self.root/'outside.log'
        source.write_text('a')
        (self.p['evidence']/'link.log').symlink_to(source)
        self.write(evidence=['link.log'])
        with self.assertRaises(core.WorkflowError):
            core.report_check(self.root,'TASK-137',self.input)

    def test_success_readonly_then_report_once(self):
        (self.p['evidence']/'test.log').write_text('real log')
        self.write()
        original=self.p['state'].read_bytes()
        result=core.report_check(self.root,'TASK-137',self.input)
        self.assertTrue(result['ok'])
        self.assertEqual(self.p['state'].read_bytes(),original)
        self.assertFalse(self.p['report'].exists())
        self.assertEqual(core.register_report(self.root,'TASK-137','implementer',self.input)['stage'],'VERIFY')
        self.assertTrue(self.p['report'].exists())
        with self.assertRaises(core.WorkflowError):
            core.register_report(self.root,'TASK-137','implementer',self.input)

    def test_cli_template_and_check(self):
        out=StringIO()
        with redirect_stdout(out):
            main(['--root',str(self.root),'report-template','TASK-137','--output',str(self.input)])
        self.assertIn('implementer-input.json', out.getvalue())
        self.assertTrue(self.input.exists())

    def test_upgrade_preserves_existing_documents_and_repeat(self):
        ag=self.root/'AGENTS.md'
        ag.write_text('USER POLICY\n')
        a=migration.upgrade_report_contract(self.root)
        self.assertTrue(a['changes'])
        b=migration.upgrade_report_contract(self.root,True)
        self.assertTrue(b['applied'])
        self.assertIn('USER POLICY',ag.read_text())
        self.assertIn('## Worker report input (v0.19.1)',ag.read_text())
        self.assertEqual(migration.upgrade_report_contract(self.root)['changes'],[])

if __name__=='__main__': unittest.main()
