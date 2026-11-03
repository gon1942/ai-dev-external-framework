"""Portable, stdlib-only workflow engine. No vendor SDK or cloud dependency."""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
import zipfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

STAGES = ("ANALYZE", "PLAN", "IMPLEMENT", "VERIFY", "REVIEW", "COMPLETE")
TEMPLATE_DIR = Path(__file__).resolve().parent / "assets"
TASK_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{2,63}$")

class WorkflowError(Exception):
    pass


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".tmp-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def json_read(path: Path) -> dict:
    if not path.is_file():
        raise WorkflowError(f"필요한 파일이 없습니다: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise WorkflowError(f"유효하지 않은 JSON: {path}: {exc}") from exc


def task_dir(root: Path, task: str) -> Path:
    if not TASK_RE.fullmatch(task):
        raise WorkflowError("작업 ID는 영숫자로 시작하는 3~64자 영숫자/하이픈/밑줄만 허용")
    return root / "docs" / "tasks" / task


@contextmanager
def completion_lock(root: Path, task: str):
    """Serialize final approval/archive for cooperating local teamdev processes."""
    try:
        import fcntl
    except ImportError as exc:
        raise WorkflowError("완료 처리 잠금은 POSIX fcntl을 필요로 합니다") from exc
    base = task_dir(root, task)
    base.mkdir(parents=True, exist_ok=True)
    with (base / ".completion.lock").open("a+b") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def plan_folder(root: Path, task: str) -> Path:
    task_dir(root, task)  # validate task ID
    active = root / "docs/exec-plans/active" / task
    completed = root / "docs/exec-plans/completed" / task
    if active.exists() and completed.exists():
        raise WorkflowError("active/completed 양쪽에 실행 계획이 존재합니다. 충돌을 확인하세요")
    return completed if completed.exists() else active


def paths(root: Path, task: str) -> dict[str, Path]:
    base = task_dir(root, task)
    plan_root = plan_folder(root, task)
    return {
        "base": base,
        "spec": root / "docs" / "product-specs" / f"{task}.md",
        "plan": plan_root / "plan.md",
        "state": base / "state.json",
        "handoff": base / "handoff.json",
        "report": base / "worker-report.json",
        "verification": base / "verification.json",
        "review": base / "review.json",
        "evidence": base / "evidence",
        "rotation_handoff": plan_root / "context-handoff.md",
        "sessions": base / "sessions",
    }


def copy_assets(root: Path, force: bool = False) -> list[str]:
    bundle = TEMPLATE_DIR / "bundle.zip"
    if not bundle.is_file():
        raise WorkflowError("설치용 템플릿 bundle.zip을 찾을 수 없습니다")
    written: list[str] = []
    with zipfile.ZipFile(bundle) as z:
        for entry in z.infolist():
            if entry.is_dir():
                continue
            rel = Path(entry.filename)
            if rel.is_absolute() or ".." in rel.parts:
                raise WorkflowError("잘못된 템플릿 파일 경로")
            dst = root / rel
            if dst.exists() and not force:
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_bytes(z.read(entry))
            written.append(str(rel))
    # Native skill discovery differs across runtimes. Keep .agents/skills as
    # the single source of truth while supplying non-destructive copies.
    for folder in sorted((root / ".agents" / "skills").glob("*")):
        if not (folder / "SKILL.md").is_file():
            continue
        for native in (".opencode/skills", ".claude/skills"):
            destination = root / native / folder.name
            if destination.exists() and not force:
                continue
            if destination.exists():
                shutil.rmtree(destination)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(folder, destination)
            written.append(str(destination.relative_to(root)))
    return written


def create_task(root: Path, task: str, title: str, task_type: str | None = None) -> dict:
    p = paths(root, task)
    if p["base"].exists() or p["spec"].exists() or p["plan"].exists():
        raise WorkflowError("해당 작업 ID가 이미 존재합니다")
    p["spec"].parent.mkdir(parents=True, exist_ok=True)
    p["plan"].parent.mkdir(parents=True, exist_ok=True)
    p["evidence"].mkdir(parents=True, exist_ok=False)
    p["spec"].write_text(
        f"# {task}: {title}\n\n## 문제 / 목표\nTODO\n\n## 범위 / 제외 범위\nTODO\n\n## 인수 조건 (AC)\n- [ ] AC-1: TODO\n\n## 위험 / 보안 영향\nTODO\n",
        encoding="utf-8",
    )
    p["plan"].write_text(
        f"# {task}: 실행 계획\n\n## 구현 단계\nTODO\n\n## Task Graph\n| ID | 선행 작업 | 담당 범위 | 검증 |\n|---|---|---|---|\n| T1 | - | TODO | TODO |\n\n## 검증 명령\nTODO\n\n## 롤백 계획\nTODO\n",
        encoding="utf-8",
    )
    state = {"schema": 1, "id": task, "title": title, "stage": "ANALYZE", "status": "DRAFT", "revision": 1, "created_at": now(), "updated_at": now(), "approvals": {}, "history": [], "rotation": {"sequence": 0, "phase": "NONE"}}
    if task_type is not None:
        from . import tdd
        state['tdd'] = tdd.classify(task_type)
    atomic_json(p["state"], state)
    return state


def _load(root: Path, task: str) -> tuple[dict, dict[str, Path]]:
    p = paths(root, task)
    return json_read(p["state"]), p


def _event(s: dict, action: str, actor: str) -> None:
    s["revision"] += 1
    s["updated_at"] = now()
    s["history"].append({"action": action, "actor": actor, "at": s["updated_at"]})


def _assert_stage(s: dict, expected: str) -> None:
    if s["stage"] != expected:
        raise WorkflowError(f"현재 단계는 {s['stage']}; 필요한 단계는 {expected}")


def _ensure_nonplaceholder(p: Path) -> None:
    txt = p.read_text(encoding="utf-8")
    if "TODO" in txt or len(txt.strip()) < 100:
        raise WorkflowError(f"문서의 TODO를 모두 해결하고 내용을 작성하세요: {p}")


def plan_ready(root: Path, task: str, actor: str) -> dict:
    s, p = _load(root, task)
    _assert_stage(s, "ANALYZE")
    for name in ("spec", "plan"):
        _ensure_nonplaceholder(p[name])
    s["stage"] = "PLAN"
    s["status"] = "AWAITING_APPROVAL"
    _event(s, "plan-ready", actor)
    atomic_json(p["state"], s)
    return s


def approve(root: Path, task: str, actor: str, scope: str, confirmation: str) -> dict:
    if not actor.strip() or not scope.strip() or confirmation != "APPROVE":
        raise WorkflowError("승인자, 승인 범위, --confirm APPROVE가 필요합니다")
    if scope == "completion":
        with completion_lock(root, task):
            return _approve_completion(root, task, actor)
    s, p = _load(root, task)
    required_stage = {"plan": "PLAN", "completion": "COMPLETE"}.get(scope)
    if not required_stage:
        raise WorkflowError("승인 범위는 plan 또는 completion")
    _assert_stage(s, required_stage)
    if scope == "plan":
        if s["status"] != "AWAITING_APPROVAL":
            raise WorkflowError("승인 대기 상태가 아닙니다")
        s["approvals"]["plan"] = {"actor": actor, "at": now(), "spec_sha256": digest(p["spec"]), "plan_sha256": digest(p["plan"])}
        if 'tdd' in s:
            s['approvals']['plan']['tdd_policy'] = dict(s['tdd'])
        s["stage"] = "IMPLEMENT"
        s["status"] = "APPROVED"
    _event(s, f"approve-{scope}", actor)
    atomic_json(p["state"], s)
    return s



def _approve_completion(root: Path, task: str, actor: str) -> dict:
    s, p = _load(root, task)
    _assert_stage(s, "COMPLETE")
    if s["status"] != "AWAITING_FINAL_APPROVAL":
        raise WorkflowError("최종 승인 대기 상태가 아닙니다")
    _ensure_plan_not_changed(s, p)
    if 'tdd' in s:
        from . import tdd
        tdd.check(root, task, report=json_read(p['report']))
    if not p["verification"].is_file() or not p["review"].is_file():
        raise WorkflowError("독립 검증 및 리뷰 증거가 없습니다")
    src = root / "docs/exec-plans/active" / task
    dst = root / "docs/exec-plans/completed" / task
    if dst.exists() or not src.is_dir() or not (src / "plan.md").is_file():
        raise WorkflowError("완료 계획 폴더가 이미 있거나 active Plan이 없습니다")
    dst.parent.mkdir(parents=True, exist_ok=True)
    # Same-filesystem rename is atomic. If state writing fails, restore active path.
    src.rename(dst)
    try:
        s["approvals"]["completion"] = {"actor": actor, "at": now()}
        s["status"] = "COMPLETED"
        s["archive"] = {"plan_dir": str(dst.relative_to(root)), "at": now()}
        _event(s, "approve-completion-and-archive", actor)
        atomic_json(p["state"], s)
    except Exception:
        dst.rename(src)
        raise
    return s


def _ensure_plan_not_changed(s: dict, p: dict[str, Path]) -> None:
    a = s.get("approvals", {}).get("plan")
    if not a:
        raise WorkflowError("계획 승인이 없습니다")
    if digest(p["spec"]) != a["spec_sha256"] or digest(p["plan"]) != a["plan_sha256"]:
        raise WorkflowError("승인 후 Spec/Plan이 변경되었습니다. 새 작업 계획 승인 필요")


def dispatch(root: Path, task: str, actor: str) -> dict:
    s, p = _load(root, task)
    _assert_stage(s, "IMPLEMENT")
    if s["status"] != "APPROVED":
        raise WorkflowError("파견 가능한 승인 상태가 아닙니다")
    _ensure_plan_not_changed(s, p)
    handoff = {"schema": 1, "task": task, "issued_at": now(), "issued_by": actor, "spec": str(p["spec"].relative_to(root)), "plan": str(p["plan"].relative_to(root)), "spec_sha256": digest(p["spec"]), "plan_sha256": digest(p["plan"]), "constraints": {"no_push": True, "no_unapproved_scope_change": True}, "worker": "implementation"}
    atomic_json(p["handoff"], handoff)
    s["status"] = "DISPATCHED"
    s["rotation"] = {"sequence": 0, "phase": "ACTIVE", "current_session": None}
    _event(s, "dispatch", actor)
    atomic_json(p["state"], s)
    return handoff


def report_template(root: Path, task: str, worker: str = "implementer", output: Path | None = None) -> dict:
    """Generate an illustrative input contract, never manufacture evidence or task success."""
    s, p = _load(root, task)
    if s['stage'] != 'IMPLEMENT':
        raise WorkflowError(f"보고서 템플릿은 IMPLEMENT 단계에서만 생성합니다 (현재 {s['stage']})")
    if not isinstance(worker, str) or not worker.strip():
        raise WorkflowError('worker는 비어 있지 않은 문자열이어야 합니다')
    sample = {'task': task, 'status': 'implemented', 'worker': worker,
              'changed_files': [], 'evidence': []}
    if output is not None:
        output = output if output.is_absolute() else root / output
        if output.exists():
            raise WorkflowError(f'기존 파일을 덮어쓸 수 없습니다: {output}')
        # The input is an unverified template, not a successful worker report.
        atomic_json(output, sample)
    return {'template': sample, 'output': str(output) if output else None,
            'note': 'changed_files와 evidence에는 실제 결과만 넣으세요. evidence는 TASK evidence/ 아래 실제 파일명(최소 1개)이며, report.md나 worker-report.json을 --file로 지정하지 마세요.'}


def _validate_report_payload(root: Path, task: str, report: object, p: dict) -> dict:
    if not isinstance(report, dict):
        raise WorkflowError('보고서는 JSON 객체여야 합니다')
    if report.get('task') != task:
        raise WorkflowError(f'report.task 오류: 예상 {task!r}, 실제 {report.get("task")!r}')
    if report.get('status') != 'implemented':
        raise WorkflowError(f'report.status 오류: 정확히 "implemented"이어야 합니다 (실제 {report.get("status")!r})')
    if not isinstance(report.get('worker'), str) or not report['worker'].strip():
        raise WorkflowError('report.worker 오류: 구현자 이름(비어 있지 않은 문자열)이 필요합니다')
    files = report.get('changed_files')
    if not isinstance(files, list) or any(not isinstance(f, str) or not f.strip() for f in files):
        raise WorkflowError('report.changed_files 오류: 파일 경로 문자열의 배열이 필요합니다')
    evidence = report.get('evidence')
    if not isinstance(evidence, list) or not evidence:
        raise WorkflowError('report.evidence 오류: TASK evidence/ 아래 존재하는 증거 파일명이 최소 1개 필요합니다')
    evidences = []
    base = p['evidence'].resolve()
    for item in evidence:
        if not isinstance(item, str) or not item.strip():
            raise WorkflowError('report.evidence 오류: 증거 파일명은 비어 있지 않은 문자열이어야 합니다')
        rel = Path(item)
        if rel.is_absolute() or '..' in rel.parts:
            raise WorkflowError(f'report.evidence 오류: 상대 경로만 허용합니다: {item}')
        candidate = (p['evidence'] / rel)
        if not candidate.is_file() or not candidate.resolve().is_relative_to(base):
            raise WorkflowError(f'report.evidence 파일이 없거나 TASK 증거 폴더 밖입니다: {item}')
        evidences.append({'file': item, 'sha256': digest(candidate)})
    if 'tdd' in _load(root, task)[0]:
        from . import tdd
        tdd.check(root, task, report=report)
    return {'evidence_checksums': evidences}


def report_check(root: Path, task: str, report_file: Path) -> dict:
    """Read-only validation: never changes state, report or evidence."""
    s, p = _load(root, task)
    _assert_stage(s, 'IMPLEMENT')
    if s['status'] != 'DISPATCHED' or s.get('rotation', {}).get('phase') != 'ACTIVE':
        raise WorkflowError('report-check는 IMPLEMENT/DISPATCHED/ACTIVE에서만 가능합니다. 이미 보고됐다면 teamdev next TASK를 확인하세요')
    _ensure_plan_not_changed(s, p)
    report_file = report_file if report_file.is_absolute() else root / report_file
    if report_file.suffix.lower() != '.json':
        raise WorkflowError('report --file에는 .json 입력 파일이 필요합니다. report.md는 사람이 읽는 Markdown입니다')
    if report_file.resolve() == p['report'].resolve():
        raise WorkflowError('worker-report.json은 CLI 출력 정본입니다. 별도 입력 파일(예: implementer-input.json)을 사용하세요')
    report = json_read(report_file)
    result = _validate_report_payload(root, task, report, p)
    return {'ok': True, 'task': task, 'input': str(report_file), 'evidence_checksums': result['evidence_checksums'],
            'state_unchanged': True}


def register_report(root: Path, task: str, actor: str, report_file: Path) -> dict:
    s, p = _load(root, task)
    _assert_stage(s, "IMPLEMENT")
    if s["status"] != "DISPATCHED" or s.get("rotation", {}).get("phase") != "ACTIVE":
        raise WorkflowError("활성 워커 세션에서만 최종 보고서를 등록할 수 있습니다")
    _ensure_plan_not_changed(s, p)
    checked = report_check(root, task, report_file)
    report_file = report_file if report_file.is_absolute() else root / report_file
    report = json_read(report_file)
    evidences = checked['evidence_checksums']
    report["evidence_checksums"] = evidences
    atomic_json(p["report"], report)
    s["rotation"]["phase"] = "FINISHED"
    s["stage"] = "VERIFY"
    s["status"] = "AWAITING_VERIFICATION"
    _event(s, "report", actor)
    atomic_json(p["state"], s)
    return s


def verify(root: Path, task: str, actor: str, verification_file: Path) -> dict:
    s, p = _load(root, task)
    _assert_stage(s, "VERIFY")
    _ensure_plan_not_changed(s, p)
    report = json_read(p["report"])
    verification = json_read(verification_file)
    if verification.get("task") != task or verification.get("result") != "PASS":
        raise WorkflowError("검증 결과가 PASS가 아닙니다")
    if verification.get("verifier") != actor or not actor.strip():
        raise WorkflowError("검증자 정보가 일치하지 않습니다")
    if actor == report.get("worker"):
        raise WorkflowError("구현자와 독립 검증자는 달라야 합니다")
    checks = verification.get("checks")
    if not isinstance(checks, list) or not checks or not all(isinstance(c, dict) and isinstance(c.get("command"), str) and c.get("exit_code") == 0 for c in checks):
        raise WorkflowError("검증 명령과 종료코드 0이 필요합니다")
    if 'tdd' in s:
        from . import tdd
        tdd.check(root, task, report=report)
    for evidence in report["evidence_checksums"]:
        candidate = p["evidence"] / evidence["file"]
        if digest(candidate) != evidence["sha256"]:
            raise WorkflowError("구현 증거 파일의 해시가 달라졌습니다")
    atomic_json(p["verification"], verification)
    s["stage"] = "REVIEW"
    s["status"] = "AWAITING_REVIEW"
    _event(s, "verified", actor)
    atomic_json(p["state"], s)
    return s


def review(root: Path, task: str, actor: str, review_file: Path) -> dict:
    s, p = _load(root, task)
    _assert_stage(s, "REVIEW")
    _ensure_plan_not_changed(s, p)
    report = json_read(p["report"])
    verification = json_read(p["verification"])
    r = json_read(review_file)
    if not actor.strip() or actor in (report.get("worker"), verification.get("verifier")):
        raise WorkflowError("리뷰어는 구현자 및 검증자와 달라야 합니다")
    if r.get("task") != task or r.get("reviewer") != actor or r.get("result") != "PASS" or r.get("blocking_findings") != 0:
        raise WorkflowError("리뷰 데이터가 유효하지 않거나 차단 이슈가 있습니다")
    atomic_json(p["review"], r)
    s["stage"] = "COMPLETE"
    s["status"] = "AWAITING_FINAL_APPROVAL"
    _event(s, "reviewed", actor)
    atomic_json(p["state"], s)
    return s


def status(root: Path, task: str) -> dict:
    return _load(root, task)[0]


def doctor(root: Path) -> dict:
    expected = ["AGENTS.md", ".ai-dev/policy.json", ".ai-dev/skills.json", ".opencode/agents/coordinator.md", ".claude/agents/coordinator.md", ".codex/agents/implementer.toml"]
    missing = [p for p in expected if not (root / p).is_file()]
    opencode_cfg = root / "opencode.json"
    opencode_default = None
    if opencode_cfg.is_file():
        try:
            opencode_default = json_read(opencode_cfg).get("default_agent")
        except WorkflowError:
            pass
    claude_cfg = root / ".claude/settings.json"
    claude_default = None
    if claude_cfg.is_file():
        try:
            claude_default = json_read(claude_cfg).get("agent")
        except WorkflowError:
            pass
    expected += ["opencode.json", ".claude/settings.json", "CLAUDE.md"]
    missing = [item for item in expected if not (root / item).is_file()]
    config_ok = opencode_default == "coordinator" and claude_default == "coordinator"
    codex_multi_agent = (root / ".codex/config.toml").is_file()
    native_cli = {name: bool(shutil.which(name)) for name in ("opencode", "claude", "codex")}
    from . import integrations
    return {"optional_tools": integrations.tool_status(root), "ok": not missing and config_ok, "missing": missing, "opencode_default": opencode_default,
            "claude_default": claude_default, "codex_policy": (root / "AGENTS.md").is_file(),
            "rtk": bool(shutil.which("rtk")), "python": os.sys.version.split()[0],
            "native_cli_found": native_cli, "codex_multi_agent_config_present": codex_multi_agent,
            "note": "설정/CLI 존재 검사만 수행합니다. 실제 Worker 호출 성공과 승인자 신원은 검증하지 않습니다."}


# Session rotation preserves the approved TASK/worktree and replaces only model conversation.
HANDOFF_FIELDS = (
    "task_id", "dispatch_sha256", "worktree", "stage", "approval_status",
    "completed", "changed_files", "verification_summary", "blockers",
    "next_action", "spec_path", "plan_path", "rotation_reason", "session_id",
)
SENSITIVE = re.compile(r"(?i)(-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|(?:api[_-]?key|password|secret|access[_-]?token|authorization)\s*[:=]\s*[^\s]{4,})")


def _parse_handoff(path: Path) -> dict:
    if not path.is_file() or path.stat().st_size > 8192:
        raise WorkflowError("인계 파일이 없거나 8KiB를 초과합니다")
    raw = path.read_text(encoding="utf-8")
    if SENSITIVE.search(raw) or "```" in raw or len(raw.splitlines()) > 65:
        raise WorkflowError("인계 파일에 민감정보/긴 로그/코드 블록이 있습니다")
    # YAML-like strict key: JSON-quoted scalar, no nested structures.
    fields = {}
    for line in raw.splitlines():
        if not line.strip() or line.startswith("# "):
            continue
        if ": " not in line:
            raise WorkflowError("인계 파일 형식이 잘못되었습니다")
        key, value = line.split(": ", 1)
        if key in fields or key not in HANDOFF_FIELDS:
            raise WorkflowError("중복되거나 알 수 없는 인계 필드")
        try:
            fields[key] = json.loads(value)
        except (ValueError, TypeError) as exc:
            raise WorkflowError("인계 값은 JSON 문자열이어야 합니다") from exc
        if not isinstance(fields[key], str):
            raise WorkflowError("인계 값은 문자열이어야 합니다")
    if set(fields) != set(HANDOFF_FIELDS) or not all(fields.values()):
        raise WorkflowError("인계 필수 필드가 누락되었습니다")
    if len(fields["next_action"]) > 400:
        raise WorkflowError("다음 행동은 한 가지, 최대 400자여야 합니다")
    return fields


def _write_handoff(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = "# Worker context handoff\n" + "\n".join(
        f"{key}: {json.dumps(data[key], ensure_ascii=False)}" for key in HANDOFF_FIELDS
    ) + "\n"
    path.write_text(raw, encoding="utf-8")


def rotation_request(root: Path, task: str, actor: str, session_id: str, worktree: Path,
                     next_action: str, reason: str, completed: str, changed_files: str = "none",
                     verification: str = "not-run", blockers: str = "none") -> dict:
    s, p = _load(root, task)
    _assert_stage(s, "IMPLEMENT")
    if s["status"] != "DISPATCHED" or s.get("rotation", {}).get("phase") != "ACTIVE":
        raise WorkflowError("활성 워커 상태에서만 회전을 요청할 수 있습니다")
    _ensure_plan_not_changed(s, p)
    if not actor.strip() or not session_id.strip() or not next_action.strip() or not reason.strip():
        raise WorkflowError("워커·세션·다음 행동·회전 사유는 필수입니다")
    worktree = worktree.resolve(strict=True)
    if not worktree.is_dir():
        raise WorkflowError("worktree 경로는 기존 디렉터리여야 합니다")
    rot = s["rotation"]
    if rot.get("worktree") and rot["worktree"] != str(worktree):
        raise WorkflowError("기존 작업 worktree와 다릅니다")
    if rot.get("current_session") and rot["current_session"] != session_id:
        raise WorkflowError("현재 활성 세션과 다릅니다")
    data = {
        "task_id": task, "dispatch_sha256": digest(p["handoff"]), "worktree": str(worktree),
        "stage": s["stage"], "approval_status": "APPROVED",
        "completed": completed or "none", "changed_files": changed_files,
        "verification_summary": verification, "blockers": blockers,
        "next_action": next_action, "spec_path": str(p["spec"].relative_to(root)),
        "plan_path": str(p["plan"].relative_to(root)), "rotation_reason": reason,
        "session_id": session_id,
    }
    if any("\n" in v or "\r" in v for v in data.values()):
        raise WorkflowError("인계 값에 여러 줄을 넣을 수 없습니다")
    _write_handoff(p["rotation_handoff"], data)
    try:
        _parse_handoff(p["rotation_handoff"])
    except Exception:
        p["rotation_handoff"].unlink(missing_ok=True)
        raise
    rot.update({"phase": "HANDOFF_REQUIRED", "pending_session": session_id,
                "worktree": str(worktree), "handoff_sha256": digest(p["rotation_handoff"])})
    _event(s, "CONTEXT_HANDOFF_REQUIRED", actor)
    atomic_json(p["state"], s)
    return {"event": "CONTEXT_HANDOFF_REQUIRED", "task": task,
            "handoff_path": str(p["rotation_handoff"]), "worker_done": False}


def rotation_resume(root: Path, task: str, actor: str, previous_session_stopped: bool,
                    new_session_id: str) -> dict:
    s, p = _load(root, task)
    _assert_stage(s, "IMPLEMENT")
    rot = s.get("rotation", {})
    if s["status"] != "DISPATCHED" or rot.get("phase") != "HANDOFF_REQUIRED":
        raise WorkflowError("인계 대기 상태가 아닙니다")
    if not previous_session_stopped:
        raise WorkflowError("이전 Worker 종료 확인이 필요합니다")
    _ensure_plan_not_changed(s, p)
    if digest(p["rotation_handoff"]) != rot["handoff_sha256"]:
        raise WorkflowError("인계 파일이 요청 후 변경되었습니다")
    handoff = _parse_handoff(p["rotation_handoff"])
    if (handoff["task_id"] != task or handoff["dispatch_sha256"] != digest(p["handoff"])
        or handoff["worktree"] != rot["worktree"]
        or handoff["session_id"] != rot["pending_session"]
        or handoff["stage"] != "IMPLEMENT" or handoff["approval_status"] != "APPROVED"
        or handoff["spec_path"] != str(p["spec"].relative_to(root))
        or handoff["plan_path"] != str(p["plan"].relative_to(root))):
        raise WorkflowError("인계의 TASK/dispatch/승인/경로 정보가 일치하지 않습니다")
    if not Path(rot["worktree"]).is_dir():
        raise WorkflowError("worktree가 없습니다")
    if not actor.strip() or not new_session_id.strip() or new_session_id == rot["pending_session"]:
        raise WorkflowError("새 Worker 세션 ID가 필요합니다")
    rot.update({"sequence": rot.get("sequence", 0) + 1, "phase": "ACTIVE",
                "current_session": new_session_id})
    rot.pop("pending_session", None)
    _event(s, "session-resumed", actor)
    atomic_json(p["state"], s)
    return {"task_id": task, "task_folder": str(p["plan"].parent),
            "context_handoff": str(p["rotation_handoff"]), "next_action": handoff["next_action"],
            "worktree": rot["worktree"], "session_id": new_session_id,
            "note": "새 세션을 실제로 시작한 것은 아닙니다. 실행기에서 새 세션 생성 및 worktree 재사용 확인이 필요합니다."}


def archive_legacy_completed(root: Path, task: str, *, apply: bool = False) -> dict:
    """Reconcile v0.5 COMPLETED state whose plan remained under active/."""
    with completion_lock(root, task):
        state, p = _load(root, task)
        if state.get('status') != 'COMPLETED' or state.get('stage') != 'COMPLETE':
            raise WorkflowError('이미 최종 승인된 COMPLETED 작업만 이전할 수 있습니다')
        if not state.get('approvals', {}).get('completion'):
            raise WorkflowError('최종 승인 이력이 없습니다')
        _ensure_plan_not_changed(state, p)
        active = root / 'docs/exec-plans/active' / task
        completed = root / 'docs/exec-plans/completed' / task
        if completed.is_dir():
            return {'task': task, 'already_archived': True, 'applied': False}
        if not active.is_dir():
            raise WorkflowError('진행 계획 폴더가 존재하지 않습니다')
        if not apply:
            return {'task': task, 'applied': False, 'from': str(active), 'to': str(completed)}
        completed.parent.mkdir(parents=True, exist_ok=True)
        active.rename(completed)
        try:
            state['archive'] = {'plan_dir': str(completed.relative_to(root)), 'at': now(), 'legacy_migration': True}
            _event(state, 'archive-legacy-completed', 'teamdev-migration')
            atomic_json(p['state'], state)
        except Exception:
            completed.rename(active)
            raise
        return {'task': task, 'applied': True, 'archive': str(completed)}
