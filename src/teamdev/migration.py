"""Opt-in routing migration with backups; never silently overwrite user project files."""
from __future__ import annotations
import json
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from . import core

ROLE_FILES = [
    '.opencode/agents/coordinator.md', '.opencode/agents/implementer.md',
    '.opencode/agents/verifier.md', '.opencode/agents/reviewer.md',
    '.claude/agents/coordinator.md', '.claude/agents/implementer.md',
    '.claude/agents/verifier.md', '.claude/agents/reviewer.md',
    '.codex/config.toml', '.codex/agents/implementer.toml',
    '.codex/agents/verifier.toml', '.codex/agents/reviewer.toml',
]


def upgrade_routing(root: Path, apply: bool = False) -> dict:
    root = root.resolve()
    if not (root / 'AGENTS.md').is_file() or not (root / '.ai-dev/policy.json').is_file():
        raise core.WorkflowError('먼저 기존 프레임워크 프로젝트에서 실행하세요 (AGENTS.md와 .ai-dev/policy.json 필요)')
    # We cannot guess the right merge for project-specific agent prompts. Explicit --apply
    # backs up every affected file, replacing ONLY designated framework agent files.
    backup_dir = root / '.ai-dev/backups' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    with zipfile.ZipFile(core.TEMPLATE_DIR / 'bundle.zip') as z:
        actions = []
        for rel in ROLE_FILES:
            dst = root / rel
            if rel not in z.namelist():
                continue
            content = z.read(rel)
            if dst.is_file() and dst.read_bytes() == content:
                continue
            actions.append({'path': rel, 'action': 'backup-and-replace' if dst.exists() else 'create'})
        for rel, field, value in [('opencode.json','default_agent','coordinator'),
                                  ('.claude/settings.json','agent','coordinator')]:
            dst = root / rel
            data = core.json_read(dst) if dst.is_file() else {}
            if data.get(field) != value:
                actions.append({'path':rel, 'action':'merge-setting', 'field':field, 'old_value':data.get(field)})
        # Existing general policies are not replaced (project-customized AGENTS.md).
        if not apply:
            return {'applied': False, 'changes': actions, 'message':'변경 없음. 검토 후 --apply 지정'}
        for item in actions:
            rel = item['path']
            dst = root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            if dst.exists():
                old = backup_dir / rel
                old.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(dst, old)
            if item['action'] == 'merge-setting':
                data = core.json_read(dst) if dst.is_file() else {}
                data[item['field']] = 'coordinator'
                core.atomic_json(dst, data)
            else:
                dst.write_bytes(z.read(rel))
        return {'applied': True, 'changes': actions, 'backup': str(backup_dir) if backup_dir.exists() else None,
                'warning':'기존 AGENTS.md/CLAUDE.md는 보존했습니다. 변경된 Coordinator 실행 규칙은 문서에 직접 병합하세요.'}

TOOL_FILES = [
    '.ai-dev/tools.json', 'docs/TOOLS.md',
    '.agents/skills/code-graph-analysis/SKILL.md',
    '.opencode/skills/code-graph-analysis/SKILL.md',
    '.claude/skills/code-graph-analysis/SKILL.md',
]
TOOLS_MARKER = '## Optional CLI/code-graph tools (v0.4)'


def upgrade_tools(root: Path, apply: bool = False) -> dict:
    """Conservative opt-in project template upgrade. Never silently replace custom files.

    Adds missing tool files and a clearly delimited AGENTS.md section; existing
    nonmatching files require manual merge instead of an overwrite.
    """
    root = root.resolve()
    if not (root / 'AGENTS.md').is_file() or not (root / '.ai-dev/policy.json').is_file():
        raise core.WorkflowError('먼저 teamdev init한 프로젝트에서 실행하세요')
    with zipfile.ZipFile(core.TEMPLATE_DIR / 'bundle.zip') as z:
        def template_bytes(rel):
            source = rel
            if rel.startswith(('.opencode/skills/', '.claude/skills/')):
                source = '.agents/skills/' + rel.split('/skills/', 1)[1]
            if source not in z.namelist():
                raise core.WorkflowError(f'도구 템플릿 누락: {source}')
            return z.read(source)
        additions, conflicts = [], []
        for rel in TOOL_FILES:
            p = root / rel
            if not p.exists():
                additions.append(rel)
            elif p.read_bytes() != template_bytes(rel):
                conflicts.append(rel)
        ag = root / 'AGENTS.md'
        text = ag.read_text(encoding='utf-8')
        guidance = z.read('AGENTS.md').decode('utf-8')
        appendix = guidance[guidance.index(TOOLS_MARKER):]
        need_append = TOOLS_MARKER not in text
        if not apply:
            return {'applied': False, 'create': additions, 'conflicts_preserved': conflicts,
                    'append_to_agents': need_append}
        for rel in additions:
            out = root / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(template_bytes(rel))
        backup = None
        if need_append:
            backup = root / '.ai-dev/backups' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') / 'AGENTS.md'
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ag, backup)
            ag.write_text(text.rstrip() + '\n\n' + appendix, encoding='utf-8')
        return {'applied': True, 'created': additions, 'conflicts_preserved': conflicts,
                'agents_appended': need_append, 'agents_backup': str(backup) if backup else None,
                'note': '기존 AGENTS 정책 및 사용자 파일은 유지. 충돌 파일은 직접 검토하고 병합해야 합니다.'}

MONITOR_MARKER = '## Worker Activity Monitoring (v0.5)'

