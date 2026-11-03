"""Evidence-aware compact progress snapshots for coordinators and humans.

Read-only. An activity heartbeat is NOT proof a native agent is still running.
"""
from __future__ import annotations
from pathlib import Path
from . import core, overview, monitor

PHASES = ('ANALYZE','PLAN','IMPLEMENT','VERIFY','REVIEW','COMPLETE')
SHORT = {'ANALYZE':'ANALYZE','PLAN':'PLAN','IMPLEMENT':'IMPL','VERIFY':'VERIFY','REVIEW':'REVIEW','COMPLETE':'DONE'}
APPROVAL_ACTIONS = ('계획 승인/수정','최종 완료 승인/수정')


def snapshot(root: Path, task: str | None = None) -> dict:
    """Derive counts and next actions from authoritative workflow, not telemetry."""
    board = overview.dashboard(root)
    rows = [r for r in board['tasks'] if task is None or r['task'] == task]
    if task and not rows:
        raise core.WorkflowError(f'등록된 TASK가 없습니다: {task}')
    items = []
    for r in rows:
        stage = r.get('stage', 'UNKNOWN')
        status = r.get('status','UNKNOWN')
        activity = r.get('activity', 'UNTRACKED')
        worker = r.get('worker') or '-'
        action = r.get('user_action','상태 점검')
        user_required = action not in ('없음', '')
        # Reporting explicit observation, not inference from start/heartbeat alone.
        activity_note = {
            'RECENT_ACTIVITY':'heartbeat 확인, 실제 실행 지속은 미확정',
            'STALE':'heartbeat 지연, 소유권 확인 필요',
            'UNTRACKED':'Worker 실행 관측 기록 없음',
            'IDLE':'활성 Worker 없음',
            'PROCESS_EXITED':'로컬 Worker 프로세스 종료 감지',
            'ERROR':'활동 기록 확인 실패',
        }.get(activity, 'Worker 활동 로그 참조')
        items.append({
            'task':r['task'], 'title':r.get('title'), 'stage':stage,
            'status':status, 'worker':worker, 'activity':activity,
            'activity_note':activity_note, 'user_action':action,
            'user_action_required':user_required,
            'next_action':r.get('next_action','UNKNOWN'),
            'phase_index':PHASES.index(stage) if stage in PHASES else None,
        })
    counts = board['counts'] if task is None else {
        'pending':sum(r['status']!='COMPLETED' for r in items),
        'completed':sum(r['status']=='COMPLETED' for r in items),
        'approval_waiting':sum('승인' in r['user_action'] and r['status']!='COMPLETED' for r in items),
        'blocked':sum(r['status']=='BLOCKED' for r in items),
        'total':len(items),
    }
    return {'counts':counts,'tasks':items,
            'note':'읽기 전용 스냅샷. RECENT_ACTIVITY ≠ 실행 중 확정; Worker 종료 ≠ 테스트 PASS. 승인과 검증은 별도 근거 필요.'}


def render(data: dict) -> str:
    c=data['counts']
    lines=[f"작업 현황 | 해야 할 작업 {c['pending']}건 | 완료 {c['completed']}건 | 승인 대기 {c['approval_waiting']}건 | 차단 {c['blocked']}건"]
    if not data['tasks']:
        lines.append('등록된 TASK가 없습니다.')
    for x in data['tasks']:
        lines.extend(['',f"TASK: {x['task']} | {x.get('title') or '-'}",
            f"단계: {x['stage']} | 상태: {x['status']} | 담당: {x['worker']} | 활동: {x['activity']}",
            '진행: ' + ' → '.join(('['+SHORT[s]+']' if s==x['stage'] else
                   ('✓'+SHORT[s] if x['phase_index'] is not None and i<x['phase_index'] else '·'+SHORT[s]))
                  for i,s in enumerate(PHASES)),
            f"사용자 조치: {x['user_action']} | 다음 실행: {x['next_action']}",
            f"관측: {x['activity_note']}"])
    lines+=['',data['note']]
    return '\n'.join(lines)
