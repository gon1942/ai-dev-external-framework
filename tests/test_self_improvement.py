import tempfile
import unittest
from pathlib import Path
from teamdev import core, improvements, migration

class SelfImprovementTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        core.copy_assets(self.root)
    def tearDown(self):
        self.tmp.cleanup()
    def test_new_project_docs(self):
        self.assertTrue((self.root/'docs/SELF-IMPROVEMENT.md').is_file())
        self.assertIn('Self-Improvement Approval Gate', (self.root/'AGENTS.md').read_text())
    def test_candidate_never_edits_policy_until_final_approval_and_apply(self):
        original = (self.root/'AGENTS.md').read_bytes()
        improvements.propose(self.root,'IMPROVE-101','Improve AGENTS','Repeated errors in task dispatch and missing safe guard evidence')
        self.assertEqual((self.root/'AGENTS.md').read_bytes(), original)
        source = self.root/'proposal.md'
        source.write_bytes(original + b'\n# Good rule\n')
        with self.assertRaises(core.WorkflowError):
            improvements.stage(self.root,'IMPROVE-101','AGENTS.md',source)
        # Use real lifecycle after approval; staging remains separate until final apply.
        p=core.paths(self.root,'IMPROVE-101')
        p['spec'].write_text('# Full spec\n'+'Problem and requirements. '*20)
        p['plan'].write_text('# Full plan\n'+'Implementation tests and rollback. '*20+'\n## Approved policy targets\n- AGENTS.md\n')
        core.plan_ready(self.root,'IMPROVE-101','coordinator')
        core.approve(self.root,'IMPROVE-101','human','plan','APPROVE')
        core.dispatch(self.root,'IMPROVE-101','coordinator')
        improvements.stage(self.root,'IMPROVE-101','AGENTS.md',source)
        self.assertEqual((self.root/'AGENTS.md').read_bytes(), original)
        self.assertFalse(improvements.inspect(self.root,'IMPROVE-101')['ready_to_apply'])
        with self.assertRaises(core.WorkflowError):
            improvements.apply(self.root,'IMPROVE-101','human','APPLY',execute=True)
        # Simulate verified workflow state for gate-only unit test.
        s=core.json_read(p['state'])
        s.update(stage='COMPLETE',status='COMPLETED')
        s['approvals']['completion']={'actor':'human','at':core.now()}
        core.atomic_json(p['state'],s)
        (self.root/'docs/exec-plans/completed').mkdir(parents=True,exist_ok=True)
        p['plan'].parent.rename(self.root/'docs/exec-plans/completed/IMPROVE-101')
        for name in ('report','verification','review'):
            core.atomic_json(p[name], {'status':'pass','task':'IMPROVE-101'})
        self.assertTrue(improvements.inspect(self.root,'IMPROVE-101')['ready_to_apply'])
        self.assertFalse(improvements.apply(self.root,'IMPROVE-101','','',execute=False)['applied'])
        with self.assertRaises(core.WorkflowError):
            improvements.apply(self.root,'IMPROVE-101','coordinator','APPLY',execute=True)
        result=improvements.apply(self.root,'IMPROVE-101','human','APPLY',execute=True)
        self.assertTrue(result['applied'])
        self.assertEqual((self.root/'AGENTS.md').read_bytes(), source.read_bytes())
        with self.assertRaises(core.WorkflowError):
            improvements.apply(self.root,'IMPROVE-101','human','APPLY',execute=True)
    def test_changed_original_blocks_apply(self):
        improvements.propose(self.root,'IMPROVE-102','Change rule','Observed repeated defects with logs and policy contract concerns')
        p=core.paths(self.root,'IMPROVE-102')
        p['spec'].write_text('Full spec '*40);p['plan'].write_text('Full plan '*40+'\n- AGENTS.md\n')
        core.plan_ready(self.root,'IMPROVE-102','coordinator')
        core.approve(self.root,'IMPROVE-102','human','plan','APPROVE')
        core.dispatch(self.root,'IMPROVE-102','coordinator')
        src=self.root/'newmd.md';src.write_text('# New good policy\n')
        improvements.stage(self.root,'IMPROVE-102','AGENTS.md',src)
        (self.root/'AGENTS.md').write_text('# Concurrent change\n')
        s=core.json_read(p['state']);s['stage']='COMPLETE';s['status']='COMPLETED';s['approvals']['completion']={'actor':'human'}
        core.atomic_json(p['state'],s)
        (self.root/'docs/exec-plans/completed').mkdir(parents=True,exist_ok=True)
        p['plan'].parent.rename(self.root/'docs/exec-plans/completed/IMPROVE-102')
        for n in ('report','verification','review'):
            core.atomic_json(p[n],{'ok':True})
        self.assertFalse(improvements.inspect(self.root,'IMPROVE-102')['ready_to_apply'])
        with self.assertRaises(core.WorkflowError):
            improvements.apply(self.root,'IMPROVE-102','human','APPLY',True)
    def test_upgrade_no_overwrite_and_idempotent(self):
        (self.root/'docs/SELF-IMPROVEMENT.md').unlink()
        md=self.root/'AGENTS.md'; md.write_text('# Custom instructions\n')
        preview=migration.upgrade_self_improvement(self.root)
        self.assertFalse(preview['applied'])
        self.assertEqual(md.read_text(),'# Custom instructions\n')
        result=migration.upgrade_self_improvement(self.root,True)
        self.assertTrue(result['applied'])
        self.assertTrue((self.root/'docs/SELF-IMPROVEMENT.md').exists())
        self.assertIn('Self-Improvement Approval Gate',md.read_text())
        self.assertFalse(migration.upgrade_self_improvement(self.root,True)['applied'])

if __name__ == '__main__': unittest.main()