def upgrade_monitor(root: Path, apply: bool = False) -> dict:
    """Append-only monitor guidance and install missing skill/docs; backup changed files."""
    root = root.resolve()
    if not (root / 'AGENTS.md').is_file() or not (root / '.ai-dev/policy.json').is_file():
        raise core.WorkflowError('먼저 teamdev init한 프로젝트에서 실행하세요')
    append_files = ['AGENTS.md', '.opencode/agents/coordinator.md', '.claude/agents/coordinator.md']
    new_files = ['docs/MONITOR.md', '.agents/skills/worker-activity-monitor/SKILL.md']
    with zipfile.ZipFile(core.TEMPLATE_DIR / 'bundle.zip') as z:
        changes = []
        for rel in append_files:
            dest = root / rel
            if not dest.is_file():
                changes.append({'path': rel, 'action': 'create'})
            else:
                old = dest.read_text(encoding='utf-8')
                marker = MONITOR_MARKER if rel == 'AGENTS.md' else '### Observability'
                if marker not in old:
                    changes.append({'path': rel, 'action': 'append'})
        for rel in new_files:
            if not (root / rel).exists():
                changes.append({'path': rel, 'action': 'create'})
        for rel in ('.opencode/skills/worker-activity-monitor/SKILL.md', '.claude/skills/worker-activity-monitor/SKILL.md'):
            if not (root / rel).exists():
                changes.append({'path': rel, 'action': 'create'})
        if not apply:
            return {'applied': False, 'changes': changes}
        backup = root / '.ai-dev/backups' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ-monitor')
        for item in changes:
            rel, action = item['path'], item['action']
            src = rel
            if '/skills/worker-activity-monitor/' in src and not src.startswith('.agents/'):
                src = '.agents/skills/worker-activity-monitor/SKILL.md'
            content = z.read(src)
            dest = root / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            if action == 'append':
                old = dest.read_bytes()
                target = backup / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(old)
                template = content.decode('utf-8')
                marker = MONITOR_MARKER if rel == 'AGENTS.md' else '### Observability'
                dest.write_text(old.decode('utf-8').rstrip() + '\n\n' + template[template.rfind(marker):], encoding='utf-8')
            else:
                dest.write_bytes(content)
        return {'applied': True, 'changes': changes, 'backup': str(backup) if backup.exists() else None}

# v0.6 policies are append-only on existing team-managed projects.
LIFECYCLE_MARKER = '## Session Start and Plan Archive (v0.6)'


def upgrade_lifecycle(root: Path, apply: bool = False) -> dict:
    root = root.resolve()
    if not (root / 'AGENTS.md').is_file() or not (root / '.ai-dev/policy.json').is_file():
        raise core.WorkflowError('teamdev init한 프로젝트에서 실행하세요')
    targets = ['AGENTS.md', '.opencode/agents/coordinator.md', '.claude/agents/coordinator.md',
               'docs/WORKFLOW.md', 'docs/SESSION-START.md']
    additions = []
    with zipfile.ZipFile(core.TEMPLATE_DIR / 'bundle.zip') as z:
        for rel in targets:
            dst = root / rel
            if not dst.exists():
                additions.append((rel, 'create'))
            elif rel != 'docs/SESSION-START.md' and LIFECYCLE_MARKER not in dst.read_text(encoding='utf-8'):
                additions.append((rel, 'append'))
        if not apply:
            return {'applied': False, 'changes': additions}
        backup = root / '.ai-dev/backups' / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '-lifecycle')
        for rel, action in additions:
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            content = z.read(rel).decode('utf-8')
            if action == 'create':
                target.write_text(content, encoding='utf-8')
            else:
                old = target.read_text(encoding='utf-8')
                old_copy = backup / rel
                old_copy.parent.mkdir(parents=True, exist_ok=True)
                old_copy.write_text(old, encoding='utf-8')
                target.write_text(old.rstrip() + '\n\n' + content[content.rfind(LIFECYCLE_MARKER):], encoding='utf-8')
        return {'applied': True, 'changes': additions,
                'backup': str(backup) if backup.exists() else None}


def upgrade_permissions(root: Path, apply: bool = False) -> dict:
    """Add OpenCode V1 bash rules without replacing unrelated user settings."""
    root = root.resolve()
    if not (root / '.ai-dev/policy.json').exists():
        raise core.WorkflowError('teamdev init한 프로젝트에서 실행하세요')
    cfg = root / 'opencode.json'
    old = core.json_read(cfg) if cfg.exists() else {}
    if 'permissions' in old or 'policies' in old:
        raise core.WorkflowError('OpenCode V2 permission 규칙은 별도의 설정이 필요합니다')
    current = old.get('permission')
    if current is not None and (not isinstance(current, dict) or 'bash' in current):
        raise core.WorkflowError('기존 bash 권한 설정은 안전하게 자동 병합할 수 없습니다. 수동 검토하세요')
    bash = {'*': 'allow', 'git commit *': 'ask', 'git push *': 'ask',
            'git reset --hard *': 'deny', 'rm -rf *': 'ask'}
    rules = dict(current or {})
    rules['bash'] = bash
    rules.setdefault('external_directory', 'ask')
    rules.setdefault('doom_loop', 'ask')
    updated = dict(old)
    updated.setdefault('$schema', 'https://opencode.ai/config.json')
    updated['permission'] = rules
    # Agent permissions override global rules: update the known framework coordinator only.
    agent = root / '.opencode/agents/coordinator.md'
    agent_old = agent.read_text(encoding='utf-8') if agent.is_file() else None
    marker = '  bash: ask\n'
    agent_needs = agent_old is not None and marker in agent_old
    agent_rules = ('  bash:\n    "*": allow\n    "git commit *": ask\n'
                   '    "git push *": ask\n    "git reset --hard *": deny\n    "rm -rf *": ask\n')
    if agent_old and '  bash:' in agent_old and not agent_needs:
        raise core.WorkflowError('Coordinator에 사용자 지정 bash 권한이 존재합니다. 수동 검토하세요')
    if not apply:
        return {'applied': False, 'path': str(cfg), 'permission': rules,
                'agent_patch': agent_needs, 'warning': '일반 shell 명령이 자동 허용됩니다. 임의 명령 실행 권한의 위험을 검토하세요.'}
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '-permissions'
    backup = root / '.ai-dev/backups' / stamp
    for dst in [cfg, agent if agent_needs else None]:
        if dst is not None and dst.exists():
            path = backup / dst.relative_to(root)
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(dst, path)
    core.atomic_json(cfg, updated)
    if agent_needs:
        agent.write_text(agent_old.replace(marker, agent_rules, 1), encoding='utf-8')
    return {'applied': True, 'path': str(cfg), 'agent_patch': agent_needs,
            'backup': str(backup) if backup.exists() else None,
            'warning': 'OpenCode V1 설정입니다. 사람 승인 정책은 shell 도구 권한과 별개로 계속 적용합니다.'}

