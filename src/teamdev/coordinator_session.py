"""Orca-friendly, runtime-agnostic coordinator handoff and explicit recovery.

No Orca UI automation is implied. A new main chat must be started by the user or
an independently verified host integration. The TASK state remains authoritative.
"""
from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path

from . import core, monitor

MAX_HANDOFF = 8192
MAX_ACTION = 400
SENSITIVE = core.SENSITIVE


@contextmanager
def _lock(root: Path, task: str):
    try:
        import fcntl
    except ImportError as exc:
        raise core.WorkflowError('Coordinator 인계는 POSIX 파일 잠금이 필요합니다') from exc
    base = core.task_dir(root, task)
    base.mkdir(parents=True, exist_ok=True)
    with (base / '.coordinator.lock').open('a+b') as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)


def _location(root: Path, task: str) -> Path:
    return core.task_dir(root, task) / 'coordinator-session.json'


def _handoff_path(root: Path, task: str) -> Path:
    return core.task_dir(root, task) / 'coordinator-handoff.md'


def status(root: Path, task: str) -> dict:
    core.status(root, task)  # check TASK exists
    path = _location(root, task)
    if not path.is_file():
        return {'task': task, 'phase': 'NONE', 'note': 'Coordinator 세션 관리 기록 없음'}
    return core.json_read(path)


def _validate(root: Path, task: str, data: dict, record: dict):
    path = _handoff_path(root, task)
    if not path.is_file() or path.stat().st_size > MAX_HANDOFF:
        raise core.WorkflowError('Coordinator 인계 파일 누락 또는 8KiB 초과')
    if core.digest(path) != record.get('handoff_sha256'):
        raise core.WorkflowError('Coordinator 인계 파일 해시가 변경되었습니다')
    content = path.read_text(encoding='utf-8')
    if SENSITIVE.search(content) or '```' in content or len(content.splitlines()) > 65:
        raise core.WorkflowError('민감정보 또는 긴 로그/코드가 포함된 인계 파일')
    try:
        supplied = json.loads(content.split('\n', 1)[1])
    except (ValueError, IndexError) as exc:
        raise core.WorkflowError('Coordinator 인계 형식 오류') from exc
    if supplied != data:
        raise core.WorkflowError('Coordinator 인계 내용 불일치')
    state, p = core._load(root, task)
    if data['task'] != task or data['stage'] != state['stage'] or data['status'] != state['status']:
        raise core.WorkflowError('인계의 TASK 단계/상태가 변경되었습니다')
    if data['state_sha256'] != core.digest(p['state']):
        raise core.WorkflowError('인계 이후 TASK 상태가 변경되었습니다. 새 인계를 생성하세요')
    if data['worktree'] != str(root.resolve()) or not Path(data['worktree']).is_dir():
        raise core.WorkflowError('인계 worktree 불일치')
    if data['spec_sha256'] != (core.digest(p['spec']) if p['spec'].is_file() else None):
        raise core.WorkflowError('Spec 문서가 인계 이후 변경되었습니다')
    if data['plan_sha256'] != (core.digest(p['plan']) if p['plan'].is_file() else None):
        raise core.WorkflowError('Plan 문서가 인계 이후 변경되었습니다')
    if not 0 < len(data['next_action']) <= MAX_ACTION:
        raise core.WorkflowError('다음 행동은 1~400자여야 합니다')


