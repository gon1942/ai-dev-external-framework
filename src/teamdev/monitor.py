"""Opt-in, truthful local worker activity telemetry.

Workflow status and observed process/heartbeat activity are intentionally separate.
Missing telemetry is UNKNOWN, never RUNNING. Local PID checks cannot verify remote agents.
"""
from __future__ import annotations
import json
import os
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from . import core

ROLES = ('implementer', 'verifier', 'reviewer')
STATES = ('RUNNING', 'FINISHED', 'FAILED', 'STOPPED')


def _time() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def _parse_time(value: str) -> float:
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00')).timestamp()
    except (ValueError, TypeError, AttributeError):
        return 0.0


def _activity_path(root: Path, task: str) -> Path:
    return core.task_dir(root, task) / 'activity.json'


@contextmanager
def _locked(root: Path, task: str):
    try:
        import fcntl
    except ImportError as exc:
        raise core.WorkflowError('모니터 파일 잠금은 POSIX fcntl이 필요합니다') from exc
    path = core.task_dir(root, task) / '.activity.lock'
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a+b') as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _read(root: Path, task: str) -> dict:
    path = _activity_path(root, task)
    if not path.exists():
        return {'schema': 1, 'task': task, 'current': None, 'history': []}
    return core.json_read(path)


def _write(root: Path, task: str, data: dict):
    core.atomic_json(_activity_path(root, task), data)


def start(root: Path, task: str, role: str, session_id: str | None = None,
          *, actor: str = 'coordinator', pid: int | None = None, source: str = 'native') -> dict:
    if role not in ROLES or not actor.strip():
        raise core.WorkflowError('유효한 역할 및 actor가 필요합니다')
    # A task must exist, have approval, and be at the corresponding stage.
    from . import coordinator_session
    coordinator_session.require_ready(root, task)
    state, paths = core._load(root, task)
    required = {'implementer': 'IMPLEMENT', 'verifier': 'VERIFY', 'reviewer': 'REVIEW'}[role]
    if state['stage'] != required:
        raise core.WorkflowError(f'{role} 시작 불가: stage={state["stage"]}, 필요={required}')
    core._ensure_plan_not_changed(state, paths)
    if role == 'implementer' and state['status'] != 'DISPATCHED':
        raise core.WorkflowError('구현 작업이 파견되지 않았습니다')
    if role == 'verifier' and state['status'] != 'AWAITING_VERIFICATION':
        raise core.WorkflowError('검증 대기 상태가 아닙니다')
    if role == 'reviewer' and state['status'] != 'AWAITING_REVIEW':
        raise core.WorkflowError('리뷰 대기 상태가 아닙니다')
    session_id = session_id or uuid.uuid4().hex
    if len(session_id) > 128 or not session_id.strip():
        raise core.WorkflowError('session-id는 1~128자여야 합니다')
    with _locked(root, task):
        data = _read(root, task)
        current = data['current']
        if current and current['status'] == 'RUNNING':
            raise core.WorkflowError('기존 Worker가 RUNNING으로 기록되어 있습니다. 종료를 확인한 뒤 재시작하세요')
        now = _time()
        item = {'role': role, 'session_id': session_id, 'actor': actor,
                'source': source, 'pid': pid, 'host': os.uname().nodename if pid else None,
                'status': 'RUNNING', 'started_at': now, 'last_heartbeat': now, 'ended_at': None}
        data['current'] = item
        _write(root, task, data)
        return item.copy()


def heartbeat(root: Path, task: str, session_id: str) -> dict:
    with _locked(root, task):
        data = _read(root, task)
        item = data.get('current')
        if not item or item['session_id'] != session_id or item['status'] != 'RUNNING':
            raise core.WorkflowError('현재 활성 세션과 일치하지 않습니다')
        item['last_heartbeat'] = _time()
        _write(root, task, data)
        return item.copy()


def stop(root: Path, task: str, session_id: str, status: str) -> dict:
    if status not in ('FINISHED', 'FAILED', 'STOPPED'):
        raise core.WorkflowError('종료 상태는 FINISHED/FAILED/STOPPED 중 하나여야 합니다')
    with _locked(root, task):
        data = _read(root, task)
        item = data.get('current')
        if not item or item['session_id'] != session_id or item['status'] != 'RUNNING':
            raise core.WorkflowError('활성 세션과 일치하지 않거나 이미 종료했습니다')
        item['status'] = status
        item['ended_at'] = _time()
        data['history'] = (data.get('history', []) + [item.copy()])[-100:]
        data['current'] = None
        _write(root, task, data)
        return item.copy()