# v0.7 additive session banner + coordinator spec/plan edit permission.
STARTUP_MARKER = '## Startup Dashboard (v0.7)'
STARTUP_AGENT_MARKER = '## Startup Dashboard (v0.7)'
COORDINATOR_EDIT_RULES = '''  edit:
    "*": deny
    "docs/product-specs/**": allow
    "**/docs/product-specs/**": allow
    "docs/exec-plans/active/**": allow
    "**/docs/exec-plans/active/**": allow
    "docs/tasks/**": allow
    "**/docs/tasks/**": allow
'''


def upgrade_startup(root: Path, apply: bool = False) -> dict:
    """Conservative merge: preserve user prompts/config; refuse unknown edit policies."""
    root = root.resolve()
    if not (root / '.ai-dev/policy.json').is_file() or not (root/'AGENTS.md').is_file():
        raise core.WorkflowError('먼저 teamdev init한 프로젝트에서 실행하세요')
    targets = ['AGENTS.md', '.opencode/agents/coordinator.md', '.claude/agents/coordinator.md']
    doc = 'docs/STARTUP-DASHBOARD.md'
    changes, conflicts = [], []
    with zipfile.ZipFile(core.TEMPLATE_DIR/'bundle.zip') as z:
        for rel in targets:
            dst = root/rel
            if not dst.is_file():
                conflicts.append(f'{rel}: 파일 없음, 자동 생성하지 않음')
                continue
            old = dst.read_text(encoding='utf-8')
            if STARTUP_MARKER not in old:
                changes.append({'path': rel, 'action': 'append-startup'})
            if rel == '.opencode/agents/coordinator.md':
                if '  edit: ask\n' in old:
                    changes.append({'path': rel, 'action': 'scope-edit'})
                elif COORDINATOR_EDIT_RULES not in old:
                    conflicts.append(f'{rel}: 사용자 정의 edit 규칙 수동 검토 필요')
        if not (root/doc).exists():
            changes.append({'path': doc, 'action': 'create'})
        if not apply:
            return {'applied': False, 'changes': changes, 'conflicts': conflicts}
        if conflicts:
            raise core.WorkflowError('자동 병합 중단: ' + '; '.join(conflicts))
        backup = root / '.ai-dev/backups' / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '-startup')
        for rel in targets:
            acts = [x['action'] for x in changes if x['path'] == rel]
            if not acts:
                continue
            dst = root/rel
            existing = dst.read_text(encoding='utf-8')
            if 'scope-edit' in acts:
                existing = existing.replace('  edit: ask\n', COORDINATOR_EDIT_RULES, 1)
            if 'append-startup' in acts:
                template = z.read(rel).decode('utf-8')
                existing = existing.rstrip() + '\n\n' + template[template.rfind(STARTUP_MARKER):].strip() + '\n'
            old_copy = backup/rel
            old_copy.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(dst, old_copy)
            dst.write_text(existing, encoding='utf-8')
        if any(x['path'] == doc for x in changes):
            (root/doc).parent.mkdir(parents=True, exist_ok=True)
            (root/doc).write_bytes(z.read(doc))
        return {'applied': True, 'changes': changes, 'conflicts': [],
                'backup': str(backup) if backup.exists() else None,
                'warning': 'Scoped edit is not a sandbox: allowed shell can still write files. Framework approval policy must be enforced separately.'}


AUDIT_MARKER = '## Runtime Audit and Skill Evidence (v0.8)'


def upgrade_audit(root: Path, apply: bool = False) -> dict:
    """Append-only upgrade of agent guidelines and runtime audit documentation."""
    root = root.resolve()
    if not (root / '.ai-dev/policy.json').is_file() or not (root / 'AGENTS.md').is_file():
        raise core.WorkflowError('먼저 teamdev init한 프로젝트에서 실행하세요')
    append_files = ('AGENTS.md', '.opencode/agents/coordinator.md', '.claude/agents/coordinator.md')
    new_doc = 'docs/RUNTIME-AUDIT.md'
    changes, conflicts = [], []
    with zipfile.ZipFile(core.TEMPLATE_DIR / 'bundle.zip') as z:
        for rel in append_files:
            dst = root / rel
            if not dst.is_file():
                conflicts.append(rel + ': 기존 파일 없음, 수동 복구 필요')
            elif AUDIT_MARKER not in dst.read_text(encoding='utf-8'):
                changes.append({'path': rel, 'action': 'append'})
        if not (root / new_doc).is_file():
            changes.append({'path': new_doc, 'action': 'create'})
        if not apply:
            return {'applied': False, 'changes': changes, 'conflicts': conflicts}
        if conflicts:
            raise core.WorkflowError('수동 검토: ' + ', '.join(conflicts))
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '-audit'
        backup = root / '.ai-dev/backups' / stamp
        for change in changes:
            rel = change['path']
            dst = root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            if change['action'] == 'create':
                dst.write_bytes(z.read(rel))
            else:
                backup_path = backup / rel
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(dst, backup_path)
                template = z.read(rel).decode('utf-8')
                appendix = template[template.rfind(AUDIT_MARKER):]
                dst.write_text(dst.read_text(encoding='utf-8').rstrip() + '\n\n' + appendix, encoding='utf-8')
    return {'applied': True, 'changes': changes, 'backup': str(backup) if backup.exists() else None,
            'note': '기존 설정은 유지. 작업 실행과 실제 모델 기반 테스트는 별도 검증 필요'}

