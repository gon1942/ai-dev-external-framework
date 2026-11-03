"""Approval-gated, non-destructive self-improvement proposals and promotion."""
from __future__ import annotations
import hashlib
import os
import shutil
import tempfile
from pathlib import Path, PurePosixPath
from . import core


def _folder(root: Path, task: str) -> Path:
    core.task_dir(root, task)  # validates ID
    return root / "docs/agent-improvements/candidates" / task


def _target(root: Path, name: str) -> Path:
    p = PurePosixPath(name)
    if (not name or p.is_absolute() or ".." in p.parts or "\\" in name
        or not (name == "AGENTS.md" or name == "CLAUDE.md"
                or (p.parts[0] == "docs" and name.endswith(".md"))
                or (p.parts[0] == ".ai-dev" and name.endswith(".json"))
                or (p.parts[0] in (".opencode", ".claude", ".codex", ".agents")
                    and len(p.parts) > 1))):
        raise core.WorkflowError("승인된 프로젝트 정책/문서 상대 경로만 허용합니다")
    dest = root.joinpath(*p.parts)
    if not dest.resolve().is_relative_to(root.resolve()):
        raise core.WorkflowError("프로젝트 외부 대상 또는 심볼릭 링크는 허용되지 않습니다")
    return dest


def propose(root: Path, task: str, title: str, problem: str) -> dict:
    if len(problem.strip()) < 15:
        raise core.WorkflowError("개선 근거/재현 요약을 15자 이상 입력하세요")
    candidate = _folder(root, task)
    if candidate.exists():
        raise core.WorkflowError("이미 존재하는 개선 후보입니다")
    core.create_task(root, task, title, "configuration")
    candidate.mkdir(parents=True)
    (candidate / 'proposal.md').write_text(
        f'# {task}: 자가개선 후보\n\n## 발견한 문제 / 재현\n{problem}\n\n'
        '## ANALYZE 결과 / 근본 원인\n미작성\n\n'
        '## 개선 범위와 제외 범위\n미작성\n\n'
        '## PLAN / 검증 및 롤백\n미작성\n\n'
        '## 독립 VERIFY / REVIEW 근거\n미작성\n\n'
        '## 사용자 승인 및 공식 반영\n미승인 / 미반영\n', encoding='utf-8')
    core.atomic_json(candidate / 'manifest.json',
        {'schema': 1, 'task': task, 'status': 'CANDIDATE', 'changes': [], 'created_at': core.now()})
    return {'task': task, 'candidate': str(candidate.relative_to(root)), 'state': 'ANALYZE/DRAFT',
            'next': 'Spec/Plan 작성 -> plan-ready -> 사용자 계획 승인 -> 구현(격리) -> VERIFY -> REVIEW -> 사용자 최종 승인'}


def stage(root: Path, task: str, target: str, source: Path) -> dict:
    candidate = _folder(root, task)
    manifest = core.json_read(candidate / 'manifest.json')
    if manifest['status'] != 'CANDIDATE':
        raise core.WorkflowError('반영이 끝난 후보는 수정할 수 없습니다')
    s = core.json_read(core.paths(root, task)['state'])
    if s['stage'] != 'IMPLEMENT' or s['status'] != 'DISPATCHED':
        raise core.WorkflowError('승인 및 파견된 IMPLEMENT 단계에서만 스테이징할 수 있습니다')
    if not s.get('approvals', {}).get('plan'):
        raise core.WorkflowError('계획 승인 기록이 없습니다')
    dest = _target(root, target)
    plan = core.paths(root, task)['plan'].read_text(encoding='utf-8')
    import re
    listed = set(re.findall(r'^\s*[-*]\s+`?([A-Za-z0-9_./-]+)`?\s*$', plan, flags=re.MULTILINE))
    if target not in listed:
        raise core.WorkflowError('승인된 Plan에 정확한 개선 대상 경로가 목록으로 명시되어 있지 않습니다: ' + target)
    core._ensure_plan_not_changed(s, core.paths(root, task))
    if not source.is_file() or source.is_symlink():
        raise core.WorkflowError('실제 로컬 개선 파일이 필요합니다')
    if source.resolve() == dest.resolve():
        raise core.WorkflowError('정본 파일 자체를 스테이징 입력으로 사용할 수 없습니다')
    if any(x['target'] == target for x in manifest['changes']):
        raise core.WorkflowError('이미 등록된 대상입니다. 추가 변경은 새 후보로 진행하세요')
    raw = source.read_bytes()
    if len(raw) > 2_000_000:
        raise core.WorkflowError('개별 개선 파일은 2MB를 초과할 수 없습니다')
    base = core.digest(dest) if dest.exists() else None
    staged = candidate / 'staged' / f'{len(manifest["changes"]):03d}.bin'
    staged.parent.mkdir(parents=True, exist_ok=True)
    staged.write_bytes(raw)
    change = {'target': target, 'source': str(staged.relative_to(candidate)),
              'base_sha256': base, 'sha256': hashlib.sha256(raw).hexdigest()}
    manifest['changes'].append(change)
    core.atomic_json(candidate / 'manifest.json', manifest)
    return {'task': task, 'staged': change, 'active_policy_changed': False}


