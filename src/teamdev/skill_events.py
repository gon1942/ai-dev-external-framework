"""Optional audit trail of declared skill usage (not independent execution proof)."""
from __future__ import annotations
import json
import re
from pathlib import Path
from . import core, monitor

NAME = re.compile(r'^[a-zA-Z0-9][a-zA-Z0-9._-]{0,127}$')


def record(root: Path, task: str, skill: str, role: str, session: str, evidence: str) -> dict:
    if not NAME.fullmatch(skill) or role not in ('coordinator',) + monitor.ROLES:
        raise core.WorkflowError('잘못된 스킬 이름 또는 역할')
    if not session.strip() or len(session) > 128:
        raise core.WorkflowError('유효한 session-id가 필요합니다')
    state, paths = core._load(root, task)
    allowed_stages = {'coordinator': ('ANALYZE', 'PLAN', 'IMPLEMENT', 'VERIFY', 'REVIEW', 'COMPLETE'),
                      'implementer': ('IMPLEMENT',), 'verifier': ('VERIFY',), 'reviewer': ('REVIEW',)}
    if state['stage'] not in allowed_stages[role]:
        raise core.WorkflowError('현재 TASK 단계와 스킬 사용 역할이 일치하지 않습니다')
    base = paths['evidence'].resolve()
    target = (base / evidence).resolve()
    if not target.is_relative_to(base) or not target.is_file() or target.is_symlink():
        raise core.WorkflowError('증거 파일은 TASK evidence/ 내부에 있어야 합니다')
    with monitor._locked(root, task):
        path = paths['base'] / 'skill-events.json'
        old = core.json_read(path) if path.is_file() else {'schema': 1, 'task': task, 'events': []}
        ev = {'at': core.now(), 'skill': skill, 'role': role, 'session_id': session,
              'stage': state['stage'], 'evidence': str(target.relative_to(root.resolve())),
              'evidence_sha256': core.digest(target),
              'confidence': 'AGENT_REPORTED_WITH_FILE',
              'verified_loaded_by_runtime': False}
        old['events'].append(ev)
        core.atomic_json(path, old)
    return ev


def list_events(root: Path, task: str) -> dict:
    core._load(root, task)
    path = core.task_dir(root, task) / 'skill-events.json'
    if not path.is_file():
        return {'task': task, 'events': [], 'note': '기록 없음. 사용하지 않았다는 증거는 아닙니다.'}
    data = core.json_read(path)
    for item in data.get('events', []):
        target = root / item.get('evidence', '')
        item['evidence_integrity'] = 'MATCH' if target.is_file() and core.digest(target) == item.get('evidence_sha256') else 'MISSING_OR_CHANGED'
    data['note'] = '호출 선언+증거 해시 기록. 런타임 자체가 스킬 로드를 증명한 것은 아닙니다.'
    return data



def history(root: Path, task: str | None = None) -> dict:
    """Project-wide, stage-classified skill declarations with evidence integrity checks."""
    from . import lifecycle
    known = [x['task'] for x in lifecycle.check(root)['tasks']]
    if task is not None and task not in known:
        raise core.WorkflowError('작업을 찾을 수 없습니다: ' + task)
    results = []
    for tid in sorted(known):
        if task is not None and tid != task:
            continue
        path = core.task_dir(root, tid) / 'skill-events.json'
        if not path.is_file():
            continue
        try:
            data = core.json_read(path)
            for ev in data.get('events', []):
                relative = ev.get('evidence', '')
                base = (core.task_dir(root, tid) / 'evidence').resolve()
                dest = (root.resolve() / relative).resolve()
                valid = dest.is_relative_to(base) and dest.is_file() and not dest.is_symlink() and core.digest(dest) == ev.get('evidence_sha256')
                results.append({'task': tid, 'stage': ev.get('stage','UNKNOWN'), 'skill': ev.get('skill','UNKNOWN'),
                                'role': ev.get('role','UNKNOWN'), 'session_id': ev.get('session_id',''),
                                'at': ev.get('at',''), 'evidence': relative,
                                'integrity': 'MATCH' if valid else 'MISSING_OR_CHANGED',
                                'verified_loaded_by_runtime': False})
        except (ValueError, KeyError, OSError, json.JSONDecodeError):
            results.append({'task': tid, 'stage': 'UNKNOWN', 'skill': 'INVALID_LOG', 'role':'-', 'session_id':'',
                            'at':'', 'evidence':str(path.relative_to(root)), 'integrity':'MISSING_OR_CHANGED',
                            'verified_loaded_by_runtime':False})
    results.sort(key=lambda x: (x['at'], x['task'], x['skill']))
    by_stage = {stage: [e for e in results if e['stage']==stage]
                for stage in ('SESSION','ANALYZE','PLAN','IMPLEMENT','VERIFY','REVIEW','COMPLETE','UNKNOWN')}
    return {'count':len(results),'integrity_errors':sum(e['integrity']!='MATCH' for e in results),
            'by_stage':by_stage,'events':results,
            'note':'에이전트가 제출한 사용 선언과 증거 무결성만 확인. 실제 skill 도구 로드가 검증되었다고 주장하지 않습니다.'}
