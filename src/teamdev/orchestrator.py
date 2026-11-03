"""Native CLI worker driver. The CLI runner is optional; native subagents remain preferred in chat.

A worker must register evidence through teamdev. A process exit code alone is never PASS.
"""
from __future__ import annotations
import shutil
import subprocess
import uuid
import os
import threading
from contextlib import contextmanager
from pathlib import Path
from . import core, monitor, lifecycle, common_skills, coordinator_session

@contextmanager
def exclusive_task_run(root: Path, task: str):
    """Prevent two local orchestrators from using the same TASK concurrently (POSIX)."""
    try:
        import fcntl
    except ImportError as exc:
        raise core.WorkflowError('원자적인 TASK 실행 잠금은 POSIX fcntl이 필요합니다') from exc
    lock = core.task_dir(root, task) / '.drive.lock'
    lock.parent.mkdir(parents=True, exist_ok=True)
    with lock.open('a+b') as fh:
        try:
            fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise core.WorkflowError('동일 TASK의 다른 실행기가 이미 실행 중입니다') from exc
        try:
            yield
        finally:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)


ROLES = {"IMPLEMENT": "implementer", "VERIFY": "verifier", "REVIEW": "reviewer"}


def next_step(root: Path, task: str) -> dict:
    coordinator_session.require_ready(root, task)
    consistency = lifecycle.inspect(root, task)
    if not consistency['ok']:
        raise core.WorkflowError('TASK 정본/아카이브 불일치: ' + ', '.join(consistency['errors'])
                                  + ' (teamdev lifecycle-check로 확인하세요)')
    state, paths = core._load(root, task)
    stage = state["stage"]
    status = state["status"]
    if stage == "ANALYZE":
        return {"action": "ANALYZE_PLAN", "task": task, "requires_approval": True}
    if stage == "PLAN":
        return {"action": "AWAIT_PLAN_APPROVAL", "task": task, "requires_approval": True}
    if stage == "COMPLETE":
        return {"action": "COMPLETE" if status == "COMPLETED" else "AWAIT_FINAL_APPROVAL", "task": task, "requires_approval": status != "COMPLETED"}
    core._ensure_plan_not_changed(state, paths)
    # A common-team baseline must be present before dispatching any worker.
    if (root/'.ai-dev/skills.lock.json').is_file() and stage in ('IMPLEMENT','VERIFY','REVIEW'):
        integrity=common_skills.status(root)
        if not integrity['ok']:
            problems=integrity['issues'][:4]
            raise core.WorkflowError('공통 스킬 불일치로 Worker 파견 차단: '+str(problems)+' (teamdev skills-sync --apply / skills-status --strict)')
    if stage == "IMPLEMENT":
        if status == "APPROVED":
            return {"action": "DISPATCH_IMPLEMENTER", "worker": "implementer", "task": task}
        if status == "DISPATCHED":
            rotation = state.get("rotation", {})
            if rotation.get("phase") == "HANDOFF_REQUIRED":
                return {"action": "ROTATE_WORKER", "worker": "implementer", "task": task, "handoff": str(paths["rotation_handoff"])}
            return {"action": "RUN_IMPLEMENTER", "worker": "implementer", "task": task}
    if stage == "VERIFY" and status == "AWAITING_VERIFICATION":
        return {"action": "RUN_VERIFIER", "worker": "verifier", "task": task}
    if stage == "REVIEW" and status == "AWAITING_REVIEW":
        return {"action": "RUN_REVIEWER", "worker": "reviewer", "task": task}
    raise core.WorkflowError(f"자동 파견 불가: {stage}/{status}")


