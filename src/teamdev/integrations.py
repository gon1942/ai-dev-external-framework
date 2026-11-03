"""Optional CRG / RTK integrations. No network access or global edits on init.

External CLIs are not bundled. Explicit setup runs only trusted binary names with
argument arrays; agents must inspect native tool output before claiming success.
"""
from __future__ import annotations
import json
import shutil
import subprocess
from pathlib import Path
from . import core

RTK = {"opencode": ["rtk", "init", "-g", "--opencode"],
       "claude": ["rtk", "init", "-g", "--auto-patch"],
       "codex": ["rtk", "init", "-g", "--codex"]}
CRG_INSTALL = ["code-review-graph", "install"]
CRG_BUILD = ["code-review-graph", "build"]


def _found(name: str) -> str | None:
    return shutil.which(name)


def tool_status(root: Path) -> dict:
    root = root.resolve()
    crg_graph = root / '.code-review-graph'
    crg_venv_binary = root / '.ai-dev/crg-venv/bin/code-review-graph'
    crg_bin = _found('code-review-graph') or (str(crg_venv_binary) if crg_venv_binary.is_file() else None)
    rtk_bin = _found('rtk')
    crg_skill = [(p, (root / p).is_file()) for p in (
        '.agents/skills/code-graph-analysis/SKILL.md',
        '.opencode/skills/code-graph-analysis/SKILL.md',
        '.claude/skills/code-graph-analysis/SKILL.md')]
    return {
        'rtk': {'installed': bool(rtk_bin), 'binary': rtk_bin,
                'native_hook_checked': False, 'note': 'CLI 발견은 hook 활성화 증거가 아닙니다. rtk init --show 및 도구별 실제 호출 확인 필요'},
        'crg': {'installed': bool(crg_bin), 'binary': crg_bin,
                'graph_directory_present': crg_graph.is_dir(),
                'graph_freshness_verified': False,
                'skill_discovery': {k: v for k, v in crg_skill},
                'note': '디렉터리 존재는 그래프 최신성 또는 MCP 연결을 증명하지 않습니다'},
        'optional_dependencies_required': False,
    }


def _invoke(argv: list[str], cwd: Path, *, execute: bool, runner=None) -> dict:
    if not execute:
        return {'executed': False, 'command': argv, 'cwd': str(cwd),
                'note': '미리보기만 수행. 실제 적용은 --apply로 명시하세요.'}
    if not _found(argv[0]) and not (cwd / '.ai-dev/crg-venv/bin' / argv[0]).is_file():
        raise core.WorkflowError(f'도구 실행 파일을 찾을 수 없습니다: {argv[0]}')
    if runner is None:
        runner = subprocess.run
    try:
        p = runner(argv, cwd=cwd, check=False, capture_output=True, text=True, timeout=120)
    except (subprocess.TimeoutExpired, OSError) as e:
        raise core.WorkflowError(f'도구 초기화/실행 실패: {e}') from e
    if p.returncode != 0:
        raise core.WorkflowError(f'도구 실행 실패 (exit={p.returncode}): {(p.stderr or p.stdout)[-1000:]}')
    return {'executed': True, 'command': argv, 'cwd': str(cwd), 'exit_code': p.returncode,
            'output_tail': (p.stdout or '')[-1000:],
            'note': 'CLI 명령 완료만 확인했습니다. 코딩 에이전트에서 실제 hook/MCP 적용 여부를 별도 점검하세요.'}


def setup_tool(root: Path, tool: str, runtime: str | None = None, *, apply: bool = False, runner=None) -> dict:
    root = root.resolve()
    if not (root / '.ai-dev/policy.json').is_file():
        raise core.WorkflowError('프레임워크 프로젝트에서 실행하세요: .ai-dev/policy.json 필요')
    if tool == 'rtk':
        if runtime not in RTK:
            raise core.WorkflowError('RTK는 --runtime opencode|claude|codex 필요')
        argv = RTK[runtime]
        return {**_invoke(argv, root, execute=apply, runner=runner), 'tool': tool,
                'runtime': runtime, 'scope': 'USER_GLOBAL',
                'warning': 'rtk init -g는 사용자 홈 설정을 변경합니다. 팀 저장소에 공유되지 않으며 설정 백업/검토가 필요합니다.'}
    if tool == 'crg':
        if runtime is not None:
            raise core.WorkflowError('CRG install은 단일 공통 명령입니다. --runtime 제외')
        return {**_invoke(CRG_INSTALL, root, execute=apply, runner=runner), 'tool': tool,
                'warning': 'CRG install은 에이전트 설정을 변경할 수 있습니다. 적용 전에 실제 변경 범위를 확인하세요.'}
    raise core.WorkflowError('지원 도구: rtk / crg')