TDD_MARKER = '## Task-Type TDD Policy (v0.9)'
TDD_GUIDANCE = '''## Task-Type TDD Policy (v0.9)

At task creation classify using `teamdev new TASK-ID "title" --type TYPE` (default feature).
Before plan-ready type correction: `teamdev tdd-set TASK-ID --type TYPE --actor coordinator`.
Required (feature, bugfix, behavior_change, api, business_logic): RED/GREEN/REFACTOR with original logs.
Conditional (ui_visual, configuration, refactoring): approved alternative verification with original logs.
Exempt (documentation): documentation validation still required. Before verification run `teamdev tdd-check TASK-ID`.
A missing manifest blocks implementation report, verification, and final approval. See docs/TDD-POLICY.md.
Existing tasks without a TDD classification remain legacy; do not silently rewrite an approved plan.
'''

def upgrade_tdd(root: Path, apply: bool = False) -> dict:
    """Non-destructive additive migration: preserve all existing policy and agent settings."""
    root = root.resolve()
    if not (root / '.ai-dev/policy.json').is_file() or not (root / 'AGENTS.md').is_file():
        raise core.WorkflowError('먼저 teamdev init한 프로젝트에서 실행하세요')
    docs = ['docs/TDD-POLICY.md', '.agents/skills/tdd-workflow/SKILL.md', '.opencode/skills/tdd-workflow/SKILL.md', '.claude/skills/tdd-workflow/SKILL.md']
    prompt_files = ['AGENTS.md', '.opencode/agents/coordinator.md',
                    '.claude/agents/coordinator.md', '.opencode/agents/implementer.md',
                    '.claude/agents/implementer.md', '.opencode/agents/verifier.md',
                    '.claude/agents/verifier.md', 'docs/WORKFLOW.md']
    changes, conflicts = [], []
    with zipfile.ZipFile(core.TEMPLATE_DIR / 'bundle.zip') as z:
        for rel in docs:
            if not (root / rel).exists():
                changes.append({'path': rel, 'action': 'create'})
        for rel in prompt_files:
            p = root / rel
            if not p.is_file():
                conflicts.append(rel + ': 파일 없음')
            elif TDD_MARKER not in p.read_text(encoding='utf-8'):
                changes.append({'path': rel, 'action': 'append'})
        policy_file = root / '.ai-dev/policy.json'
        current = core.json_read(policy_file)
        if 'tdd' not in current:
            changes.append({'path': '.ai-dev/policy.json', 'action': 'merge-tdd'})
        elif current['tdd'] != json.loads(z.read('.ai-dev/policy.json'))['tdd']:
            conflicts.append('.ai-dev/policy.json: 기존 사용자 정의 tdd 정책 수동 검토 필요')
        if not apply:
            return {'applied': False, 'changes': changes, 'conflicts': conflicts}
        if conflicts:
            raise core.WorkflowError('자동 병합 중단: ' + '; '.join(conflicts))
        backup = root / '.ai-dev/backups' / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '-tdd')
        for item in changes:
            rel, action = item['path'], item['action']
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists():
                saved = backup / rel
                saved.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(target, saved)
            if action == 'create':
                src = '.agents/skills/tdd-workflow/SKILL.md' if '/skills/tdd-workflow/' in rel else rel
                target.write_bytes(z.read(src))
            elif action == 'append':
                target.write_text(target.read_text(encoding='utf-8').rstrip() + '\n\n' + TDD_GUIDANCE, encoding='utf-8')
            else:
                policy = core.json_read(target)
                policy['tdd'] = json.loads(z.read('.ai-dev/policy.json'))['tdd']
                core.atomic_json(target, policy)
    return {'applied': True, 'changes': changes, 'backup': str(backup) if backup.exists() else None,
            'note': '미완료 및 승인된 기존 TASK 유형은 변경하지 않았습니다.'}


def upgrade_lifecycle_integrity(root: Path, apply: bool = False) -> dict:
    """Non-destructive upgrade of task lifecycle consistency guidance."""
    root = root.resolve()
    if not (root / '.ai-dev/policy.json').is_file():
        raise core.WorkflowError('teamdev init 프로젝트가 아닙니다')
    marker = '## Lifecycle integrity (v0.10)'
    targets = ('AGENTS.md', 'docs/WORKFLOW.md', 'docs/SESSION-START.md',
               'docs/LIFECYCLE-INTEGRITY.md')
    actions = []
    with zipfile.ZipFile(core.TEMPLATE_DIR / 'bundle.zip') as z:
        for rel in targets:
            path = root / rel
            if not path.is_file():
                actions.append({'path': rel, 'action': 'create'})
            elif rel != 'docs/LIFECYCLE-INTEGRITY.md' and marker not in path.read_text(encoding='utf-8'):
                actions.append({'path': rel, 'action': 'append'})
        if not apply:
            return {'applied': False, 'changes': actions}
        backup = root / '.ai-dev/backups' / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '-lifecycle-v010')
        for entry in actions:
            rel = entry['path']
            dst = root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            content = z.read(rel).decode('utf-8')
            if entry['action'] == 'append':
                previous = dst.read_text(encoding='utf-8')
                saved = backup / rel
                saved.parent.mkdir(parents=True, exist_ok=True)
                saved.write_text(previous, encoding='utf-8')
                content = previous.rstrip() + '\n\n' + content[content.index(marker):]
            dst.write_text(content, encoding='utf-8')
        return {'applied': bool(actions), 'changes': actions,
                'backup': str(backup) if backup.exists() else None}


