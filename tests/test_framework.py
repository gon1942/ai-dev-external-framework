import json
import tempfile
import unittest
from pathlib import Path
from teamdev import core


class FrameworkTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        core.copy_assets(self.root)
        core.create_task(self.root, "TASK-001", "Example")
        self.p = core.paths(self.root, "TASK-001")

    def prepare(self):
        for k in ("spec", "plan"):
            self.p[k].write_text(self.p[k].read_text().replace("TODO", "확인 가능한 요구사항과 충분한 검증 절차"), encoding="utf-8")
        core.plan_ready(self.root, "TASK-001", "planner")
        core.approve(self.root, "TASK-001", "owner", "plan", "APPROVE")

    def test_install_non_destructive(self):
        f = self.root / "AGENTS.md"
        f.write_text("my own policy")
        core.copy_assets(self.root)
        self.assertEqual(f.read_text(), "my own policy")

    def test_approval_required(self):
        with self.assertRaises(core.WorkflowError):
            core.dispatch(self.root, "TASK-001", "coordinator")

    def test_placeholder_blocks_plan(self):
        with self.assertRaises(core.WorkflowError):
            core.plan_ready(self.root, "TASK-001", "planner")

    def test_approval_document_mutation_blocks_dispatch(self):
        self.prepare()
        self.p["spec"].write_text(self.p["spec"].read_text() + "\nSCOPE CHANGE")
        with self.assertRaises(core.WorkflowError):
            core.dispatch(self.root, "TASK-001", "coordinator")

    def test_wrong_confirmation_blocks(self):
        for k in ("spec", "plan"):
            self.p[k].write_text(self.p[k].read_text().replace("TODO", "검토한 상세 정책과 실증 테스트 케이스"))
        core.plan_ready(self.root, "TASK-001", "planner")
        with self.assertRaises(core.WorkflowError):
            core.approve(self.root, "TASK-001", "owner", "plan", "YES")

    def test_bad_task_id(self):
        with self.assertRaises(core.WorkflowError):
            core.create_task(self.root, "../secret", "Bad")

    def test_full_flow_and_independence(self):
        self.prepare()
        core.dispatch(self.root, "TASK-001", "coordinator")
        evidence = self.p["evidence"] / "test.log"
        evidence.write_text("unit tests pass")
        report_file = self.root / "report.json"
        report_file.write_text(json.dumps({"task":"TASK-001", "worker":"dev1", "status":"implemented", "changed_files":["app.py"], "evidence":["test.log"]}))
        core.register_report(self.root, "TASK-001", "coordinator", report_file)
        verify_file = self.root / "verify.json"
        verify_file.write_text(json.dumps({"task":"TASK-001", "verifier":"dev1", "result":"PASS", "checks":[{"command":"python -m unittest", "exit_code":0}]}))
        with self.assertRaises(core.WorkflowError):
            core.verify(self.root, "TASK-001", "dev1", verify_file)
        verify_file.write_text(json.dumps({"task":"TASK-001", "verifier":"qa", "result":"PASS", "checks":[{"command":"python -m unittest", "exit_code":0}]}))
        core.verify(self.root, "TASK-001", "qa", verify_file)
        review_file = self.root / "review.json"
        review_file.write_text(json.dumps({"task":"TASK-001", "reviewer":"lead", "result":"PASS", "blocking_findings":0}))
        with self.assertRaises(core.WorkflowError):
            core.review(self.root, "TASK-001", "dev1", review_file)
        core.review(self.root, "TASK-001", "lead", review_file)
        with self.assertRaises(core.WorkflowError):
            core.approve(self.root, "TASK-001", "", "completion", "APPROVE")
        result = core.approve(self.root, "TASK-001", "product-owner", "completion", "APPROVE")
        self.assertEqual(result["status"], "COMPLETED")

    def test_evidence_tamper_blocks(self):
        self.prepare()
        core.dispatch(self.root, "TASK-001", "coordinator")
        (self.p["evidence"] / "test.log").write_text("PASS")
        report_file = self.root / "report.json"
        report_file.write_text(json.dumps({"task":"TASK-001", "worker":"dev", "status":"implemented", "changed_files":[], "evidence":["test.log"]}))
        core.register_report(self.root, "TASK-001", "coordinator", report_file)
        (self.p["evidence"] / "test.log").write_text("CHANGED")
        verify_file = self.root / "verify.json"
        verify_file.write_text(json.dumps({"task":"TASK-001", "verifier":"qa", "result":"PASS", "checks":[{"command":"true", "exit_code":0}]}))
        with self.assertRaises(core.WorkflowError):
            core.verify(self.root, "TASK-001", "qa", verify_file)

    def test_invalid_report_evidence_path(self):
        self.prepare()
        core.dispatch(self.root, "TASK-001", "coordinator")
        report_file = self.root / "report.json"
        report_file.write_text(json.dumps({"task":"TASK-001", "worker":"dev", "status":"implemented", "changed_files":[], "evidence":["../../../../../etc/passwd"]}))
        with self.assertRaises(core.WorkflowError):
            core.register_report(self.root, "TASK-001", "coordinator", report_file)

    def test_doctor(self):
        self.assertTrue(core.doctor(self.root)["ok"])


if __name__ == "__main__":
    unittest.main()