def observe_return(root: Path, task: str, role: str, session_id: str,
                   status: str, *, actor: str = 'coordinator') -> dict:
    """Register an observed synchronous native Task/Agent *return*.

    Does not claim a runtime hook, process liveness, or verification PASS.
    Never creates an active RUNNING entry that could imply a live native task.
    """
    if role not in ROLES or status not in ('FINISHED', 'FAILED', 'STOPPED'):
        raise core.WorkflowError('유효한 role/status가 필요합니다')
    if not session_id.strip() or len(session_id) > 128 or not actor.strip():
        raise core.WorkflowError('유효한 session-id/actor가 필요합니다')
    core._load(root, task)  # TASK exists; state may already have advanced.
    with _locked(root, task):
        data = _read(root, task)
        if data.get('current') is not None:
            raise core.WorkflowError('활성 Worker 기록이 있습니다. worker-stop으로 종료 확인 후 기록하세요')
        if any(x['session_id'] == session_id for x in data.get('history', [])):
            raise core.WorkflowError('동일 Worker 세션의 반환 기록이 이미 존재합니다')
        now = _time()
        item = {'role':role, 'session_id':session_id, 'actor':actor,
                'source':'native-return-reported', 'pid':None, 'host':None,
                'status':status, 'started_at':None, 'last_heartbeat':None,
                'ended_at':now}
        data['history'] = (data.get('history', []) + [item])[-100:]
        _write(root, task, data)
        return item.copy()


def _pid_alive(pid: int) -> bool | None:
    if not isinstance(pid, int) or pid <= 0:
        return None
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return None


def one(root: Path, task: str, *, stale_seconds: int = 120) -> dict:
    state, _ = core._load(root, task)
    with _locked(root, task):
        activity = _read(root, task)
    current = activity.get('current')
    last = activity.get('history', [])[-1] if activity.get('history') else None
    observed = 'UNTRACKED'
    last_activity = None
    age = None
    reason = '이 작업에 대해 Worker 활동 이벤트가 기록되지 않았습니다'
    if not current and last:
        observed = 'IDLE'
        reason = '현재 활성 Worker 기록이 없으며 이전 실행은 종료되었습니다'
    if current:
        last_activity = current.get('last_heartbeat')
        age = max(0, int(time.time() - _parse_time(last_activity)))
        if current['status'] != 'RUNNING':
            observed = current['status']
            reason = '기록된 종료 상태'
        elif current.get('pid') and current.get('host') == os.uname().nodename and _pid_alive(current['pid']) is False:
            observed = 'PROCESS_EXITED'
            reason = '같은 호스트의 기록된 실행 프로세스가 존재하지 않습니다'
        elif age > stale_seconds:
            observed = 'STALE'
            reason = f'최근 heartbeat가 {stale_seconds}초를 초과했습니다. 실제 작업 중일 수도 있습니다'
        else:
            observed = 'RECENT_ACTIVITY'
            reason = '최근 heartbeat 확인. 실행 중이라는 확정 증거는 아닙니다'
    launch_ready = (state.get('stage') == 'IMPLEMENT' and state.get('status') == 'DISPATCHED') or (state.get('stage') == 'VERIFY' and state.get('status') == 'AWAITING_VERIFICATION') or (state.get('stage') == 'REVIEW' and state.get('status') == 'AWAITING_REVIEW')
    if not current and not last and launch_ready:
        reason = '워크플로 파견 준비 상태입니다. 네이티브 Worker 실행은 관측되지 않았습니다'
    return {'task': task, 'title': state.get('title'), 'stage': state.get('stage'),
            'workflow_status': state.get('status'), 'launch_ready': launch_ready, 'worker': current.get('role') if current else None,
            'activity': observed, 'session_id': current.get('session_id') if current else None,
            'source': current.get('source') if current else None,
            'last_worker': last.get('role') if last else None,
            'last_outcome': last.get('status') if last else None,
            'last_ended_at': last.get('ended_at') if last else None,
            'last_heartbeat': last_activity, 'seconds_since_heartbeat': age,
            'reason': reason}


def all_tasks(root: Path, *, stale_seconds: int = 120) -> list[dict]:
    base = root / 'docs' / 'tasks'
    if not base.is_dir():
        return []
    result = []
    for folder in sorted(base.iterdir()):
        if folder.is_dir() and (folder / 'state.json').is_file():
            try:
                result.append(one(root, folder.name, stale_seconds=stale_seconds))
            except (core.WorkflowError, OSError, KeyError, ValueError) as exc:
                result.append({'task': folder.name, 'activity': 'ERROR', 'reason': str(exc)})
    return result


def render(rows: list[dict]) -> str:
    if not rows:
        return '등록된 TASK가 없습니다.'
    headers = ['TASK', 'STAGE', 'WORKER', 'ACTIVITY', 'HEARTBEAT(s)']
    values = [[str(x.get('task', '-')), str(x.get('stage', '?')),
               str(x.get('worker') or '-'), str(x.get('activity', '?')),
               str(x.get('seconds_since_heartbeat') if x.get('seconds_since_heartbeat') is not None else '-')]
              for x in rows]
    lengths = [max(len(h), *(len(v[i]) for v in values)) for i, h in enumerate(headers)]
    return '\n'.join(['  '.join(h.ljust(lengths[i]) for i, h in enumerate(headers)),
                      '  '.join('-' * n for n in lengths),
                      *['  '.join(v[i].ljust(lengths[i]) for i in range(len(headers))) for v in values]])