CRG_AUTO_MARKER = '## CRG On-Demand Lifecycle (v0.11)'

def upgrade_crg_auto(root: Path, apply: bool = False) -> dict:
    """Append-only policy upgrade, preserving customized worker/skill files."""
    root = root.resolve()
    if not (root / '.ai-dev/policy.json').is_file():
        raise core.WorkflowError('먼저 teamdev init한 프로젝트에서 실행하세요')
    paths = ['AGENTS.md', '.opencode/agents/coordinator.md', '.claude/agents/coordinator.md',
             '.opencode/agents/reviewer.md', '.claude/agents/reviewer.md', 'docs/TOOLS.md',
             '.agents/skills/code-graph-analysis/SKILL.md',
             '.opencode/skills/code-graph-analysis/SKILL.md',
             '.claude/skills/code-graph-analysis/SKILL.md']
    policy = ('\n\n' + CRG_AUTO_MARKER + '\n'
      '- CRG is optional: call `teamdev crg-auto` at ANALYZE/REVIEW when cross-file impact matters.\n'
      '- If SKIP_EMPTY or FALLBACK_NO_CRG, continue using native code reading/rg; never block project bootstrap.\n'
      '- If BUILD/REBUILD, only after the project contains source run `teamdev crg-auto --apply` then confirm graph.db and actual graph queries.\n'
      '- READY_CANDIDATE proves only file timestamp ordering, not full graph validity.\n'
      '- Recommended external skills are OPTIONAL and NOT automatically loaded or downloaded; discover and load only installed skills relevant to the task.\n')
    changes = [p for p in paths if (root/p).is_file() and CRG_AUTO_MARKER not in (root/p).read_text(encoding='utf-8')]
    if not apply:
        return {'applied':False, 'append_to':changes, 'missing_preserved':[p for p in paths if not (root/p).is_file()]}
    backup = root/'.ai-dev/backups'/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-crg-auto')
    for rel in changes:
        p = root/rel
        dest=backup/rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dest)
        p.write_text(p.read_text(encoding='utf-8').rstrip()+policy, encoding='utf-8')
    return {'applied':True, 'updated':changes, 'backup':str(backup) if changes else None,
            'note':'기존 개인 설정과 스킬 본문 보존; 정책만 추가. 구버전 skill 설명과 충돌하면 새 정책 우선.'}


VISIBILITY_MARKER = '## Startup Dashboard and Skill Usage Ledger (v0.12)'

def upgrade_visibility(root: Path, apply: bool = False) -> dict:
    """Append v0.12 guidance and add docs; preserve every existing user instruction."""
    root = root.resolve()
    if not (root/'.ai-dev/policy.json').is_file():
        raise core.WorkflowError('teamdev init한 프로젝트에서 실행하세요')
    candidates = ('AGENTS.md','CLAUDE.md','docs/SESSION-START.md','docs/STARTUP-DASHBOARD.md',
                  '.opencode/agents/coordinator.md','.claude/agents/coordinator.md')
    with zipfile.ZipFile(core.TEMPLATE_DIR/'bundle.zip') as z:
        changes=[]
        for rel in candidates:
            path=root/rel
            if path.is_file() and VISIBILITY_MARKER not in path.read_text(encoding='utf-8'):
                changes.append({'path':rel,'action':'append'})
            elif not path.exists() and rel in z.namelist():
                changes.append({'path':rel,'action':'create'})
        if not (root/'docs/SKILL-HISTORY.md').exists():
            changes.append({'path':'docs/SKILL-HISTORY.md','action':'create'})
        if not apply:
            return {'applied':False,'changes':changes}
        backup=root/'.ai-dev/backups'/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-visibility')
        for entry in changes:
            rel=entry['path']; dst=root/rel; dst.parent.mkdir(parents=True,exist_ok=True)
            content=z.read(rel).decode('utf-8')
            if entry['action']=='append':
                src=dst.read_text(encoding='utf-8')
                bp=backup/rel;bp.parent.mkdir(parents=True,exist_ok=True);bp.write_text(src,encoding='utf-8')
                content=src.rstrip()+'\n\n'+content[content.index(VISIBILITY_MARKER):]
            dst.write_text(content,encoding='utf-8')
        return {'applied':bool(changes),'changes':changes,'backup':str(backup) if backup.exists() else None}


PROGRESS_MARKER = '## Coordinator Progress Reporting (v0.14)'
PROGRESS_GUIDANCE = '## Coordinator Progress Reporting (v0.14)\n\n- Run `teamdev progress --task TASK-ID` at meaningful transitions: after PLAN is ready (before requesting approval), after confirmed Worker dispatch, after Worker return, after VERIFY/REVIEW result recording, before final user approval, and after COMPLETE archive. Also show `teamdev progress` at SESSION start when tasks exist.\n- Present a concise human-readable status: TASK, stage, workflow status, Worker / observed activity, stage pipeline, user action, and next execution. Report FAIL / BLOCKED immediately.\n- Show actual monitored facts, not fabricated progress percentages. `RECENT_ACTIVITY` from heartbeat is not proof of a live native Worker or of successful verification. Never call `worker-start` before confirmed dispatch or `worker-stop` before confirmed return.\n- Do not poll `teamdev monitor` inside a synchronous native Task call. During long runs the human may use a separate terminal: `teamdev monitor --watch --interval 3`. Only report genuine new progress on real events, not repetitive messages.\n- Preserve both explicit human approval gates. Progress display must never auto-approve, advance workflow, or overwrite TASK evidence.\n- Detailed usage: `docs/PROGRESS.md`. `teamdev progress --json` is read-only and machine-readable.\n'

