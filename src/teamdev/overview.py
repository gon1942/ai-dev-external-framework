"""Session-start task overview from authoritative task status and archive folders."""
from pathlib import Path
from . import core, monitor, orchestrator, lifecycle


def overview(root: Path) -> dict:
    tasks = []
    observed = {item['task']: item for item in monitor.all_tasks(root)}
    for check in lifecycle.check(root)['tasks']:
        if not check['ok']:
            tasks.append({'task': check['task'], 'error': ', '.join(check['errors'])})
            continue
        item = observed.get(check['task'], {'task': check['task'], 'activity': 'UNTRACKED'})
        tid = item["task"]
        if item.get("activity") == "ERROR":
            tasks.append({"task": tid, "error": item.get("reason")})
            continue
        try:
            state = core.status(root, tid)
            folder = core.plan_folder(root, tid)
            is_completed = state.get("status") == "COMPLETED"
            if (folder.parent.name == "completed") != is_completed:
                raise core.WorkflowError("문서 아카이브와 TASK 상태가 불일치합니다")
            next_action = "NONE" if is_completed else orchestrator.next_step(root, tid).get("action", "UNKNOWN")
            tasks.append({"task": tid, "title": state.get("title"), "stage": state.get("stage"),
                          "status": state.get("status"), "plan_dir": str(folder.relative_to(root)),
                          "activity": item.get("activity"), "worker": item.get("worker"),
                          "next_action": next_action, "resume_requires_ownership_check": not is_completed})
        except (core.WorkflowError, OSError, KeyError, ValueError) as exc:
            tasks.append({"task": tid, "error": str(exc)})
    return {"active": [t for t in tasks if t.get("status") != "COMPLETED"],
            "completed": [t for t in tasks if t.get("status") == "COMPLETED"],
            "note": "새 세션은 상태를 확인만 합니다. 기존 Worker 소유권·heartbeat·승인 없이 자동 재개하지 마세요."}


ACTION_DESCRIPTIONS = {
    'ANALYZE_PLAN': ('없음', '요구사항 분석 및 Spec/Plan 작성'),
    'AWAIT_PLAN_APPROVAL': ('계획 승인/수정', '사용자 계획 승인 대기'),
    'DISPATCH_IMPLEMENTER': ('없음', 'Implementer 파견'),
    'RUN_IMPLEMENTER': ('없음', '구현 진행 확인'),
    'ROTATE_WORKER': ('없음', '이전 Worker 종료 확인 후 세션 재개'),
    'RUN_VERIFIER': ('없음', '독립 검증 Worker 실행'),
    'RUN_REVIEWER': ('없음', '독립 리뷰 Worker 실행'),
    'AWAIT_FINAL_APPROVAL': ('최종 완료 승인/수정', '최종 완료 승인 대기'),
    'COMPLETE': ('없음', '완료 기록 보관'),
}


def dashboard(root: Path) -> dict:
    """Read-only dashboard; file status is not evidence of a currently running model."""
    data = overview(root)
    tasks = []
    for entry in data['active'] + data['completed']:
        action = entry.get('next_action', 'UNKNOWN')
        if 'error' in entry:
            tasks.append({'task': entry['task'], 'stage': 'UNKNOWN', 'status': 'BLOCKED',
                          'user_action': '상태/문서 불일치 확인', 'next_action': entry['error'],
                          'worker': '-', 'activity': 'UNTRACKED'})
            continue
        user_action, next_action = ACTION_DESCRIPTIONS.get(action, ('상태 점검', action))
        if entry.get('status') == 'COMPLETED':
            user_action, next_action = '없음', '완료 이력 조회'
        activity = entry.get('activity') or 'UNTRACKED'
        if activity in ('RECENT_ACTIVITY', 'RUNNING', 'STALE') and entry.get('status') != 'COMPLETED':
            user_action = 'Worker 소유권 확인' if user_action == '없음' else user_action + ' + Worker 소유권 확인'
        tasks.append({'task': entry['task'], 'title': entry.get('title'), 'stage': entry.get('stage','UNKNOWN'),
                      'status': entry.get('status','UNKNOWN'), 'user_action': user_action,
                      'next_action': next_action, 'worker': entry.get('worker') or '-', 'activity': activity})
    approval = sum('승인' in r['user_action'] for r in tasks if r['status'] != 'COMPLETED')
    blocked = sum(r['status'] == 'BLOCKED' for r in tasks)
    return {'counts': {'pending': len(data['active']), 'completed': len(data['completed']),
                       'approval_waiting': approval, 'blocked': blocked, 'total': len(tasks)},
            'tasks': tasks, 'note': '사용자 조치는 권장 다음 행동입니다. RUNNING 여부는 별도 활동 관측이 필요합니다.'}
