"""Task-type TDD contracts. Evidence files are user/worker-supplied, not attested execution."""
from __future__ import annotations
import json
from pathlib import Path
from . import core

REQUIRED = {'feature', 'bugfix', 'behavior_change', 'api', 'business_logic'}
CONDITIONAL = {'ui_visual', 'configuration', 'refactoring'}
EXEMPT = {'documentation'}
TYPES = tuple(sorted(REQUIRED | CONDITIONAL | EXEMPT))
ALTERNATIVES = {'ui_visual': 'visual_accessibility', 'configuration': 'config_smoke', 'refactoring': 'regression'}

def classify(task_type: str, *, reason: str = '') -> dict:
    if task_type not in TYPES:
        raise core.WorkflowError(f'유효하지 않은 작업 유형: {task_type}')
    if task_type in REQUIRED:
        return {'type': task_type, 'mode': 'required', 'strategy': 'red_green_refactor'}
    if task_type in CONDITIONAL:
        return {'type': task_type, 'mode': 'alternative', 'strategy': ALTERNATIVES[task_type]}
    return {'type': task_type, 'mode': 'exempt', 'strategy': 'documentation_validation'}

def set_type(root: Path, task: str, task_type: str, actor: str) -> dict:
    state, paths = core._load(root, task)
    if state['stage'] != 'ANALYZE' or state['status'] != 'DRAFT':
        raise core.WorkflowError('작업 유형은 계획 승인 준비 전 ANALYZE/DRAFT 상태에서만 변경할 수 있습니다')
    if not actor.strip():
        raise core.WorkflowError('작업 유형 변경자 정보가 필요합니다')
    state['tdd'] = classify(task_type)
    core._event(state, f'tdd-type-{task_type}', actor)
    core.atomic_json(paths['state'], state)
    return state['tdd']

def _log(evidence: Path, entry: dict, *, expected_zero: bool | None) -> str:
    if not isinstance(entry, dict) or not isinstance(entry.get('command'), str) or not entry['command'].strip():
        raise core.WorkflowError('검증 명령이 없습니다')
    code = entry.get('exit_code')
    if type(code) is not int or (expected_zero is True and code != 0) or (expected_zero is False and code == 0):
        raise core.WorkflowError('RED는 0이 아닌 종료코드, GREEN/회귀는 종료코드 0이 필요합니다')
    name = entry.get('log')
    if not isinstance(name, str) or not name or Path(name).is_absolute() or '..' in Path(name).parts:
        raise core.WorkflowError('증거 로그 경로가 유효하지 않습니다')
    target = (evidence / name).resolve()
    if not target.is_relative_to(evidence.resolve()) or not target.is_file() or target.stat().st_size == 0:
        raise core.WorkflowError(f'원본 실행 로그를 찾을 수 없습니다: {name}')
    return name

def check(root: Path, task: str, *, report: dict | None = None) -> dict:
    s, p = core._load(root, task)
    policy = s.get('tdd')
    if policy is None:
        return {'task': task, 'status': 'LEGACY_UNCLASSIFIED', 'message': '이전 버전 작업입니다. TDD 유형이 기록되지 않아 새 게이트를 소급 적용하지 않습니다.'}
    if s.get('approvals', {}).get('plan', {}).get('tdd_policy') != policy:
        raise core.WorkflowError('승인된 TDD 정책과 현재 작업 정책이 다릅니다')
    filename = 'tdd-manifest.json'
    manifest_path = p['evidence'] / filename
    if not manifest_path.is_file():
        raise core.WorkflowError('TDD/대체 검증 기록 evidence/tdd-manifest.json이 필요합니다')
    m = core.json_read(manifest_path)
    if m.get('task') != task or m.get('type') != policy['type'] or m.get('mode') != policy['mode']:
        raise core.WorkflowError('TDD 기록의 작업·유형·모드가 승인된 정책과 다릅니다')
    logs = [filename]
    if policy['mode'] == 'required':
        cycles = m.get('cycles')
        if not isinstance(cycles, list) or not cycles:
            raise core.WorkflowError('TDD 필수 유형은 RED/GREEN/REFACTOR 사이클이 필요합니다')
        for cycle in cycles:
            if not isinstance(cycle, dict):
                raise core.WorkflowError('TDD cycle 형식이 잘못되었습니다')
            red, green, refactor = (cycle.get(key) for key in ('red','green','refactor'))
            if not isinstance(red,dict) or not isinstance(red.get('expected_failure'), str) or not red['expected_failure'].strip():
                raise core.WorkflowError('RED의 의도한 실패 원인을 기록해야 합니다')
            if not isinstance(refactor,dict) or not isinstance(refactor.get('review'), str) or not refactor['review'].strip():
                raise core.WorkflowError('REFACTOR 검토 결과가 필요합니다 (코드 변경이 없어도 검토 기록)')
            logs.extend([_log(p['evidence'],red,expected_zero=False), _log(p['evidence'],green,expected_zero=True), _log(p['evidence'],refactor,expected_zero=True)])
    else:
        checks=m.get('checks')
        if not isinstance(checks,list) or not checks or not isinstance(m.get('rationale'),str) or not m['rationale'].strip():
            raise core.WorkflowError('대체/제외 유형은 근거와 실제 검증 기록이 필요합니다')
        for item in checks:
            logs.append(_log(p['evidence'],item,expected_zero=True))
        if policy['mode'] == 'alternative' and m.get('strategy') != policy['strategy']:
            raise core.WorkflowError('승인된 대체 검증 전략이 아닙니다')
    if report is not None:
        reported = report.get('evidence', [])
        if not all(x in reported for x in logs):
            raise core.WorkflowError('TDD 증거/원본 로그가 Worker 보고서 evidence 목록에서 누락되었습니다')
    return {'task': task, 'status': 'EVIDENCE_VALIDATED', 'type': policy['type'], 'mode': policy['mode'], 'logs': logs,
            'note': '명령/로그/종료코드와 파일 무결성의 형식을 확인한 것입니다. 실행 진위는 독립 Verifier/CI가 확인해야 합니다.'}
