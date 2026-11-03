import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from teamdev import core, orchestrator


class OrchestratorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        core.copy_assets(self.root)
        core.create_task(self.root, "TASK-100", "Login")
        self.p = core.paths(self.root, "TASK-100")

    def approve(self):
        for key in ("spec", "plan"):
            self.p[key].write_text(self.p[key].read_text().replace("TODO", "확인한 테스트 케이스와 역할 및 설계 검토 내용을 상세하게 기록합니다"))
        core.plan_ready(self.root, "TASK-100", "planner")
        core.approve(self.root, "TASK-100", "owner", "plan", "APPROVE")

    def test_preapproval_never_invokes_worker(self):
        with patch("shutil.which", return_value="/bin/mock"):
            result = orchestrator.drive(self.root, "TASK-100", "opencode", execute=True,
                runner=lambda *a, **k: self.fail("worker must not start"))
        self.assertEqual(result["action"], "ANALYZE_PLAN")

    def test_preview_does_not_change_state(self):
        self.approve()
        result = orchestrator.drive(self.root, "TASK-100", "opencode")
        self.assertEqual(result["action"], "DISPATCH_IMPLEMENTER")
        self.assertEqual(core.status(self.root, "TASK-100")["status"], "APPROVED")

    def test_driver_launches_three_real_runner_invocations(self):
        self.approve()
        calls = []
        class Result:
            returncode = 0
        def fake_runner(command, cwd, check):
            self.assertEqual(cwd, str(self.root))
            calls.append(command)
            role = ["implementer", "verifier", "reviewer"][len(calls)-1]
            self.assertEqual(command[3], role)
            if role == "implementer":
                (self.p["evidence"] / "test.log").write_text("executed mock tests")
                f = self.root / "report.json"
                f.write_text(json.dumps({"task":"TASK-100", "worker":"implementer", "status":"implemented", "changed_files":[], "evidence":["test.log"]}))
                core.register_report(self.root, "TASK-100", "coordinator", f)
            elif role == "verifier":
                f = self.root / "verify.json"
                f.write_text(json.dumps({"task":"TASK-100", "verifier":"verifier", "result":"PASS", "checks":[{"command":"mock test", "exit_code":0}]}))
                core.verify(self.root, "TASK-100", "verifier", f)
            else:
                f = self.root / "review.json"
                f.write_text(json.dumps({"task":"TASK-100", "reviewer":"reviewer", "result":"PASS", "blocking_findings":0}))
                core.review(self.root, "TASK-100", "reviewer", f)
            return Result()
        with patch("shutil.which", return_value="/bin/mock"):
            out = orchestrator.drive(self.root, "TASK-100", "opencode", execute=True, runner=fake_runner)
        self.assertEqual(len(calls), 3)
        self.assertEqual(out["action"], "AWAIT_FINAL_APPROVAL")
        self.assertEqual(core.status(self.root, "TASK-100")["status"], "AWAITING_FINAL_APPROVAL")

    def test_no_worker_report_fails_closed(self):
        self.approve()
        class Result:
            returncode = 0
        with patch("shutil.which", return_value="/bin/mock"):
            with self.assertRaisesRegex(core.WorkflowError, "상태 전이가 없습니다"):
                orchestrator.drive(self.root, "TASK-100", "opencode", execute=True,
                    runner=lambda *args, **kwargs: Result())
        self.assertEqual(core.status(self.root, "TASK-100")["status"], "DISPATCHED")

    def test_nonzero_exit_fails_closed(self):
        self.approve()
        class Result:
            returncode = 2
        with patch("shutil.which", return_value="/bin/mock"):
            with self.assertRaisesRegex(core.WorkflowError, "종료코드 2"):
                orchestrator.drive(self.root, "TASK-100", "opencode", execute=True,
                    runner=lambda *args, **kwargs: Result())

    def test_rotation_creates_second_process(self):
        self.approve()
        calls = []
        class Result:
            returncode = 0
        def fake_runner(command, cwd, check):
            calls.append(command)
            role = command[3]
            if role == "implementer" and len(calls) == 1:
                core.rotation_request(self.root, "TASK-100", "implementer", "session-a", self.root,
                    "write auth test", "build/test boundary", "auth implementation partly done")
            elif role == "implementer":
                self.assertIn("Resume", command[-1])
                (self.p["evidence"] / "test.log").write_text("test proof")
                f = self.root / "report.json"
                f.write_text(json.dumps({"task":"TASK-100", "worker":"implementer", "status":"implemented", "changed_files":[], "evidence":["test.log"]}))
                core.register_report(self.root, "TASK-100", "coordinator", f)
            elif role == "verifier":
                f = self.root / "verify.json"
                f.write_text(json.dumps({"task":"TASK-100", "verifier":"verifier", "result":"PASS", "checks":[{"command":"mock", "exit_code":0}]}))
                core.verify(self.root, "TASK-100", "verifier", f)
            elif role == "reviewer":
                f = self.root / "review.json"
                f.write_text(json.dumps({"task":"TASK-100", "reviewer":"reviewer", "result":"PASS", "blocking_findings":0}))
                core.review(self.root, "TASK-100", "reviewer", f)
            return Result()
        with patch("shutil.which", return_value="/bin/mock"):
            out = orchestrator.drive(self.root, "TASK-100", "opencode", execute=True, runner=fake_runner)
        self.assertEqual(len(calls), 4)
        self.assertEqual(out["action"], "AWAIT_FINAL_APPROVAL")
        self.assertEqual(core.status(self.root, "TASK-100")["rotation"]["sequence"], 1)

    def test_docs_changed_blocks_driver(self):
        self.approve()
        self.p["plan"].write_text(self.p["plan"].read_text() + "\nextra")
        with self.assertRaises(core.WorkflowError):
            orchestrator.drive(self.root, "TASK-100", "opencode", execute=True)


if __name__ == "__main__":
    unittest.main()