def prepare_worker(root: Path, task: str, role: str, actor: str = 'coordinator') -> dict:
    """Prepare ONE native agent call. No agent is launched and no heartbeat is invented.

    Implements the approved->dispatch transition exactly once, under a local
    task lock. Never auto-approves a plan or skips independent worker stages.
    """
    if role not in ROLES.values():
        raise core.WorkflowError('알 수 없는 Worker 역할: ' + role)
    root = root.resolve()
    with exclusive_task_run(root, task):
        step = next_step(root, task)
        if step['action'] == 'DISPATCH_IMPLEMENTER' and role == 'implementer':
            # No dispatch if an active worker is already registered.
            activity = monitor.one(root, task)
            if activity.get('session_id') is not None:
                raise core.WorkflowError('활성 Worker 기록이 있어 중복 파견을 차단했습니다')
            core.dispatch(root, task, actor)
            step = next_step(root, task)
        expected = {'implementer': 'RUN_IMPLEMENTER',
                    'verifier': 'RUN_VERIFIER', 'reviewer': 'RUN_REVIEWER'}[role]
        if step['action'] != expected:
            raise core.WorkflowError(f'파견 준비 불가: 요청={role}, 현재={step["action"]}; 상태를 확인하세요')
        activity = monitor.one(root, task)
        if activity.get('session_id') is not None:
            raise core.WorkflowError('활성 Worker 기록이 있습니다. 실제 종료 확인 전 중복 호출 금지')
        return {'task': task, 'role': role, 'action': expected,
                'prepared': True, 'native_invoked': False,
                'monitor_activity': activity['activity'],
                'message': ('파견 상태 준비 완료. 네이티브 Task/Agent는 아직 실행되지 않았습니다. '
                            '실제 호출 후 반환되면 worker-return을 기록하고 monitor/progress를 조회하세요.'),
                'next': ['native Task/Agent call', 'worker-return', 'monitor', 'progress']}


def worker_prompt(root: Path, task: str, role: str, resume: dict | None = None) -> str:
    p = core.paths(root, task)
    base = (f"TASK={task}; role={role}; project={root}; Spec={p['spec']}; Plan={p['plan']}; "
            f"state={p['state']}; worker contract={p['handoff']}. "
            "Read AGENTS.md and docs/WORKFLOW.md. Never bypass approval or report unexecuted verification. ")
    if resume is not None:
        return (f"Resume the SAME TASK/worktree with a FRESH conversation. TASK ID: {task}. "
                f"Task folder: {resume['task_folder']}. Handoff: {resume['context_handoff']}. "
                f"Only next action: {resume['next_action']}. "
                "Read handoff, approved Spec/Plan and current Git/worktree state before edits. "
                "Do not reuse previous conversation history. " + base)
    if role == "implementer":
        return (base + "Read TASK state.tdd and the approved task-type policy. Follow RED/GREEN/REFACTOR for required types, approved alternative verification for UI/config/refactoring, and validation for docs. Produce evidence/tdd-manifest.json with real logs and include all logs in the report. Implement only approved scope using TDD. Save raw logs to docs/tasks/" + task + "/evidence/. "
                "When complete create a JSON report with task, worker (use 'implementer'), status='implemented', "
                "changed_files and evidence and register it with `teamdev --root . report " + task + " --actor coordinator --file <report.json>`. "
                "Only call report after real implementation and logs. For context pressure call rotate-request and then STOP; "
                "do not report worker_done on handoff. Do not commit/push.")
    if role == "verifier":
        return (base + "Check teamdev tdd-check TASK and independently confirm RED failure reason, GREEN/REFACTOR executions or alternative evidence before PASS. Run independent verification. Record actual command and exit code (never invent results). "
                "If PASS create verification JSON with task, verifier='verifier', result='PASS', checks, then "
                "`teamdev --root . verify " + task + " --actor verifier --file <verification.json>`. "
                "Do not edit product source. If tests fail, report BLOCKED; do not claim PASS.")
    if role == "reviewer":
        return (base + "Independently review scope, security, regressions and AC, no edits. "
                "For PASS create review JSON with task, reviewer='reviewer', result='PASS', blocking_findings=0 and "
                "`teamdev --root . review " + task + " --actor reviewer --file <review.json>`. "
                "For findings report blockers to coordinator; never fabricate PASS.")
    raise core.WorkflowError(f"알 수 없는 역할: {role}")


def _command(runtime: str, role: str, prompt: str) -> list[str]:
    if runtime == "opencode":
        return ["opencode", "run", "--agent", role, prompt]
    if runtime == "claude":
        return ["claude", "--agent", role, "--print", prompt]
    if runtime == "codex":
        # Codex exec uses the project AGENTS.md Coordinator rules; role instructions are prompt based.
        # No claim that this is a named Codex subagent.
        return ["codex", "exec", prompt]
    raise core.WorkflowError(f"지원하지 않는 런타임: {runtime}")


def drive(root: Path, task: str, runtime: str, *, execute: bool = False,
          max_rotations: int = 5, runner=None) -> dict:
    if max_rotations < 0:
        raise core.WorkflowError('max_rotations는 0 이상이어야 합니다')
    if execute:
        coordinator_session.require_ready(root, task)
        with exclusive_task_run(root, task):
            return _drive_unlocked(root, task, runtime, execute=True,
                                   max_rotations=max_rotations, runner=runner)
    return _drive_unlocked(root, task, runtime, execute=False,
                           max_rotations=max_rotations, runner=runner)


