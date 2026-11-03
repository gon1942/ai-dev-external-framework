"""Read-only startup information and an explicit terminal launcher.

An agent instruction cannot guarantee an OpenCode/Claude/Codex native first-screen
render; launch is the reliable local CLI banner entry point.
"""
from __future__ import annotations
import json
import shutil
import subprocess
from pathlib import Path
from . import core, overview, integrations, audit, skill_events, common_skills, progress

EXTERNAL_RECOMMENDED = {
    'ANALYZE': ['brainstorming', 'systematic-debugging'],
    'PLAN': ['writing-plans'],
    'IMPLEMENT': ['test-driven-development', 'implement'],
    'VERIFY': ['verification-before-completion', 'playwright-cli (웹 작업)'],
    'REVIEW': ['requesting-code-review', 'web-design-guidelines (웹 작업)'],
}

STAGE_SKILLS = [
    ('SESSION', 'coordinator', ['worker-activity-monitor'], '작업·소유권 확인'),
    ('ANALYZE', 'coordinator', ['code-graph-analysis'], '기존 코드·영향 분석'),
    ('PLAN', 'coordinator', ['task-orchestration'], 'Spec·Plan·Task Graph·승인'),
    ('IMPLEMENT', 'implementer', ['context-handoff', 'tdd-workflow'], '유형별 TDD 강제·구현·인계'),
    ('VERIFY', 'verifier', ['evidence-driven-verification'], '원본 로그·종료코드 검증'),
    ('REVIEW', 'reviewer', ['ui-quality', 'code-graph-analysis'], '독립 리뷰·UI/구조 검토'),
    ('COMPLETE', 'coordinator', [], '최종 승인 후 archive'),
]


def snapshot(root: Path) -> dict:
    root = root.resolve()
    if not (root/'.ai-dev/policy.json').is_file():
        raise core.WorkflowError('프레임워크 미설치 프로젝트입니다. teamdev init을 먼저 실행하세요')
    tool = integrations.tool_status(root)
    data = overview.overview(root)
    phases = []
    for stage, role, skills, purpose in STAGE_SKILLS:
        phases.append({'stage': stage, 'role': role, 'purpose': purpose,
                       'external_recommended_not_verified': EXTERNAL_RECOMMENDED.get(stage, []),
                       'skills': [{'name': name, 'project_installed':
                           (root/'.agents/skills'/name/'SKILL.md').is_file()}
                          for name in skills]})
    return {'task_dashboard': overview.dashboard(root), 'progress': progress.snapshot(root), 'skill_history': skill_events.history(root),
            'framework': 'Team AI Dev Framework', 'version': __import__('teamdev').__version__, 'common_skills':common_skills.status(root) if (root/'.ai-dev/skills.lock.json').is_file() else None,
            'workflow': 'COORDINATOR → ANALYZE → PLAN → [승인] → IMPLEMENTER → VERIFIER → REVIEWER → [최종 승인] → COMPLETE',
            'phases': phases, 'active': data['active'], 'completed': data['completed'],
            'runtime_checks': {'coordinator_config': [c for c in audit.agent_checks(root) if 'coordinator' in c['id']],
                               'external_skills_loaded': 'NOT_VERIFIED',
                               'native_worker_dispatch': 'NOT_VERIFIED',
                               'skill_execution': 'NOT_VERIFIED'},
            'tools': {'rtk_installed': tool['rtk']['installed'],
                      'rtk_hook_verified': False, 'crg_installed': tool['crg']['installed'],
                      'crg_graph_present': tool['crg']['graph_directory_present'],
                      'crg_freshness_verified': False},
            'note': '선택 스킬은 필요 시에만 로드합니다. 설치 여부는 실행 증거가 아닙니다. RUNNING은 모니터 관측 필요.'}


