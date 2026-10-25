import tempfile, pathlib, subprocess, sys, json, unittest
SCRIPT=pathlib.Path(__file__).resolve().parents[1]/'scripts/workflow.py'
class GateTests(unittest.TestCase):
 def test_wrong_test_command_blocked(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d); dest=root/'scripts';dest.mkdir();(dest/'workflow.py').write_bytes(SCRIPT.read_bytes())
   base=root/'docs/exec-plans/active/TASK-001';base.mkdir(parents=True)
   (base/'status.json').write_text(json.dumps({'approved':True}))
   (base/'spec.md').write_text('spec');(base/'plan.md').write_text('plan')
   (base/'ac-tests.json').write_text(json.dumps({'AC-01':['python3 -V']}))
   r=subprocess.run([sys.executable,str(dest/'workflow.py'),'run','--id','TASK-001','--ac','AC-01','--','python3','-c','print(123)'],text=True,capture_output=True)
   self.assertEqual(r.returncode,2);self.assertIn('not declared',r.stderr)
 def test_openspec_requires_actual_change(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);dest=root/'scripts';dest.mkdir();(dest/'workflow.py').write_bytes(SCRIPT.read_bytes())
   (root/'.ai-dev').mkdir();(root/'.ai-dev/spec-adapter.json').write_text(json.dumps({'mode':'openspec','source':'openspec/changes'}))
   base=root/'docs/exec-plans/active/TASK-001';base.mkdir(parents=True)
   (base/'status.json').write_text(json.dumps({'approved':False}))
   (base/'spec.md').write_text('spec');(base/'plan.md').write_text('plan');(base/'ac-tests.json').write_text(json.dumps({'AC-01':['python3 -V']}))
   r=subprocess.run([sys.executable,str(dest/'workflow.py'),'approve','--id','TASK-001','--user-confirmed'],text=True,capture_output=True)
   self.assertEqual(r.returncode,2);self.assertIn('openspec_change_id',r.stderr)
if __name__=='__main__':unittest.main()