def _drive_unlocked(root: Path, task: str, runtime: str, *, execute: bool = False,
          max_rotations: int = 5, runner=None) -> dict:
    """Run stage workers in new CLI processes, observing persistent state after each.

    `execute=False` is a no-side-effect preview. Test runners may replace subprocess.run.
    No auto-approval or manual report fabrication. Rotation checks old process exit.
    """
    root = root.resolve()
    if runner is None:
        runner = subprocess.run
    first = next_step(root, task)
    if first["action"] in ("ANALYZE_PLAN", "AWAIT_PLAN_APPROVAL", "AWAIT_FINAL_APPROVAL", "COMPLETE"):
        return {"task": task, "action": first["action"], "invocations": []}
    if not execute:
        return {"task": task, "action": first["action"], "runtime": runtime, "execute": False,
                "message": "미실행 미리보기입니다. --execute 지정 시 승인된 작업만 실제 CLI 워커를 시작합니다."}
    executable = {"opencode":"opencode", "claude":"claude", "codex":"codex"}.get(runtime)
    if not executable:
        raise core.WorkflowError("runtime은 opencode, claude, codex 중 하나여야 합니다")
    if not shutil.which(executable):
        raise core.WorkflowError(f"실행기를 찾지 못했습니다: {executable}")
    invocations = []
    rotations = 0
    while True:
        step = next_step(root, task)
        action = step["action"]
        if action in ("AWAIT_FINAL_APPROVAL", "COMPLETE"):
            return {"task": task, "action": action, "invocations": invocations}
        if action == "DISPATCH_IMPLEMENTER":
            core.dispatch(root, task, "coordinator")
            step = next_step(root, task)
            action = step["action"]
        if action == "ROTATE_WORKER":
            if rotations >= max_rotations:
                raise core.WorkflowError("세션 회전 횟수 제한을 초과했습니다. 운영자 확인 필요")
            # The previous subprocess has returned. Never trust only a worker-provided flag.
            new_session = "worker-" + uuid.uuid4().hex[:12]
            resume = core.rotation_resume(root, task, "coordinator", True, new_session)
            rotations += 1
            role = "implementer"
            prompt = worker_prompt(root, task, role, resume)
        else:
            role = step.get("worker")
            if role not in ROLES.values():
                raise core.WorkflowError(f"실행 불가 상태: {action}")
            prompt = worker_prompt(root, task, role)
        command = _command(runtime, role, prompt)
        # One process = one fresh model invocation. Record *observed* worker
        # invocation activity, independent from the workflow PASS/FAIL state.
        session_id = 'cli-' + uuid.uuid4().hex[:16]
        monitor.start(root, task, role, session_id, actor='drive', pid=os.getpid(), source='cli-driver')
        stop_signal = threading.Event()
        def pulse():
            while not stop_signal.wait(10):
                try:
                    monitor.heartbeat(root, task, session_id)
                except (core.WorkflowError, OSError):
                    break
        pulse_thread = threading.Thread(target=pulse, daemon=True)
        pulse_thread.start()
        returncode = None
        try:
            # runner is subprocess.run by default; tests can substitute it.
            result = runner(command, cwd=str(root), check=False)
            returncode = result.returncode
        finally:
            stop_signal.set()
            pulse_thread.join(timeout=1)
            monitor.stop(root, task, session_id, 'FINISHED' if returncode == 0 else 'FAILED')
        invocations.append({"role": role, "exit_code": returncode, "command": command[:3]})
        if returncode != 0:
            raise core.WorkflowError(f"{role} 실행기 종료코드 {returncode}. TASK 상태는 자동 PASS 처리하지 않았습니다")
        after = next_step(root, task)
        if after["action"] == "ROTATE_WORKER":
            continue
        expected = {"implementer": "RUN_VERIFIER", "verifier": "RUN_REVIEWER", "reviewer": "AWAIT_FINAL_APPROVAL"}[role]
        if after["action"] != expected:
            raise core.WorkflowError(
                f"{role}가 종료했지만 유효한 상태 전이가 없습니다. 기대={expected}, 실제={after['action']}. "
                "원본 증거·결과 등록을 확인하세요"
            )