def upgrade_progress(root: Path, apply: bool = False) -> dict:
    """Add status reporting to existing framework without overwriting custom prompts."""
    root = root.resolve()
    if not (root/'.ai-dev/policy.json').is_file():
        raise core.WorkflowError('teamdev init한 프로젝트에서 실행하세요')
    targets = ('AGENTS.md','CLAUDE.md','.opencode/agents/coordinator.md',
               '.claude/agents/coordinator.md','docs/WORKFLOW.md',
               'docs/STARTUP-DASHBOARD.md','docs/MONITOR.md')
    changes=[]
    with zipfile.ZipFile(core.TEMPLATE_DIR/'bundle.zip') as z:
        for rel in targets:
            dst=root/rel
            if dst.is_file():
                if PROGRESS_MARKER not in dst.read_text(encoding='utf-8'):
                    changes.append({'path':rel,'action':'append'})
            elif rel in z.namelist():
                changes.append({'path':rel,'action':'create'})
        if not (root/'docs/PROGRESS.md').is_file():
            changes.append({'path':'docs/PROGRESS.md','action':'create'})
        if not apply:
            return {'applied':False,'changes':changes}
        backup=root/'.ai-dev/backups'/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-progress')
        for change in changes:
            rel=change['path']
            dst=root/rel
            dst.parent.mkdir(parents=True,exist_ok=True)
            if change['action']=='append':
                old=dst.read_text(encoding='utf-8')
                bk=backup/rel
                bk.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(dst,bk)
                dst.write_text(old.rstrip()+'\n\n'+PROGRESS_GUIDANCE,encoding='utf-8')
            else:
                dst.write_bytes(z.read(rel))
        return {'applied':bool(changes),'changes':changes,
                'backup':str(backup) if backup.exists() else None}


# v0.15: targeted migration; unlike routing upgrade, never replace the agent prompt.
COORDINATOR_EDIT_RULES_V014 = '''  edit:
    "*": deny
    "docs/product-specs/**": allow
    "docs/exec-plans/active/**": allow
    "docs/tasks/**": allow
'''


def upgrade_coordinator_permissions(root: Path, apply: bool = False) -> dict:
    """Add absolute-path-compatible doc rules only to known framework edit block.

    Never rewrite other agent permissions, instructions, or application files.
    Unknown policy configurations are a conflict requiring manual review.
    """
    root = root.resolve()
    if not (root/'.ai-dev/policy.json').is_file():
        raise core.WorkflowError('teamdev init한 프로젝트에서 실행하세요')
    rel = '.opencode/agents/coordinator.md'
    path = root/rel
    if not path.is_file():
        raise core.WorkflowError(f'{rel}: 파일 없음')
    original = path.read_text(encoding='utf-8')
    if original.count(COORDINATOR_EDIT_RULES) == 1:
        return {'applied': False, 'changes': [], 'status': 'UP_TO_DATE'}
    if original.count(COORDINATOR_EDIT_RULES_V014) != 1:
        raise core.WorkflowError(f'{rel}: 알려지지 않은 edit 정책; 수동 검토 필요 (변경하지 않음)')
    changes = [{'path': rel, 'action': 'scoped-edit-globs'}]
    if not apply:
        return {'applied': False, 'changes': changes, 'status': 'PREVIEW'}
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-coordinator-permissions'
    backup = root/'.ai-dev/backups'/stamp/rel
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, backup)
    updated = original.replace(COORDINATOR_EDIT_RULES_V014, COORDINATOR_EDIT_RULES, 1)
    path.write_text(updated, encoding='utf-8')
    return {'applied': True, 'changes': changes, 'status': 'UPDATED',
            'backup': str(backup),
            'warning': '도구의 경로 매칭은 런타임에서 재검증 필요. bash allow는 소스 수정 차단을 보장하지 않음.'}

COORDINATOR_RECOVERY_MARKER = '## Orca Coordinator Session Recovery (v0.16)'
COORDINATOR_RECOVERY_GUIDANCE = '''## Orca Coordinator Session Recovery (v0.16)

- Keep TASK, worktree, approvals and evidence stable. Only the **main Coordinator model conversation** changes; do not spawn another Coordinator as a subagent.
- At a safe stage boundary (or when context pressure is detected), ensure any native Worker call has actually returned and its monitoring record is stopped. Then use `teamdev coordinator-handoff TASK --session-id CURRENT --next-action "one next action" --reason "context pressure"`.
- This command freezes `teamdev next`, native Worker registration and CLI Worker execution for that TASK while PREPARED. The freeze is enforced by cooperating `teamdev` commands, not by Orca or direct file writes.
- In Orca, open a **fresh main Coordinator conversation** in the same project/worktree. Do not resume the old context or have both conversations advance the same TASK.
- After confirming the old Coordinator is inactive, from the NEW session call `teamdev coordinator-resume TASK --new-session-id NEW --old-session-stopped`. The flag is an operator/agent assertion, **not** an independent process-liveness check.
- Read the short `docs/tasks/TASK/coordinator-handoff.md`, run `teamdev startup`, `teamdev status TASK`, `teamdev next TASK` and verify approvals and Worker ownership before dispatch.
- No fictional token percentage: checkpoint at real phase boundaries or contextual pressure. No automatic Orca window creation/clearing is claimed. `teamdev coordinator-session TASK` shows PREPARED/RESUMED state.
- Handoffs preserve original logs externally; never paste secrets, transcript dumps or raw logs into the handoff file. Do not commit or push without separate user approval.
'''