def prepare(root: Path, task: str, session_id: str, next_action: str, reason: str,
            summary: str = '참조: TASK 정본/증거', blockers: str = 'none') -> dict:
    if not all(isinstance(x, str) and x.strip() for x in (session_id, next_action, reason, summary, blockers)):
        raise core.WorkflowError('session-id, next-action, reason, summary, blockers 필요')
    if len(next_action) > MAX_ACTION or len(session_id) > 128:
        raise core.WorkflowError('인계 필드 길이 제한 초과')
    with _lock(root, task):
        record = status(root, task)
        if record['phase'] == 'PREPARED':
            raise core.WorkflowError('인계 대기 중입니다. 먼저 복구하거나 취소하세요')
        if record['phase'] == 'RESUMED' and record.get('session_id') != session_id:
            raise core.WorkflowError('현재 Coordinator 세션 ID가 다릅니다. 중복 세션 방지')
        state, p = core._load(root, task)
        activity = monitor._read(root, task).get('current')
        if activity and activity.get('status') == 'RUNNING':
            raise core.WorkflowError('RUNNING으로 기록된 Worker가 있습니다. 실제 종료·인계 후 진행하세요')
        if state.get('rotation', {}).get('phase') == 'HANDOFF_REQUIRED':
            raise core.WorkflowError('Worker 인계 처리 중입니다. 먼저 Worker 회전 완료 확인')
        data = {
            'task': task, 'worktree': str(root.resolve()), 'stage': state['stage'],
            'status': state['status'], 'state_sha256': core.digest(p['state']),
            'spec_path': str(p['spec'].relative_to(root)),
            'plan_path': str(p['plan'].relative_to(root)),
            'spec_sha256': core.digest(p['spec']) if p['spec'].is_file() else None,
            'plan_sha256': core.digest(p['plan']) if p['plan'].is_file() else None,
            'plan_approved': 'plan' in state.get('approvals', {}),
            'completion_approved': 'completion' in state.get('approvals', {}),
            'summary': summary, 'blockers': blockers, 'next_action': next_action,
            'reason': reason, 'previous_session_id': session_id,
        }
        raw = '# Coordinator handoff — JSON facts, no conversation transcript\n' + json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + '\n'
        if len(raw.encode('utf-8')) > MAX_HANDOFF or len(raw.splitlines()) > 65 or SENSITIVE.search(raw) or '```' in raw:
            raise core.WorkflowError('인계 내용이 크거나 민감한 내용을 포함합니다')
        handoff = _handoff_path(root, task)
        handoff.write_text(raw, encoding='utf-8')
        record = {'schema': 1, 'task': task, 'phase': 'PREPARED', 'session_id': session_id,
                  'handoff_sha256': core.digest(handoff), 'prepared_at': core.now(),
                  'sequence': record.get('sequence', 0) + 1}
        core.atomic_json(_location(root, task), record)
        return {'task': task, 'phase': 'PREPARED', 'handoff': str(handoff),
                'note': 'Orca에서 기존 메인 세션 작업을 멈추고 새 메인 Coordinator 세션을 시작하세요. 이 명령은 UI 세션을 생성하지 않습니다.'}


def resume(root: Path, task: str, new_session_id: str, old_session_stopped: bool) -> dict:
    if not old_session_stopped:
        raise core.WorkflowError('기존 Coordinator 세션이 더 이상 작업하지 않는지 확인해야 합니다')
    if not isinstance(new_session_id, str) or not new_session_id.strip() or len(new_session_id) > 128:
        raise core.WorkflowError('유효한 새 세션 ID 필요')
    with _lock(root, task):
        record = status(root, task)
        if record['phase'] != 'PREPARED':
            raise core.WorkflowError('Coordinator 인계 대기 상태가 아닙니다')
        if record['session_id'] == new_session_id:
            raise core.WorkflowError('이전과 동일한 세션 ID는 사용할 수 없습니다')
        raw = _handoff_path(root, task).read_text(encoding='utf-8')
        data = json.loads(raw.split('\n', 1)[1])
        _validate(root, task, data, record)
        if data['previous_session_id'] != record['session_id']:
            raise core.WorkflowError('인계 출발 세션 ID 불일치')
        activity = monitor._read(root, task).get('current')
        if activity and activity.get('status') == 'RUNNING':
            raise core.WorkflowError('Worker가 RUNNING으로 기록되어 있습니다. 소유권/종료 확인 필요')
        record.update({'phase': 'RESUMED', 'session_id': new_session_id, 'resumed_at': core.now(),
                       'previous_session_id': data['previous_session_id']})
        core.atomic_json(_location(root, task), record)
        return {'task': task, 'phase': 'RESUMED', 'session_id': new_session_id,
                'handoff': str(_handoff_path(root, task)), 'next_action': data['next_action'],
                'bootstrap': [f'TASK={task}', f'TASK_FOLDER=docs/tasks/{task}',
                              f'HANDOFF=docs/tasks/{task}/coordinator-handoff.md',
                              f'NEXT_ACTION={data["next_action"]}'],
                'note': '새 Orca 메인 Coordinator에서 teamdev startup / status / next로 정본을 다시 확인하세요. 자동 Worker 호출 아님.'}


def require_ready(root: Path, task: str) -> None:
    path = _location(root, task)
    if path.is_file() and core.json_read(path).get('phase') == 'PREPARED':
        raise core.WorkflowError('Coordinator 인계 PREPARED: 새 세션 resume 전 Worker 파견/다음 단계 진행 금지')