def render(info: dict) -> str:
    lines = ['='*70, f" {info['framework']} v{info['version']} — 시작 안내", '='*70,
             ' 실행: ' + info['workflow'], '', ' 단계별 역할 / 프로젝트 번들 스킬']
    for step in info['phases']:
        names = ', '.join(x['name'] + ('' if x['project_installed'] else ' [미설치]') for x in step['skills']) or '없음(명령/승인)'
        lines.append(f"  {step['stage']:<10} {step['role']:<12} {names}")
        if step['external_recommended_not_verified']:
            lines.append('  ' + ' '*10 + '↳ 통합 선택 스킬(설치·사용 상태 아래 참조): ' + ', '.join(step['external_recommended_not_verified']))
    common=info.get('common_skills')
    if common:
        lines += ['', ' 공통 잠금 스킬: '+str(common['total'])+'종 | '+ ' / '.join(k+':'+str(v)+'/'+str(common['total']) for k,v in common['runtimes'].items()), ' 불일치: '+str(len(common['issues']))+'건 (runtime load: NOT_VERIFIED)']
    board = info.get('task_dashboard', {})
    stats = board.get('counts', {})
    lines += ['', ' 작업 현황: 해야 할 작업 {pending} / 완료 {completed} / 승인 대기 {approval} / 차단 {blocked}'.format(
        pending=stats.get('pending',len(info['active'])), completed=stats.get('completed',len(info['completed'])),
        approval=stats.get('approval_waiting',0), blocked=stats.get('blocked',0)),
        ' TASK | 단계 | 상태 | 사용자 조치 | 다음 실행 | Worker / 활동']
    for task in board.get('tasks', []):
        lines.append(' {task} | {stage} | {status} | {user_action} | {next_action} | {worker} / {activity}'.format(**task))
    lines += ['', ' 단계별 진행 현황 (검증·실행 상태는 별도 관측)']
    lines += progress.render(info['progress']).splitlines()
    h = info.get('skill_history', {})
    lines += ['', ' 단계별 스킬 사용 기록 (에이전트 제출 기록; 런타임 로드 증명 아님)']
    for stage in ('ANALYZE','PLAN','IMPLEMENT','VERIFY','REVIEW','COMPLETE'):
        group = h.get('by_stage', {}).get(stage, [])
        if group:
            for x in group[-5:]:
                lines.append('  {stage}: {skill} | {task} | {role} | {integrity} | {at}'.format(**x))
        else:
            lines.append('  ' + stage + ': 기록 없음')
    lines.append(' 전체 스킬 이벤트 {total}건 / 증거 불일치 {bad}건'.format(total=h.get('count',0), bad=h.get('integrity_errors',0)))
    lines += ['', f" 기존 상세 분류: 진행 {len(info['active'])} / 완료 {len(info['completed'])}"]
    for task in info['active']:
        if 'error' in task:
            lines.append(f"  ! {task['task']}: ERROR {task['error']}")
        else:
            lines.append(f"  - {task['task']} [{task['stage']}/{task['status']}] 다음: {task['next_action']} | worker: {task.get('worker') or '-'} | activity: {task.get('activity') or 'UNTRACKED'}")
    lines += ['', ' 도구: RTK=' + ('installed' if info['tools']['rtk_installed'] else 'missing') + ' (hook 미검증), CRG=' +
              ('installed' if info['tools']['crg_installed'] else 'missing') +
              (' (graph 존재·최신성 미검증)' if info['tools']['crg_graph_present'] else ' (graph 없음)'),
              ' 확인: 설정/파일 발견은 실제 스킬 로드·워커 파견·검증 성공의 증거가 아닙니다.',
              ' 진단: teamdev audit  |  상세: teamdev audit --json',
              ' 주의: 시작 요약은 상태 조회만 수행하며 작업을 자동 재개하지 않습니다.', '='*70]
    return '\n'.join(lines)


def launch(root: Path, runtime: str, extra_args: list[str] | None = None, runner=None) -> int:
    if runtime not in ('opencode', 'claude', 'codex'):
        raise core.WorkflowError('지원 실행기: opencode, claude, codex')
    binary = shutil.which(runtime)
    if binary is None:
        raise core.WorkflowError(f'{runtime} 실행 파일을 찾을 수 없습니다')
    print(render(snapshot(root)), flush=True)
    if runner is None:
        runner = subprocess.run
    result = runner([binary, *(extra_args or [])], cwd=root, check=False)
    return result.returncode