def build_graph(root: Path, *, apply: bool = False, runner=None) -> dict:
    root = root.resolve()
    if not (root / '.ai-dev/policy.json').is_file():
        raise core.WorkflowError('프레임워크 프로젝트에서 실행하세요')
    cmd = CRG_BUILD.copy()
    private = root / '.ai-dev/crg-venv/bin/code-review-graph'
    if private.is_file() and not _found('code-review-graph'):
        cmd[0] = str(private)
    if not apply:
        return {'executed': False, 'command': cmd, 'cwd': str(root),
                'note': '그래프 생성/갱신은 명시적 --apply 필요'}
    if not _found('code-review-graph') and not private.is_file():
        raise core.WorkflowError('CRG 미설치: code-review-graph CLI 또는 .ai-dev/crg-venv 필요')
    return _invoke(cmd, root, execute=True, runner=runner)


# Source readiness is a local heuristic, not proof that a CRG index is semantically fresh.
SOURCE_SUFFIXES = frozenset({'.py', '.pyi', '.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs', '.java', '.go', '.rs', '.c', '.h', '.cpp', '.hpp', '.cs', '.rb', '.php', '.kt', '.swift', '.vue', '.svelte'})
EXCLUDED_DIRS = frozenset({'.git', '.hg', '.svn', '.code-review-graph', '.ai-dev', '.opencode', '.claude', '.codex', '.agents', 'node_modules', '.venv', 'venv', '__pycache__', 'dist', 'build', 'coverage', '.next', '.pytest_cache'})


def _source_snapshot(root: Path) -> dict:
    import os
    count = 0
    latest = 0.0
    for base, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS and not (Path(base) / d).is_symlink()]
        for filename in files:
            p = Path(base) / filename
            if p.suffix.lower() not in SOURCE_SUFFIXES or p.is_symlink():
                continue
            try:
                if not p.is_file():
                    continue
                latest = max(latest, p.stat().st_mtime)
                count += 1
            except OSError:
                continue
    return {'count': count, 'latest_mtime': latest}


def graph_auto_status(root: Path) -> dict:
    """Read-only: no CRG commands and no project modifications."""
    root = root.resolve()
    if not (root / '.ai-dev/policy.json').is_file():
        raise core.WorkflowError('먼저 teamdev init한 프로젝트에서 실행하세요')
    sources = _source_snapshot(root)
    binary = tool_status(root)['crg']['binary']
    db = root / '.code-review-graph/graph.db'
    graph = db.is_file()
    graph_mtime = db.stat().st_mtime if graph else None
    stale = bool(graph and sources['latest_mtime'] > graph_mtime + 0.001)
    if sources['count'] == 0:
        action = 'SKIP_EMPTY'
    elif binary is None:
        action = 'FALLBACK_NO_CRG'
    elif not graph:
        action = 'BUILD'
    elif stale:
        action = 'REBUILD'
    else:
        action = 'READY_CANDIDATE'
    return {'action': action, 'source_files': sources['count'], 'crg_installed': binary is not None,
            'graph_db_present': graph, 'source_newer_than_graph': stale,
            'graph_freshness': 'MTIME_ONLY_NOT_VERIFIED' if graph else 'NO_GRAPH',
            'note': '빈 폴더는 정상 SKIP. 그래프 최신성은 수정시간의 보수적 추정일 뿐 실제 CRG 분석 가능 여부 확인이 필요합니다.'}


def auto_graph(root: Path, *, apply: bool = False, runner=None) -> dict:
    """Local on-demand graph preparation. No installs, hooks, network setup or approvals."""
    status = graph_auto_status(root)
    action = status['action']
    if action in ('SKIP_EMPTY', 'FALLBACK_NO_CRG', 'READY_CANDIDATE'):
        return {**status, 'executed': False, 'result': 'SKIPPED' if action != 'READY_CANDIDATE' else 'CANDIDATE_READY'}
    if not apply:
        return {**status, 'executed': False, 'result': 'PREVIEW', 'command': CRG_BUILD}
    # The documented CRG build command is used for both initial build and rebuild.
    # Do not assume every installed CRG version supports an incremental update command.
    result = build_graph(root, apply=True, runner=runner)
    db = root.resolve() / '.code-review-graph/graph.db'
    return {**status, **result, 'result': 'GRAPH_CREATED' if db.is_file() else 'BUILD_EXITED_NO_GRAPH',
            'graph_db_present_after': db.is_file(),
            'note': 'CRG build exit=0 확인. 그래프 파일과 실제 CRG 탐색 명령의 유효성은 별도로 검사하세요.'}
