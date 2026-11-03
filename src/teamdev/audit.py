"""Evidence-conscious audit of agent configuration, skills, tools and task lifecycle.

This is a read-only local diagnostic, not proof that an LLM loaded or used a skill.
Never access external services or claim a subagent was invoked merely from config.
"""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from . import core, integrations, monitor, overview, lifecycle

STAGES = {
    'SESSION': ('coordinator', ('worker-activity-monitor',)),
    'ANALYZE': ('coordinator', ('code-graph-analysis',)),
    'PLAN': ('coordinator', ('task-orchestration',)),
    'IMPLEMENT': ('implementer', ('context-handoff', 'tdd-workflow')),
    'VERIFY': ('verifier', ('evidence-driven-verification',)),
    'REVIEW': ('reviewer', ('ui-quality', 'code-graph-analysis')),
    'COMPLETE': ('coordinator', ()),
}

RUNTIME_SKILL_DIR = {
    'opencode': '.opencode/skills',
    'claude': '.claude/skills',
    'codex': '.agents/skills',
}
RUNTIME_AGENT_DIR = {
    'opencode': '.opencode/agents',
    'claude': '.claude/agents',
    'codex': '.codex/agents',
}


def _read_json(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        return data if isinstance(data, dict) else {}
    except (ValueError, UnicodeError, OSError):
        return {}


def _external_locations(runtime: str) -> list[Path]:
    home = Path.home()
    return {
        'opencode': [home / '.config/opencode/skills', home / '.opencode/skills'],
        'claude': [home / '.claude/skills'],
        'codex': [home / '.agents/skills', home / '.codex/skills'],
    }[runtime]


def _found_external(root: Path, name: str) -> dict:
    # Labels like "playwright-cli (웹 작업)" are recommendations, not file names.
    pure = name.split(' (', 1)[0]
    paths = {}
    for runtime, folder in RUNTIME_SKILL_DIR.items():
        candidates = [root / folder / pure / 'SKILL.md']
        candidates += [base / pure / 'SKILL.md' for base in _external_locations(runtime)]
        paths[runtime] = next((str(p) for p in candidates if p.is_file()), None)
    return paths


def skill_inventory(root: Path) -> dict:
    """Distinguish bundled, discoverable, missing and recommended-only skills."""
    registry = _read_json(root / '.ai-dev/skills.json')
    bundled = sorted(set(registry.get('bundled', [])) | {s for _, v in STAGES.values() for s in v})
    records = []
    for skill in bundled:
        paths = {runtime: (root / folder / skill / 'SKILL.md').is_file()
                 for runtime, folder in RUNTIME_SKILL_DIR.items()}
        records.append({'name': skill,
                        'source_present': (root / '.agents/skills' / skill / 'SKILL.md').is_file(),
                        'native_discovery_files': paths,
                        'loaded_in_model': 'NOT_VERIFIED',
                        'executed_in_model': 'NOT_VERIFIED'})
    external = {}
    for profile, names in registry.get('recommended_external', {}).items():
        external[profile] = [{'name': name, 'discovery_files': _found_external(root, name),
                              'loaded_in_model': 'NOT_VERIFIED', 'executed_in_model': 'NOT_VERIFIED'}
                             for name in names]
    return {'bundled': records, 'external_recommended': external,
            'note': 'SKILL.md 존재=발견 가능성. 자동 로드/실제 실행 증거가 아닙니다.'}


def agent_checks(root: Path) -> list[dict]:
    results = []
    configs = {'opencode': ('opencode.json', 'default_agent'),
               'claude': ('.claude/settings.json', 'agent')}
    for runtime, (config, key) in configs.items():
        obj = _read_json(root / config)
        agent = root / RUNTIME_AGENT_DIR[runtime] / 'coordinator.md'
        text = agent.read_text(encoding='utf-8') if agent.is_file() else ''
        primary = 'mode: primary' in text if runtime == 'opencode' else agent.is_file()
        ok = obj.get(key) == 'coordinator' and primary
        results.append({'id': runtime + '_coordinator_entry', 'status': 'PASS' if ok else 'FAIL',
                        'detail': '설정 파일과 coordinator 정의만 검사; 실제 모델 진입은 미검증',
                        'config': config, 'agent': str(agent.relative_to(root))})
    codex = (root / 'AGENTS.md').is_file() and (root / '.codex/config.toml').is_file()
    results.append({'id': 'codex_coordinator_policy', 'status': 'CONFIG_ONLY' if codex else 'FAIL',
                    'detail': 'AGENTS.md 정책 진입. 독립 기본 Coordinator / multi_agent 실제 실행은 미검증'})
    for runtime in ('opencode', 'claude', 'codex'):
        for role in ('implementer', 'verifier', 'reviewer'):
            ext = 'toml' if runtime == 'codex' else 'md'
            path = root / RUNTIME_AGENT_DIR[runtime] / f'{role}.{ext}'
            results.append({'id': f'{runtime}_{role}_definition',
                            'status': 'CONFIG_ONLY' if path.is_file() else 'FAIL',
                            'detail': '에이전트 파일 발견 여부. Worker 호출 여부는 미검증'})
    return results


def tool_checks(root: Path) -> dict:
    data = integrations.tool_status(root)
    graph = root / '.code-review-graph/graph.db'
    return {'rtk': {'cli_installed': data['rtk']['installed'],
                    'hook_status': 'NOT_VERIFIED',
                    'note': 'RTK CLI 설치는 명령 자동 인터셉트의 증거가 아님'},
            'crg': {'cli_installed': data['crg']['installed'],
                    'graph_db_present': graph.is_file(),
                    'graph_freshness': 'NOT_VERIFIED',
                    'note': 'graph.db 존재하더라도 최신성·MCP 연결은 별도 검증 필요'}}


def audit(root: Path) -> dict:
    root = root.resolve()
    if not (root / '.ai-dev/policy.json').is_file():
        raise core.WorkflowError('teamdev init 프로젝트가 아닙니다')
    from . import common_skills
    common = common_skills.status(root) if (root/'.ai-dev/skills.lock.json').is_file() else None
    skills = skill_inventory(root)
    roles = agent_checks(root)
    tools = tool_checks(root)
    tasks = overview.overview(root)
    lifecycle_report = lifecycle.check(root)
    issues = []
    for row in roles:
        if row['status'] == 'FAIL':
            issues.append({'severity': 'ERROR', 'item': row['id'], 'detail': row['detail']})
    for row in skills['bundled']:
        missing = [x for x, found in row['native_discovery_files'].items() if not found]
        if not row['source_present'] or missing:
            issues.append({'severity': 'ERROR', 'item': 'skill:' + row['name'],
                           'detail': '누락: ' + ','.join(missing + ([] if row['source_present'] else ['source']))})
    if common is None:
        issues.append({'severity':'ERROR','item':'skills_lock','detail':'공통 스킬 잠금 정책 없음'})
    else:
        for problem in common['issues']:
            issues.append({'severity':'ERROR','item':'common_skill:'+problem['skill'],'detail':problem['runtime']+' '+problem['status']})
    if not tools['crg']['graph_db_present']:
        issues.append({'severity': 'OPTIONAL', 'item': 'crg_graph',
                       'detail': '그래프 미생성. CRG CLI가 있어도 분석 준비 완료가 아님'})
    if tools['rtk']['cli_installed']:
        issues.append({'severity': 'VERIFY', 'item': 'rtk_hook',
                       'detail': 'RTK 훅 활성화 및 자동 호출 여부 실환경 검증 필요'})
    for task in tasks['active']:
        if task.get('error'):
            issues.append({'severity': 'ERROR', 'item': task['task'], 'detail': task['error']})
    return {'framework_version': '0.17.0', 'common_skills':common, 'lifecycle': lifecycle_report, 'agents': roles, 'skills': skills,
            'tools': tools, 'tasks': tasks, 'issues': issues,
            'status': 'CHECK_REQUIRED' if issues else 'CONFIG_CHECK_PASSED',
            'runtime_e2e': 'NOT_VERIFIED',
            'note': '이 결과는 로컬 파일 기반 진단입니다. 사용자 승인, 서브에이전트 실행, 스킬 로드, 훅 동작의 실증을 대체하지 않습니다.'}


def render(info: dict) -> str:
    lines = ['Team AI Dev Framework v0.17.0 — 종합 진단',
             f"판정: {info['status']}  (실제 모델 기반 E2E: {info['runtime_e2e']})", '',
             '에이전트:']
    lines += [f"  {r['status']:<12} {r['id']}" for r in info['agents']]
    lines += ['', '프로젝트 번들 스킬 (파일 발견 / 모델 로드 미검증):']
    for entry in info['skills']['bundled']:
        runtime = ' '.join(f'{k}:{"OK" if v else "MISSING"}' for k, v in entry['native_discovery_files'].items())
        lines.append(f"  {entry['name']}: {runtime}; source={entry['source_present']}")
    lines += ['', '도구: RTK CLI=' + str(info['tools']['rtk']['cli_installed']) +
              ', hook=NOT_VERIFIED; CRG CLI=' + str(info['tools']['crg']['cli_installed']) +
              ', graph.db=' + str(info['tools']['crg']['graph_db_present']) +
              ', freshness=NOT_VERIFIED',
              f"작업: 진행 {len(info['tasks']['active'])} / 완료 {len(info['tasks']['completed'])}", '', '확인/조치:']
    lines += [f"  [{r['severity']}] {r['item']}: {r['detail']}" for r in info['issues']]
    lines.append('주의: FILE FOUND != SKILL LOADED != WORKER EXECUTED != TEST PASSED')
    return '\n'.join(lines)
