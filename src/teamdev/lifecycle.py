"""Read-only reconciliation of stable Spec/Task evidence paths and movable Plan folders.

Never infer completion from a directory alone. State and explicit approvals govern.
"""
from __future__ import annotations
from pathlib import Path
from . import core


def _task_ids(root: Path) -> list[str]:
    bases = (root / 'docs/tasks', root / 'docs/product-specs',
             root / 'docs/exec-plans/active', root / 'docs/exec-plans/completed')
    found: set[str] = set()
    for n, base in enumerate(bases):
        if not base.is_dir():
            continue
        for entry in base.iterdir():
            if n == 1 and entry.is_file() and entry.suffix == '.md' and entry.name != 'README.md':
                name = entry.stem
            elif n != 1 and entry.is_dir():
                name = entry.name
            else:
                continue
            if core.TASK_RE.fullmatch(name):
                found.add(name)
    return sorted(found)


def inspect(root: Path, task: str) -> dict:
    core.task_dir(root, task)  # validate
    spec = root / 'docs/product-specs' / f'{task}.md'
    base = root / 'docs/tasks' / task
    state_file = base / 'state.json'
    active = root / 'docs/exec-plans/active' / task
    completed = root / 'docs/exec-plans/completed' / task
    errors: list[str] = []
    if not spec.is_file():
        errors.append('SPEC_MISSING')
    if not state_file.is_file():
        errors.append('STATE_MISSING')
    if active.exists() and completed.exists():
        errors.append('DUPLICATE_PLAN')
    if not active.is_dir() and not completed.is_dir():
        errors.append('PLAN_FOLDER_MISSING')
    location = 'completed' if completed.is_dir() else 'active' if active.is_dir() else 'missing'
    plan = (completed if location == 'completed' else active) / 'plan.md'
    if location != 'missing' and not plan.is_file():
        errors.append('PLAN_FILE_MISSING')
    stage = status = None
    if state_file.is_file():
        try:
            state = core.json_read(state_file)
            stage, status = state.get('stage'), state.get('status')
            if state.get('id') != task:
                errors.append('TASK_ID_MISMATCH')
            done = status == 'COMPLETED'
            if done and stage != 'COMPLETE':
                errors.append('COMPLETED_STAGE_MISMATCH')
            if done and not state.get('approvals', {}).get('completion', {}).get('actor'):
                errors.append('FINAL_APPROVAL_MISSING')
            if done and location != 'completed':
                errors.append('COMPLETED_NOT_ARCHIVED')
            if not done and location == 'completed':
                errors.append('UNFINISHED_ARCHIVED')
            if done and state.get('archive', {}).get('plan_dir') not in (None, f'docs/exec-plans/completed/{task}'):
                errors.append('ARCHIVE_METADATA_MISMATCH')
            approved = state.get('approvals', {}).get('plan', {})
            if approved and spec.is_file() and plan.is_file():
                if (approved.get('spec_sha256') != core.digest(spec)
                        or approved.get('plan_sha256') != core.digest(plan)):
                    errors.append('APPROVED_DOC_CHANGED')
        except (core.WorkflowError, ValueError, KeyError, TypeError, OSError):
            errors.append('STATE_INVALID')
    return {'task': task, 'stage': stage, 'status': status, 'plan_location': location,
            'spec': str(spec.relative_to(root)), 'task_dir': str(base.relative_to(root)),
            'plan': str(plan.relative_to(root)) if location != 'missing' else None,
            'errors': errors, 'ok': not errors}


def check(root: Path) -> dict:
    rows = [inspect(root, task) for task in _task_ids(root)]
    return {'ok': all(row['ok'] for row in rows), 'tasks': rows,
            'active': sum(row['status'] != 'COMPLETED' for row in rows),
            'completed': sum(row['status'] == 'COMPLETED' for row in rows),
            'errors': sum(len(row['errors']) for row in rows),
            'policy': 'Spec/Task/evidence paths are fixed; only Plan folder is archived after final approval',
            'note': '읽기 전용 검사입니다. 파일 이동과 자동 복구는 수행하지 않습니다.'}


def render(result: dict) -> str:
    lines = [f"Lifecycle {'PASS' if result['ok'] else 'FAIL'}: active={result['active']} completed={result['completed']} errors={result['errors']}"]
    for row in result['tasks']:
        lines.append(f"  {row['task']} [{row['status'] or '?'}] plan={row['plan_location']} "
                     + ('OK' if row['ok'] else 'ERROR: ' + ', '.join(row['errors'])))
    return '\n'.join(lines)