def upgrade_coordinator_recovery(root: Path, apply: bool = False) -> dict:
    """Non-destructive append of Orca recovery policy into existing framework docs."""
    root = root.resolve()
    if not (root / '.ai-dev/policy.json').is_file():
        raise core.WorkflowError('teamdev init한 프로젝트에서 실행하세요')
    targets = ('AGENTS.md', 'CLAUDE.md', '.opencode/agents/coordinator.md',
               '.claude/agents/coordinator.md', 'docs/SESSION-ROTATION.md')
    changes=[]
    for rel in targets:
        p=root/rel
        if p.is_file() and COORDINATOR_RECOVERY_MARKER not in p.read_text(encoding='utf-8'):
            changes.append({'path':rel,'action':'append'})
    if not (root/'docs/COORDINATOR-RECOVERY.md').exists():
        changes.append({'path':'docs/COORDINATOR-RECOVERY.md','action':'create'})
    if not apply:
        return {'applied':False,'changes':changes}
    backup=root/'.ai-dev/backups'/(datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-coordinator-recovery')
    for ch in changes:
        dst=root/ch['path']; dst.parent.mkdir(parents=True,exist_ok=True)
        if ch['action']=='append':
            b=backup/ch['path']; b.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(dst,b)
            dst.write_text(dst.read_text(encoding='utf-8').rstrip()+'\n\n'+COORDINATOR_RECOVERY_GUIDANCE,encoding='utf-8')
        else:
            dst.write_text('# Orca Coordinator Session Recovery\n\n'+COORDINATOR_RECOVERY_GUIDANCE,encoding='utf-8')
    return {'applied':bool(changes),'changes':changes,'backup':str(backup) if backup.exists() else None}


WORKER_DISPATCH_MARKER = '## Native Worker Dispatch and Monitoring (v0.17)'

def upgrade_worker_dispatch(root: Path, apply: bool = False) -> dict:
    """Append-only, backed-up v0.17 Coordinator guidance. No TASK mutation."""
    root = root.resolve()
    if not (root/'.ai-dev/policy.json').is_file():
        raise core.WorkflowError('teamdev init한 프로젝트에서 실행하세요')
    paths = ['AGENTS.md', 'CLAUDE.md', '.opencode/agents/coordinator.md',
             '.claude/agents/coordinator.md', 'docs/WORKFLOW.md',
             'docs/MONITOR.md', 'docs/PROGRESS.md']
    with zipfile.ZipFile(core.TEMPLATE_DIR / 'bundle.zip') as z:
        changes = []
        for rel in paths:
            target = root / rel
            if not target.is_file():
                continue  # preserve absent / custom files
            if WORKER_DISPATCH_MARKER not in target.read_text(encoding='utf-8'):
                changes.append(rel)
        if not apply:
            return {'applied': False, 'append_to': changes}
        backup = root / '.ai-dev/backups' / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-worker-dispatch')
        for rel in changes:
            target = root / rel
            template = z.read(rel).decode('utf-8')
            appendix = template[template.index(WORKER_DISPATCH_MARKER):]
            saved = backup / rel
            saved.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target, saved)
            target.write_text(target.read_text(encoding='utf-8').rstrip()+'\n\n'+appendix, encoding='utf-8')
        return {'applied': True, 'updated': changes,
                'backup': str(backup) if changes else None}


DOCUMENT_SOURCES_MARKER = '## Design Documents and References (v0.18)'
DOCUMENT_SOURCES_NEW = [
    'docs/DOCUMENT-SOURCES.md',
    'docs/design-docs/README.md',
    'docs/references/README.md',
]
DOCUMENT_SOURCES_GUIDANCE = [
    'AGENTS.md', 'CLAUDE.md', 'docs/WORKFLOW.md',
    '.opencode/agents/coordinator.md', '.claude/agents/coordinator.md',
    '.opencode/agents/implementer.md', '.claude/agents/implementer.md',
    '.opencode/agents/verifier.md', '.claude/agents/verifier.md',
    '.opencode/agents/reviewer.md', '.claude/agents/reviewer.md',
]


def upgrade_document_sources(root: Path, apply: bool = False) -> dict:
    """Non-destructive document directory adoption; no task state or source changes."""
    root = root.resolve()
    if not (root / 'AGENTS.md').is_file() or not (root / '.ai-dev/policy.json').is_file():
        raise core.WorkflowError('teamdev init한 프로젝트에서 실행하세요')
    with zipfile.ZipFile(core.TEMPLATE_DIR / 'bundle.zip') as z:
        actions = []
        for rel in DOCUMENT_SOURCES_NEW:
            if not (root / rel).exists():
                actions.append({'path': rel, 'action': 'create'})
        for rel in DOCUMENT_SOURCES_GUIDANCE:
            dest = root / rel
            if dest.is_file() and DOCUMENT_SOURCES_MARKER not in dest.read_text(encoding='utf-8') and rel in z.namelist():
                actions.append({'path': rel, 'action': 'append'})
        if not apply:
            return {'applied': False, 'changes': actions, 'message': '미리보기만 수행; --apply로 명시 적용'}
        backup = root / '.ai-dev/backups' / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '-document-sources')
        for item in actions:
            rel = item['path']
            dst = root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            if item['action'] == 'create':
                dst.write_bytes(z.read(rel))
            else:
                b = backup / rel
                b.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(dst, b)
                template = z.read(rel).decode('utf-8')
                appendix = template[template.index(DOCUMENT_SOURCES_MARKER):]
                dst.write_text(dst.read_text(encoding='utf-8').rstrip() + '\n\n' + appendix, encoding='utf-8')
        return {'applied': bool(actions), 'changes': actions,
                'backup': str(backup) if backup.exists() else None,
                'note': '기존 design-docs/references의 파일, Spec/Plan/TASK 상태는 보존'}