def inspect(root: Path, task: str) -> dict:
    candidate = _folder(root, task)
    m = core.json_read(candidate / 'manifest.json')
    s = core.json_read(core.paths(root, task)['state'])
    ready = (s.get('stage') == 'COMPLETE' and s.get('status') == 'COMPLETED'
             and 'completion' in s.get('approvals', {})
             and 'plan' in s.get('approvals', {}))
    p = core.paths(root, task)
    completed_plan = root / 'docs/exec-plans/completed' / task / 'plan.md'
    active_plan = root / 'docs/exec-plans/active' / task / 'plan.md'
    ready = bool(ready and completed_plan.is_file() and not active_plan.exists()
                 and p['report'].is_file() and p['verification'].is_file()
                 and p['review'].is_file() and m['changes'] and m['status'] == 'CANDIDATE')
    if ready:
        try:
            core._ensure_plan_not_changed(s, p)
        except core.WorkflowError:
            ready = False
    issues = []
    for c in m['changes']:
        dst = _target(root, c['target'])
        src = candidate / c['source']
        if not src.is_file() or core.digest(src) != c['sha256']:
            issues.append(f"스테이징 데이터 변조: {c['target']}")
        current = core.digest(dst) if dst.exists() else None
        if current != c['base_sha256']:
            issues.append(f"정본 변경 충돌: {c['target']}")
    return {'task': task, 'state': s['status'], 'stage': s['stage'],
            'completion_approval': s.get('approvals', {}).get('completion'),
            'candidate_status': m['status'], 'changes': m['changes'],
            'ready_to_apply': ready and not issues, 'issues': issues}


def apply(root: Path, task: str, actor: str, confirm: str, execute: bool = False) -> dict:
    with core.completion_lock(root, task):
        result = inspect(root, task)
        if not execute:
            return {'applied': False, **result}
        if confirm != 'APPLY' or not actor.strip() or actor.lower() in ('coordinator', 'implementer', 'verifier', 'reviewer', 'ai'):
            raise core.WorkflowError('사용자 확인 --actor HUMAN --confirm APPLY가 필요합니다 (CLI만으로 신원 검증 불가)')
        if not result['ready_to_apply']:
            raise core.WorkflowError('완료 승인/검증/리뷰/스테이징 무결성 확인 전 공식 반영 금지: ' + str(result['issues']))
        candidate = _folder(root, task)
        manifest = core.json_read(candidate / 'manifest.json')
        backup = candidate / 'backups'
        written = []
        try:
            for i, c in enumerate(manifest['changes']):
                dst = _target(root, c['target'])
                src = candidate / c['source']
                if dst.exists():
                    b = backup / f'{i:03d}.bin'
                    b.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(dst, b)
                dst.parent.mkdir(parents=True, exist_ok=True)
                fd, tmp = tempfile.mkstemp(prefix='.improve-', dir=dst.parent)
                try:
                    with os.fdopen(fd, 'wb') as f:
                        f.write(src.read_bytes())
                        f.flush()
                        os.fsync(f.fileno())
                    os.replace(tmp, dst)
                finally:
                    if os.path.exists(tmp):
                        os.unlink(tmp)
                written.append((i, dst))
        except Exception:
            for i, dst in reversed(written):
                b = backup / f'{i:03d}.bin'
                if b.exists():
                    shutil.copy2(b, dst)
                else:
                    dst.unlink(missing_ok=True)
            raise
        manifest['status'] = 'APPLIED'
        manifest['applied_at'] = core.now()
        manifest['applied_by_claim'] = actor
        core.atomic_json(candidate / 'manifest.json', manifest)
        return {'applied': True, 'task': task, 'targets': [c['target'] for c in manifest['changes']],
                'backups': str(backup.relative_to(root)),
                'warning': 'actor는 자기 신고이며 인증된 사용자 신원 확인이 아닙니다'}
