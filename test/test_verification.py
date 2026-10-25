import tempfile, pathlib, json, unittest, subprocess, sys
SCRIPT=pathlib.Path(__file__).resolve().parents[1]/'scripts/verification.py'
class VerificationTests(unittest.TestCase):
 def test_profiles_preview_and_missing(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);(root/'.ai-dev').mkdir();(root/'.ai-dev/verification-profiles.json').write_text(json.dumps({'profiles':{'python':{'patterns':['*.py'],'checks':{'test':['python3','-V']}}}}))
   r=subprocess.run([sys.executable,str(SCRIPT),'--project',d,'--files','main.py'],capture_output=True,text=True)
   self.assertEqual(r.returncode,0,r.stderr);self.assertIn('python',r.stdout)
   r=subprocess.run([sys.executable,str(SCRIPT),'--project',d,'--files','main.java'],capture_output=True,text=True)
   self.assertEqual(r.returncode,2);self.assertIn('NO_MATCHING_PROFILE',r.stdout)
 def test_safe_run(self):
  with tempfile.TemporaryDirectory() as d:
   root=pathlib.Path(d);(root/'.ai-dev').mkdir();(root/'.ai-dev/verification-profiles.json').write_text(json.dumps({'profiles':{'python':{'patterns':['*.py'],'checks':{'test':['python3','-V']}}}}))
   r=subprocess.run([sys.executable,str(SCRIPT),'--project',d,'--files','main.py','--run'],capture_output=True,text=True)
   self.assertEqual(r.returncode,0,r.stderr);self.assertIn('exit_code',r.stdout)
if __name__=='__main__':unittest.main()