# Default OpenCode project configuration requested by the user (v0.18.1).
OPENCODE_CONFIG_TARGET = {
    'default_agent': 'coordinator',
    'permission': {
        'read': 'allow', 'edit': 'allow', 'task': 'allow', 'skill': 'allow',
        'bash': {'*': 'allow', 'git commit *': 'ask', 'git push *': 'ask',
                 'git reset --hard *': 'deny', 'rm -rf *': 'ask'},
        'external_directory': 'allow', 'doom_loop': 'ask',
    },
    'lsp': True,
}


def upgrade_opencode_config(root: Path, apply: bool = False) -> dict:
    """Opt-in merge of the framework OpenCode defaults, preserving user-added keys.

    Any modified framework-managed fields are reported and backed up before updating.
    This affects project opencode.json, not ~/.config/opencode/opencode.json.
    """
    root = root.resolve()
    if not (root / 'AGENTS.md').is_file() or not (root / '.ai-dev/policy.json').is_file():
        raise core.WorkflowError('teamdev init한 프로젝트에서 실행하세요')
    path = root / 'opencode.json'
    old = core.json_read(path) if path.is_file() else {}
    if not isinstance(old, dict):
        raise core.WorkflowError('opencode.json 최상위 구조는 객체여야 합니다')
    if 'permissions' in old or 'policies' in old:
        raise core.WorkflowError('기존 V2 permissions/policies 설정은 수동 검토가 필요합니다')
    existing_permission = old.get('permission', {})
    if not isinstance(existing_permission, dict):
        raise core.WorkflowError('permission이 객체가 아니므로 자동 병합할 수 없습니다')
    existing_bash = existing_permission.get('bash', {})
    if not isinstance(existing_bash, dict):
        raise core.WorkflowError('bash 권한이 객체가 아니므로 자동 병합할 수 없습니다')
    new = dict(old)
    new.setdefault('$schema', 'https://opencode.ai/config.json')
    new['default_agent'] = OPENCODE_CONFIG_TARGET['default_agent']
    new_permission = dict(existing_permission)
    for key, value in OPENCODE_CONFIG_TARGET['permission'].items():
        if key == 'bash':
            merged_bash = dict(existing_bash)
            merged_bash.update(value)
            new_permission['bash'] = merged_bash
        else:
            new_permission[key] = value
    new['permission'] = new_permission
    new['lsp'] = True
    changed = [key for key in ('$schema', 'default_agent', 'permission', 'lsp')
               if old.get(key) != new.get(key)]
    if not apply:
        return {'applied': False, 'path': str(path), 'changed': changed,
                'preserved_extra_keys': sorted(set(old) - {'$schema', 'default_agent', 'permission', 'lsp'}),
                'warning': 'edit/bash/external_directory 허용은 강한 권한입니다. 별도 에이전트별 permission과 사람 승인 규칙은 유지됩니다.'}
    if not changed:
        return {'applied': False, 'path': str(path), 'changed': [], 'backup': None}
    backup = None
    if path.is_file():
        backup = root / '.ai-dev/backups' / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '-opencode-config') / 'opencode.json'
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, backup)
    core.atomic_json(path, new)
    return {'applied': True, 'path': str(path), 'changed': changed,
            'backup': str(backup) if backup else None,
            'warning': '편집/명령/외부 디렉터리 접근을 허용합니다. 기존 에이전트별 deny/ask 규칙은 별도로 평가됩니다.'}

SELF_IMPROVEMENT_MARKER = '## Self-Improvement Approval Gate (v0.18.2)'
SELF_IMPROVEMENT_NEW = [
    'docs/SELF-IMPROVEMENT.md',
    'docs/agent-improvements/candidates/README.md',
    'docs/agent-improvements/approved/README.md',
    'docs/agent-improvements/rejected/README.md',
]


def upgrade_self_improvement(root: Path, apply: bool = False) -> dict:
    """Opt-in migration: create missing policy docs, append deduplicated guidance."""
    root = root.resolve()
    if not (root / 'AGENTS.md').is_file() or not (root / '.ai-dev/policy.json').is_file():
        raise core.WorkflowError('teamdev init한 기존 프로젝트에서 실행하세요')
    with zipfile.ZipFile(core.TEMPLATE_DIR / 'bundle.zip') as z:
        actions = []
        for rel in SELF_IMPROVEMENT_NEW:
            if not (root / rel).exists():
                actions.append({'path': rel, 'action': 'create'})
        for rel in ('AGENTS.md', 'CLAUDE.md', 'docs/WORKFLOW.md'):
            dst = root / rel
            marker = SELF_IMPROVEMENT_MARKER if rel != 'docs/WORKFLOW.md' else '## 자가개선 정식 반영 (v0.18.2)'
            if dst.is_file() and marker not in dst.read_text(encoding='utf-8'):
                actions.append({'path': rel, 'action': 'append'})
        if not apply:
            return {'applied': False, 'changes': actions}
        backup = root / '.ai-dev/backups' / (datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '-self-improvement')
        for change in actions:
            rel = change['path']
            dst = root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            if change['action'] == 'create':
                dst.write_bytes(z.read(rel))
            else:
                old = backup / rel
                old.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(dst, old)
                template = z.read(rel).decode('utf-8')
                marker = SELF_IMPROVEMENT_MARKER if rel != 'docs/WORKFLOW.md' else '## 자가개선 정식 반영 (v0.18.2)'
                dst.write_text(dst.read_text(encoding='utf-8').rstrip() + '\n\n' + template[template.index(marker):], encoding='utf-8')
        return {'applied': bool(actions), 'changes': actions,
                'backup': str(backup) if backup.exists() else None,
                'note': '기존 작업/설계/설정 파일은 유지; 승인 없이 개선 정본 반영 없음'}
