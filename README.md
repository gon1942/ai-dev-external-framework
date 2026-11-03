# Team AI Dev Framework v2.0.0 — npm / npx Bootstrap

v0.18.2 Python workflow 엔진은 유지하고 신규 설치와 기존 프로젝트 적용을 위한 Node.js/npm 실행 계층을 추가했습니다. **npm registry에는 아직 배포하지 않았으며**, npm 배포용 tarball을 제공합니다.

- `npm/` — npm 패키지 및 Node.js 설치/업그레이드 실행기
- `npm/vendor/*.whl` — Python workflow 엔진 내장; 프로젝트 `.ai-dev/.runtime`에 독립 설치
- `init <project>` — 신규 프로젝트 안전 생성 (`--force` 미사용)
- `upgrade --project .` — 기존 Team AI Dev 프로젝트 미리보기; `--apply` 명시 시 선택된 비파괴 업그레이드
- `adopt --project . --apply` — 기존 별도 프레임워크가 없는 프로젝트에 안전 초기 설치
- 기존 `ai-dev-external-framework` 상태가 탐지되면 자동 교체하지 않고 중단 (상태 스키마 이관 별도 필요)
- `doctor --project .`, `cli --project . -- startup` 지원

**로컬 시험:**

```bash
npm install -g ./gon1942-team-ai-dev-framework-0.19.0.tgz
team-ai-dev init my-project
team-ai-dev upgrade --project my-project       # preview
team-ai-dev upgrade --project my-project --apply
team-ai-dev doctor --project my-project
```

배포 후에는 `npx --yes @gon1942/team-ai-dev-framework@0.19.0 init my-project`와 동일한 사용자 인터페이스가 됩니다. 자세한 설명과 한계는 `npm/README.md`를 참고하세요.

---

# Team AI Dev Framework v0.18.2 — 설계문서·참고자료 연계

v0.17.0 기능을 유지하며 `docs/design-docs/`(제품 설계 정본), `docs/references/`(근거/레거시/조사)를 **선택적으로** 활용하도록 개선했습니다. 기존 `architecture/`, `decisions/`, Spec/Plan/Task는 그대로 유지합니다. 전체 문서를 매번 로딩하지 않습니다.

기존 설치 프로젝트 업그레이드(기본은 미리보기, 기존 파일 자동 덮어쓰기 없음):

```bash
teamdev --root . upgrade-document-sources
teamdev --root . upgrade-document-sources --apply
```

신규 설치는 `teamdev init`으로 디렉터리 안내 문서를 포함합니다. 문서 사용 기준: `docs/DOCUMENT-SOURCES.md`. 기존 내용이 있는 문서는 수정하지 않으며, AGENTS/Coordinator/Worker/WORKFLOW 지침은 백업 후 중복 없이 추가됩니다.

---

# Team AI Dev Framework v0.17.0 — Native Worker Dispatch + Monitor

Coordinator의 `plan-ready`와 `dispatch` 누락, `worker-start`와 동기 네이티브 Task 병렬 호출 문제를 예방합니다.

- `teamdev worker-prepare TASK --role implementer|verifier|reviewer`: 현재 상태 검사, IMPLEMENT 최초 dispatch 보장, 중복 호출 방지. **Worker를 실행하지 않음**.
- `teamdev worker-return TASK --role ROLE --session-id ID --status FINISHED`: 네이티브 Task가 실제 반환된 이후 Coordinator가 결과 관측을 기록. 독립 런타임 검증 아님.
- `teamdev monitor --task TASK`: 승인·대기 상태와 활동 이벤트를 구분; 무기록은 UNTRACKED.
- `teamdev progress --task TASK`: 사용자 조치·다음 단계 보고.
- `teamdev upgrade-worker-dispatch --apply`: 기존 AGENTS/Coordinator/WORKFLOW 문서를 백업 후 **지침만 추가**. Task 및 소스 파일 변경 없음.

## 정상 실행 순서

```bash
teamdev new TASK-001 '기능' --type feature
# Spec/Plan 작성 후
a=coordinator
teamdev plan-ready TASK-001 --actor "$a"
# 사람이 명시적으로 승인한 이후
teamdev approve TASK-001 --scope plan --actor user --confirm APPROVE
teamdev worker-prepare TASK-001 --role implementer
teamdev monitor --task TASK-001
teamdev progress --task TASK-001
# 이때 Orca/OpenCode 네이티브 Task로 Implementer 실제 실행 (위 CLI는 실행하지 않음)
# 네이티브 Task 호출이 반환된 다음에만:
teamdev worker-return TASK-001 --role implementer --session-id REAL_SESSION_ID --status FINISHED
teamdev monitor --task TASK-001
teamdev progress --task TASK-001
# report / verifier / review는 각각 실제 증거와 상태 전환 후 이어서 진행
```

동기 네이티브 Task 호출 중에는 Coordinator가 monitor를 실행할 수 없습니다. 실시간 Worker 상태를 원한다면 런타임 훅 또는 별도 터미널 `teamdev monitor --watch`가 필요합니다. `worker-return`은 자기 신고 활동 기록이며 QA PASS 증명이 아닙니다.

업그레이드: 최신 패키지 설치 후 기존 프로젝트에서 `teamdev upgrade-worker-dispatch` (미리보기) / `teamdev upgrade-worker-dispatch --apply`.

---

# Team AI Dev Framework v0.16.0

## Coordinator 문서 편집 권한 개선

- OpenCode Coordinator의 `permission.edit`에서 기존 상대 경로 규칙에 `**/docs/...` 경로 패턴을 추가했습니다.
- 신규 프로젝트는 수정된 `.opencode/agents/coordinator.md`를 포함합니다.
- 기존 프로젝트에는 아래 비파괴 마이그레이션을 적용합니다. **기존 지침과 Bash/Task 권한은 유지**하며 변경 전 파일을 `.ai-dev/backups/`에 보관합니다.
- 이미 변경됐거나 사용자 정의 권한인 경우 덮어쓰지 않고 수동 검토를 요구합니다.

```bash
# v0.16.0 소스 폴더에서 설치
python3 -m pip install .
# 기존 프로젝트 루트로 이동
teamdev upgrade-coordinator-permissions
teamdev upgrade-coordinator-permissions --apply
opencode debug agent coordinator
teamdev audit --strict
```

`opencode debug agent coordinator`에서 허용 규칙이 출력되는지 확인한 뒤 실제 `Write docs/product-specs/TASK-ID.md`를 재시험해야 합니다. **패턴 추가만으로 OpenCode 런타임의 Permission 거부가 해결됐다고 단정할 수 없습니다.** 특히 플러그인이나 다른 런타임 제약이 있을 수 있습니다.

보안 주의: `bash: "*": allow`는 명령을 통한 쓰기까지 막지는 않습니다. 계획 승인·완료 승인은 계속 별도 요구합니다.

---

# Team AI Dev Framework v0.14.0

## 새 기능 — Coordinator Progress Reporting

Coordinator가 PLAN 완료/승인 요청, Worker 파견 및 반환, VERIFY·REVIEW 완료, 최종 승인 및 아카이브 시점에 읽기 전용 진행 정보를 표시하는 정책을 추가했습니다.

```bash
teamdev progress                           # 전체 TASK 간결 표시
teamdev progress --task TASK-001           # 한 TASK의 단계 상태 / Worker / 사용자 조치
teamdev progress --task TASK-001 --json    # 자동화용 JSON
teamdev monitor --watch --interval 3       # 별도 터미널에서 활동 관측
```

기존 v0.13.0 프로젝트에서 v0.14.0을 설치한 뒤:

```bash
teamdev upgrade-progress           # 변경 예정 목록
teamdev upgrade-progress --apply   # 기존 지침 백업 후 정책 병합
teamdev startup
teamdev progress
```

상태 표시 예시:

```text
작업 현황 | 해야 할 작업 1건 | 완료 0건 | 승인 대기 1건 | 차단 0건
TASK: TASK-LOGIN-PAGE | Node.js 로그인 페이지
단계: PLAN | 상태: AWAITING_PLAN_APPROVAL | 담당: - | 활동: UNTRACKED
진행: ✓ANALYZE → [PLAN] → ·IMPL → ·VERIFY → ·REVIEW → ·DONE
사용자 조치: 계획 승인/수정 | 다음 실행: 사용자 계획 승인 대기
관측: Worker 실행 관측 기록 없음
```

상태 조회는 **읽기 전용**이며 Worker 실행을 시작하거나 승인하지 않습니다. `RECENT_ACTIVITY`는 실제 네이티브 서브에이전트의 계속 실행이나 테스트 PASS 증거가 아닙니다. 동기 파견 중간에는 Coordinator가 자동으로 주기 조회를 못 할 수 있으며 별도 터미널의 `monitor --watch`를 사용합니다.

---

# Team AI Dev Framework v0.10.0 — 작업 정본 무결성 개선

v0.9.0을 기반으로 작업 완료 후 **Spec·Task·evidence 경로는 유지**하면서 **Plan 폴더만 completed로 이동**하는 방식을 검사하고 보호합니다.

- `teamdev lifecycle-check --strict`: 승인·상태·Plan 위치·Spec/Plan 승인 해시 검사. 오류 시 종료코드 2
- `teamdev next TASK-ID`: 정본이 불일치하면 다음 Worker 단계 진행 중단
- `teamdev audit --strict`와 `teamdev session-summary`: 누락된 Task 상태도 오류로 표시
- `teamdev upgrade-lifecycle-integrity --apply`: 기존 프로젝트에 사용 지침과 문서만 안전 병합(기존 파일 백업)
- 완료 처리는 여전히 사람의 명시적 최종 승인 이후 진행합니다.

## 설치 및 업그레이드

```bash
# ZIP 압축 해제 후 한 번
python3 -m pip install .

# 기존 프로젝트 폴더에서
teamdev upgrade-lifecycle-integrity    # 변경 미리보기
teamdev upgrade-lifecycle-integrity --apply
teamdev lifecycle-check --strict
teamdev session-summary
teamdev audit --strict
```

신규 프로젝트: `mkdir my-project && cd my-project && teamdev init`.

과거 승인 완료 작업이 아직 active에 남아 있다면:

```bash
teamdev archive-completed TASK-ID
teamdev archive-completed TASK-ID --apply
```

**주의:** 이 버전의 검사는 파일·메타데이터의 로컬 일치성만 확인합니다. 실제 검증 명령 실행이나 승인자 신원을 인증하지 않습니다. 잘못된 TASK는 자동 수리하지 않습니다.

---

# Team AI Dev Framework v0.8.0 — Runtime Audit & Startup Dashboard

## 첫 화면 / 신규 설치

```bash
python3 -m pip install -e .
mkdir -p ~/work/demo && cd ~/work/demo
teamdev init
teamdev doctor
teamdev startup
teamdev launch opencode  # 안내 화면 출력 후 OpenCode 시작
```

Claude Code: `teamdev launch claude` / Codex: `teamdev launch codex`.
기본 `opencode` 실행 시에는 Coordinator 지침이 시작 요약을 출력하도록 요청하지만, 화면에 표시되는 것을 기술적으로 강제하지는 않습니다.

기존 v0.6 프로젝트 업그레이드:
```bash
teamdev upgrade-startup          # 변경 미리보기
teamdev upgrade-startup --apply  # 백업 후 적용, 사용자 편집 정책 충돌 시 차단
teamdev startup
```

Coordinator의 OpenCode `edit` 권한은 `docs/product-specs/**`, `docs/exec-plans/active/**`, `docs/tasks/**` 범위만 허용하도록 변경합니다. Shell의 광범위한 실행 허용은 별도의 위험이며, 정책의 완전한 강제는 아닙니다.

주의: 단계별 스킬은 **발견/설치** 기준으로 표시하며 호출 성공을 뜻하지 않습니다. 네이티브 Worker 실제 실행과 RTK hook/CRG graph 최신성은 별도 확인해야 합니다.

---

# Team AI Dev Framework v0.6.0

OpenCode · Claude Code · Codex 팀 공동 개발을 위한 **Coordinator 중심 실행형** 프레임워크. 특정 개인/프로젝트 전용 워커(`projflow-*` 등)는 포함하지 않습니다.

## 변경 내용

- 일반 요청: Coordinator가 ANALYZE → PLAN을 진행하고 명시적인 사람 승인을 요청하도록 에이전트 지침을 강화했습니다.
- 승인된 TASK: Coordinator가 네이티브 Task/Agent/multi-agent 도구로 implementer → verifier → reviewer를 **실제로 호출**하도록 설정했습니다.
- 네이티브 하위 에이전트 호출이 불가능하면 `teamdev drive --execute`로 각 코딩 에이전트 CLI의 **별도 프로세스를 실제 실행**할 수 있습니다. `handoff.json`만 쓰고 파견했다고 선언하지 않습니다.
- 상태 전이 없이는 다음 Worker로 진행할 수 없습니다. 종료코드 0만으로 PASS를 선언하지 않습니다.
- Worker 컨텍스트 회전 시 `context-handoff.md` 검사 후 이전 프로세스가 종료된 상태에서 새 Worker 프로세스를 시작합니다. 동일 TASK/작업경로를 유지합니다.
- 기존 프로젝트를 위한 `upgrade-routing` 미리보기/명시적 적용 및 백업을 제공합니다.

## 동작 흐름

```text
사용자 요청
  └─ Coordinator (기본 진입, 도구별 차이 있음)
       ├─ ANALYZE / PLAN
       ├─ 사용자 명시적 계획 승인 (멈춤)
       └─ 구현 Worker 실행 ── CONTEXT_HANDOFF_REQUIRED → 재시작(선택)
            └─ 작업 결과 + 실제 증거 등록
                 └─ 독립 검증 Worker 실행 → PASS 등록
                      └─ 독립 리뷰 Worker 실행 → PASS 등록
                           └─ 사용자 최종 승인 (멈춤)
                                └─ COMPLETE
```

## 신규 프로젝트 설치

Python 3.10 이상. `teamdev` CLI는 네이티브 에이전트 CLI를 호출하는 데 사용합니다.

```bash
python -m pip install -e .
mkdir -p ~/demo-project
teamdev --root ~/demo-project init
teamdev --root ~/demo-project doctor
cd ~/demo-project
```

OpenCode는 프로젝트 `opencode.json`의 `default_agent: coordinator`를 사용합니다. **이미 열려 있는 세션은 재시작하거나 에이전트를 전환**해야 할 수 있습니다. Claude Code는 `.claude/settings.json`과 `CLAUDE.md`, Codex는 `AGENTS.md` 및 `.codex/config.toml`에서 Coordinator 규칙을 적용합니다. Codex 기본 메인 에이전트가 별도 이름의 Coordinator로 교체된다는 의미는 아닙니다.

## 기존 v0.2 프로젝트 개선 적용

```bash
python -m pip install -e /path/to/team-ai-dev-framework-v0.3.0
teamdev --root /path/to/project upgrade-routing           # 미리보기
teamdev --root /path/to/project upgrade-routing --apply   # 백업 후 적용
teamdev --root /path/to/project doctor
```

`upgrade-routing --apply`는 프레임워크에 정의된 기본 agent 파일을 업데이트하며 변경 전 내용을 `.ai-dev/backups/`에 저장합니다. 기존 사용자 `AGENTS.md`, `CLAUDE.md`, 워크플로 문서, 외부 스킬을 덮어쓰지 않습니다. **기존 `AGENTS.md`에 v0.3 Coordinator 지침을 별도로 반영**해야 합니다. 기존 `opencode.json`과 `.claude/settings.json`은 기존 키를 유지하면서 기본 agent 키만 변경합니다. 여러 사람이 공유하는 저장소에서는 PR로 검토하고 적용하세요.

## 실제 Worker 자동 순차 실행

일반적인 사용에서는 에이전트에게 **"로그인 기능 구현해줘"**라고 요청하고 계획 승인 후 Coordinator가 네이티브 Task/Agent 도구를 통해 Worker를 파견하도록 지침이 있습니다. **LLM이 스스로 도구를 호출해야 하므로, 호출 여부는 런타임/권한/모델 설정에 좌우됩니다.**

CLI에서 명시적으로 실행하려면:

```bash
teamdev --root . new TASK-001 "로그인 기능 구현"
# docs/product-specs/TASK-001.md 및 docs/exec-plans/active/TASK-001/plan.md 실제 작성
teamdev --root . plan-ready TASK-001 --actor planner
# 사용자가 계획을 검토하고 명시적으로 승인한 경우에만:
teamdev --root . approve TASK-001 --scope plan --actor owner --confirm APPROVE
teamdev --root . next TASK-001
teamdev --root . drive TASK-001 --runtime opencode          # 미리보기, 실행 없음
teamdev --root . drive TASK-001 --runtime opencode --execute
# 또는 --runtime claude / --runtime codex
# 구현/검증/리뷰가 실증 결과를 등록한 경우 AWAIT_FINAL_APPROVAL에서 멈춥니다.
teamdev --root . approve TASK-001 --scope completion --actor owner --confirm APPROVE
```

CLI 실행기는 다음 외부 명령을 `shell=False`로 실행합니다:

- OpenCode: `opencode run --agent implementer|verifier|reviewer <작업지시>`
- Claude Code: `claude --agent implementer|verifier|reviewer --print <작업지시>`
- Codex: `codex exec <작업지시>` (별도 프로세스에 역할 지시만 전달하며 네이티브 named subagent와 다름)

각 실행기는 설치 및 인증되어 있어야 합니다. 프로젝트 루트에서 수행되므로 실행 전 코드/환경/권한을 확인하세요. **이번 환경에서는 실제 모델 CLI에 접속해 작업을 실행하지 않았습니다.**

Worker는 구현 증거를 저장하고 `teamdev report`, `verify`, `review`로 결과를 등록해야 합니다. 상태가 바뀌지 않았으면 실행기가 종료코드 0을 반환했더라도 드라이버가 중단합니다. 검증/리뷰 실패와 승인 범위 변경은 자동 PASS로 승격되지 않으며, 재계획·재승인이 필요합니다.

## 컨텍스트 관리 및 보안 주의

`docs/exec-plans/active/TASK-ID/context-handoff.md`가 회전 인계 정본입니다. 세션은 새 CLI 프로세스로 교체하고 기존 TASK/프로젝트 경로를 유지합니다. `rotate-request` 이벤트는 완료가 아닙니다. `drive`가 직접 호출한 Worker 프로세스가 반환한 후에만 회전을 재개합니다. **실제 Git worktree 생성/잠금과 프로세스 중단 신호, 승인자 신원 인증은 이 패키지가 보장하지 않습니다.** 동시 실행을 방지하려면 작업 격리 정책이 추가로 필요합니다.

내장 검사는 프로세스 결과·기록 파일의 형식 및 체크섬을 검사하며 독립적인 CI 신뢰 경계가 아닙니다. 원본 로그는 `docs/tasks/TASK-ID/evidence/`에 보존합니다. 토큰 압축용 RTK가 원본 증거를 대체해서는 안 됩니다. commit/push는 별도 승인입니다.

## 테스트

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

이 테스트에는 **모의 실행기 기반 3단계 순차 실행/세션 회전 검증**이 포함됩니다. 실제 OpenCode/Claude Code/Codex 연결 및 모델 응답의 종단 간 실증 테스트는 각 팀 환경에서 추가해야 합니다.

---

# v0.4.0 — RTK + Code Review Graph integration

This release builds on v0.3.0 and adds **optional, safe-by-default tooling integration**, not bundled external binaries. OpenCode / Claude Code / Codex retain the v0.3 Coordinator/Worker protocol.

## What's added

| Part | Effect |
|---|---|
| `teamdev tools-status` | Detects RTK and CRG CLI, project graph directory and discovery of the CRG bridge skill; does **not** claim active hooks, MCP connection, or graph freshness |
| `teamdev tools-setup --tool rtk --runtime ...` | Shows exact native `rtk init` command to run, without modifying anything unless `--apply` is specified |
| `teamdev tools-setup --tool crg` | Previews official `code-review-graph install`; `--apply` actually executes installed CLI |
| `teamdev crg-build` | Preview the graph build; `--apply` builds/updates project-local CRG graph |
| `teamdev upgrade-tools` | Safely adds bridge skill/policy/docs to existing projects, appending a controlled AGENTS.md section while preserving custom files |
| `code-graph-analysis` | New included **routing skill** for complex ANALYZE/PLAN/REVIEW; *not the external CRG tool itself* |
| `docs/TOOLS.md`, `.ai-dev/tools.json` | Shared tool policy and explicit instructions for all developers |

## Fresh project installation

```bash
cd team-ai-dev-framework-v0.4.0
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
teamdev --root /path/to/my-project init
teamdev --root /path/to/my-project doctor
teamdev --root /path/to/my-project tools-status
```

## Upgrade an existing v0.3 project (no forced overwrites)

```bash
python -m pip install -e /path/to/team-ai-dev-framework-v0.4.0
teamdev --root /path/to/my-project upgrade-tools           # preview
teamdev --root /path/to/my-project upgrade-tools --apply   # add missing policy/skills and AGENTS note
teamdev --root /path/to/my-project tools-status
```

`upgrade-tools` preserves any existing nonmatching tool files and reports conflicts requiring manual merge. Existing general workflow docs and agent prompts are not overwritten. Restart agents after changing their config.

## Setup RTK on developer's own machine

First install RTK (official source: https://github.com/rtk-ai/rtk) after reviewing edition/license. Then preview each native integration, optionally apply it:

```bash
teamdev --root . tools-setup --tool rtk --runtime opencode
teamdev --root . tools-setup --tool rtk --runtime opencode --apply
teamdev --root . tools-setup --tool rtk --runtime claude --apply
teamdev --root . tools-setup --tool rtk --runtime codex --apply
```

**Warning:** The `--apply` commands above call `rtk init -g` and therefore modify the **current developer's user-global agent settings**. They are never run by project initialization. They may require restart or consent, and the framework does not verify hook activation just because a command succeeded. Run `rtk init --show` and a real agent shell call to check. For license-restricted deployments, use the OSS edition if needed.

## Setup CRG locally when needed

Install official CRG CLI/MCP (https://code-review-graph.com/install) separately in an approved Python environment, then:

```bash
teamdev --root . tools-setup --tool crg               # preview
teamdev --root . tools-setup --tool crg --apply       # native installer; may change local agent config
teamdev --root . crg-build                           # preview
teamdev --root . crg-build --apply                   # build/update project-local graph
teamdev --root . tools-status
```

For large repositories, use the `code-graph-analysis` skill in ANALYZE, PLAN or REVIEW if the graph was built for the current source. If unavailable or stale, fall back to repository search and tests. **A graph directory is not proof of a fresh graph or connected MCP.**

## Operational boundaries

RTK may shorten terminal output, but Worker must still save raw stdout/stderr, full exit codes and test commands as task evidence. There are no silent external downloads, hooks activation, global settings changes, or graph builds on `teamdev init` or `doctor`. v0.4 includes no live test of external RTK/CRG binaries or actual agent MCP connections. See `docs/TOOLS.md` after installation.

---

# v0.5.0 — TASK Activity Monitor

The monitor shows **persisted workflow state** separately from **observed worker activity**. `RUN_VERIFIER` from `teamdev next` is a proposed next action, **not** evidence that a worker is currently running.

```bash
# Update an existing v0.3 / v0.4 project without removing user settings
teamdev --root /path/to/project upgrade-monitor           # preview
teamdev --root /path/to/project upgrade-monitor --apply   # back up and append rules

# One snapshot of all tasks (no agent is launched)
teamdev --root /path/to/project monitor
teamdev --root /path/to/project monitor --json
teamdev --root /path/to/project monitor --task LOGIN-PAGE-001

# Refresh every 3 seconds; Ctrl+C to stop
teamdev --root /path/to/project monitor --watch --interval 3
```

**Activity semantics**

- `IDLE`: previous monitored worker session ended; no currently active recorded worker.
- `UNTRACKED`: no monitored worker session; the TASK may still be running inside OpenCode's native Task UI.
- `RECENT_ACTIVITY`: worker-start / heartbeat was received recently; *not proof that an LLM is currently producing tokens*.
- `STALE`: heartbeat interval exceeded threshold, may be disconnected, blocked, or still running without reporting.
- `PROCESS_EXITED`: a locally recorded coordinator/CLI driver process no longer exists.
- `ERROR`: malformed task status; check workflow files.

**CLI `teamdev drive --execute`** records worker start/heartbeat/end automatically. Its heartbeat is from the *driver process*, and is therefore a sign that a worker invocation is still pending, not a direct health signal from the model. Existing native subagents do not automatically send these events; the Coordinator/agents should record events using the following commands:

```bash
teamdev --root . worker-start LOGIN-PAGE-001 --role verifier --session-id verify-001
teamdev --root . worker-heartbeat LOGIN-PAGE-001 --session-id verify-001
teamdev --root . worker-stop LOGIN-PAGE-001 --session-id verify-001 --status FINISHED
```

A native Worker must only mark `FINISHED` on actual return and must **never** use heartbeat as a substitute for evidence-based `teamdev verify`/`teamdev review`. A Worker that cannot execute the commands remains `UNTRACKED` rather than receiving a fabricated RUNNING label. Use unique session IDs for retries and rotation. A session replacement must close the old activity record before starting the new one.

Local TASK activity is stored in `docs/tasks/<TASK-ID>/activity.json`, with the last 100 ended sessions in the history. It contains role, session ID, time, event source and, for the CLI driver, local PID/host. It does not capture prompts, passwords, or raw logs. Running work in other worktrees or on different machines requires extra coordination; this monitor is **not** a distributed scheduler or trusted heartbeat service. `--watch` polls local filesystem and does not communicate with OpenCode itself.

---

# v0.6.0 — 완료 계획 아카이브 + 세션 요약 + OpenCode shell 권한

## 달라진 점

- 최종 사용자가 실제로 완료를 승인한 뒤 `teamdev approve TASK --scope completion ...`를 호출하면 `docs/exec-plans/active/TASK/` **전체**가 `docs/exec-plans/completed/TASK/`로 이동됩니다. 상태·승인·검증·리뷰 자료는 `docs/tasks/TASK/`에 그대로 보존합니다.
- 완료 시 로컬 파일 잠금을 사용하며, 아카이브 충돌이나 상태 저장 오류가 나면 완료 처리하지 않습니다. 같은 파일 시스템에서 이동하고, 상태 기록 오류 시 원래 위치로 되돌립니다. 분산 파일 시스템/프로세스 강제 종료까지 원자적이라고 보장하지 않습니다.
- `teamdev session-summary`는 신규 세션에서 진행·승인 대기·완료 작업과 다음 행동, 기록된 Worker 활동을 요약합니다. 서브에이전트의 미계측 실행은 RUNNING으로 추정하지 않습니다.
- `teamdev archive-completed TASK`로 v0.5에서 이미 COMPLETED인데 active에 남아 있던 작업의 이전을 미리 확인하고 `--apply`로 정리할 수 있습니다.
- 새 프로젝트의 `opencode.json`과 Coordinator 에이전트에는 일반적인 shell 명령 자동 허용 규칙이 들어갑니다. `git commit`, `git push`는 별도 확인하고 `git reset --hard`는 차단하는 명령 패턴을 포함합니다. **광범위 shell 허용에는 임의 명령 실행 위험이 있습니다. 이 규칙은 보안 샌드박스가 아니며, 우회 가능한 셸 스크립트나 다른 명령 형태까지 확실히 통제하지 않습니다.** 계획 승인/최종 완료 승인/commit·push의 사용자 승인 원칙은 별개입니다.
- `upgrade-permissions`는 **OpenCode V1의 `permission` / `bash` 설정**을 대상으로 합니다. 새로운 OpenCode V2 `permissions` / `shell` 설정에서는 자동 병합을 거부하고 수동 검토를 요구합니다.

## 기존 프로젝트 v0.5 → v0.6

```bash
# 다운로드한 프레임워크 v0.6.0 디렉터리에서
python3 -m pip install -e .

# 실제 개발 프로젝트 루트에서
teamdev upgrade-lifecycle                 # 미리보기
teamdev upgrade-lifecycle --apply         # 지침 반영, 수정되는 기존 파일은 백업
teamdev upgrade-permissions               # OpenCode shell 권한 변경 미리보기
teamdev upgrade-permissions --apply       # 명시적 허용 적용, 백업
teamdev session-summary                   # 진행/완료/차단 작업 확인
teamdev doctor
```

이미 v0.5에서 최종 승인 완료했지만 계획이 `active/`에 있는 경우:

```bash
teamdev archive-completed TASK-001
teamdev archive-completed TASK-001 --apply
```

최종 승인은 **사용자가 실제로 승인한 뒤에만** 기록합니다.

```bash
teamdev approve TASK-002 --scope completion --actor owner --confirm APPROVE
teamdev session-summary
```

**주의:** 새 프레임워크를 내려받아 설치하는 것만으로 사용자의 로컬 프로젝트에 권한이 변경되지는 않습니다. 해당 프로젝트의 `upgrade-permissions --apply` 실행이 필요합니다. 기존 사용자 지정 bash 권한이 있으면 자동 덮어쓰지 않고 충돌을 보고합니다. 기존 OpenCode 세션은 설정을 재로드하도록 재시작하는 것이 좋습니다.

## 검증

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -q
```

테스트는 모의 상태 기록과 파일 시스템의 아카이브·권한 설정을 대상으로 합니다. 로컬 OpenCode/Claude Code/Codex의 실제 대화, 관리자 권한, 에이전트 도구 실행은 실환경에서 별도 검증해야 합니다.

---

## v0.8.0 — 통합 점검 / 스킬·Worker 증거 구분

이번 릴리스는 실행 구조를 새로 약속하는 대신 기존 v0.7.0의 **설정과 실제 검증 범위 사이의 차이**를 점검할 수 있도록 변경했습니다. `docs/RUNTIME-AUDIT.md` 참조.

### 새 프로젝트

```bash
python3 -m pip install ./team_ai_dev_framework-0.8.0-py3-none-any.whl
mkdir -p my-project && cd my-project
teamdev init
teamdev startup
teamdev audit
teamdev audit --strict
teamdev launch opencode
```

### v0.7.0 사용 중인 프로젝트

```bash
# 업데이트한 패키지에서 팀 공통 CLI를 업데이트한 뒤 기존 프로젝트에서:
teamdev upgrade-audit          # 변경 미리보기
teamdev upgrade-audit --apply  # AGENTS.md / Coordinator 지침에 섹션 추가, 기존 파일 백업
teamdev audit                  # 읽기 전용 점검
teamdev audit --strict         # 설정 누락은 exit 2
teamdev startup
```

기존 사용자 정의 에이전트 설정과 권한을 덮어쓰지 않습니다. 이번 업그레이드는 `docs/RUNTIME-AUDIT.md`와 지침을 추가하며, 프로젝트에 이미 배포된 기존 스킬 파일을 자동 교체하지 않습니다. 신규 프로젝트는 정확한 6개 번들 스킬 목록을 사용합니다.

### 스킬 실제 사용 기록(선택)

에이전트가 네이티브 스킬 도구를 호출하고 그 호출 기록을 TASK의 `evidence/`에 저장한 경우에만 다음 명령을 실행합니다.

```bash
teamdev skill-record TASK-001 --skill code-graph-analysis --role coordinator --session-id session-01 --evidence skill-call.log
teamdev skill-events TASK-001
```

**주의:** 이는 Agent가 제출한 호출 기록·해시입니다. 로컬 CLI만으로 네이티브 모델의 스킬 로드를 독립 증명하지는 못합니다. 로그에 비밀정보를 기록하지 마세요.

### 진단 상태 의미

| 진단 값 | 뜻 |
|---|---|
| PASS | 로컬 설정 파일과 에이전트 진입 구성이 기대 형태임 |
| CONFIG_ONLY | 역할별 설정 파일만 확인됨 |
| NOT_VERIFIED | 실제 스킬 로드, Worker 파견, hook 사용을 검증하지 못함 |
| ERROR | 누락된 파일이나 일관성 오류 (strict 모드 실패) |

`teamdev audit`는 CRG graph.db 유무, RTK 실행 파일과 훅 검증의 차이, 작업 상태 불일치, 세 도구별 스킬 발견 경로를 확인합니다. 모델 기반 E2E, 전역 훅 활성화, 원격 서비스의 상태를 실제로 검증했다고 주장하지 않습니다.

### 실환경 수락 테스트(수동)

1. OpenCode / Claude Code / Codex를 각각 실행해 기본 Coordinator 진입을 확인
2. `teamdev new` → Spec/Plan 생성 후 승인 전 Worker 파견이 차단되는지 확인
3. 명시적 인간 계획 승인 이후 Implementer 네이티브 호출·완료 반환 확인
4. 별도 Verifier / Reviewer 호출과 원본 테스트 로그 존재 확인
5. 인간 최종 승인 후 `active/` → `completed/` 이동 확인
6. Worker 회전 시 종료→인계 검증→새 세션 재개 확인
7. RTK 훅과 CRG 그래프 최신성을 각 코딩 에이전트에서 직접 확인

프로젝트 설정 파일만 읽고 위 작업을 실제로 실행하지 않았다면 해당 항목은 **미검증**입니다.


## v0.9.0 — 작업 유형별 TDD 강제

신규 `teamdev new TASK-001 "제목" --type feature`는 기본적으로 TDD 필수로 시작합니다. 유형 변경은 계획 승인 준비 전에 `teamdev tdd-set TASK-001 --type ui_visual --actor coordinator`로 수행합니다. PLAN 승인 시 정책이 고정되며, 구현 보고·독립 검증·최종 완료 단계에서 TDD 매니페스트 및 원본 로그를 검사합니다.

유형별 적용: feature/bugfix/behavior_change/api/business_logic → RED/GREEN/REFACTOR, ui_visual/configuration/refactoring → 지정된 대체 검증, documentation → 문서 검증. 자세한 계약은 `docs/TDD-POLICY.md`.

`teamdev tdd-check TASK-001`로 증거를 검사합니다. 과거 TASK는 자동으로 재분류하지 않습니다. 기존 프로젝트의 템플릿 변경은 아래 `upgrade-tdd` 명령으로 확인 후 적용합니다.


## v0.13.0 — Empty-project safe CRG auto

CRG is optional, used only for meaningful cross-file analysis, not before every request.

```bash
teamdev crg-auto              # read-only status/next action
teamdev crg-auto --apply      # run graph build only if sources exist and graph is missing/stale
teamdev upgrade-crg-auto      # existing-project preview
teamdev upgrade-crg-auto --apply
```

`SKIP_EMPTY` (no code) and `FALLBACK_NO_CRG` (CLI missing) do not block development. `READY_CANDIDATE` is only a timestamp-based indication, not proof of graph quality. For full CRG usage, verify the graph and queries in the runtime.

**External recommended skills:** They are a catalogue, not installed by the framework. An agent can select and load only discoverable installed skills applicable to the task. They are not executed automatically and cannot substitute for mandatory TDD evidence or verification.


## v0.13.0 — 시작 작업 대시보드와 단계별 스킬 사용 이력

```bash
teamdev session-summary                 # 진행/완료/승인대기/차단 + TASK/상태/사용자 조치
teamdev session-summary --json
teamdev startup                         # 실행 구조 + 대시보드 + 스킬 이력
teamdev skill-history                   # 전체 TASK 단계별 스킬 사용 기록
teamdev skill-history --task TASK-001
teamdev skill-record TASK-001 --skill tdd-workflow --role implementer --session-id worker-01 --evidence logs/skill-call.log
teamdev upgrade-visibility              # 기존 프로젝트 변경 미리보기
teamdev upgrade-visibility --apply      # 비파괴 지침 추가
```

스킬 이벤트는 실제 호출 후 근거를 남길 때만 기록합니다. 단순 설치나 프롬프트 내 스킬 언급은 실행을 증명하지 않습니다.

새 세션의 사용자 조치는 승인 대기, 오류 복구, Worker 소유권 확인 등 작업 상태에 맞춰 표시합니다. 정본은 `docs/tasks`와 `docs/exec-plans`입니다.


## v0.13.0 공통 스킬 배포

프로젝트당 동일한 스킬 20종을 OpenCode·Claude Code·Codex에 설치합니다. 잠금 파일은 SHA-256으로 파일 동일성을 검사하며, 기존 7개 외 13개는 upstream 외부 원본이 아닌 프레임워크 자체 작성 동등 역할 스킬입니다. 자세한 내용은 `docs/COMMON-SKILLS.md`.

```sh
teamdev upgrade-skills            # 기존 프로젝트 미리보기
teamdev upgrade-skills --apply    # 설치/정책 백업
teamdev skills-status --strict    # 3 런타임 일치 검사
teamdev skills-sync --apply       # 누락된 런타임 복사본 복구
teamdev audit --strict            # 종합 점검
```

설치는 통일, 로드는 업무 유형에 따라 조건부입니다. 실제 호출 증거는 별도 `skill-history`를 확인하세요.

## Orca Coordinator 세션 인계·복구 (v0.16)

긴 작업에서 메인 Coordinator의 컨텍스트가 누적될 때, **기존 TASK·승인·worktree는 보존**하고 Orca에서 새 **메인 Coordinator 대화 세션**으로 이어서 작업하는 절차입니다. 기존 세션의 컨텍스트 사용률은 추정하지 않으며, 실제 Orca 세션 생성·종료를 자동 수행하지 않습니다.

Worker 호출이 실제로 반환되고 `teamdev monitor`에서 RUNNING 기록이 없는 안전한 단계 경계에서:

```bash
teamdev coordinator-handoff TASK-001 \
  --session-id orca-main-01 \
  --next-action "검증 Worker 호출" \
  --reason "단계 경계 및 컨텍스트 누적"
teamdev coordinator-session TASK-001
```

Orca에서 **동일 프로젝트/worktree**를 사용하는 **새 메인 Coordinator 대화**를 시작하고 이전 대화의 작업 진행을 중단합니다. 새 대화에서:

```bash
teamdev coordinator-resume TASK-001 \
  --new-session-id orca-main-02 \
  --old-session-stopped
teamdev startup
teamdev status TASK-001
teamdev next TASK-001
teamdev progress --task TASK-001
```

`--old-session-stopped`는 이전 세션의 종료·비활성화를 사용자가 확인했다고 **선언**하는 플래그이며 런타임 종료 자체를 검증하지 않습니다. `PREPARED` 중에는 `teamdev next`, CLI Worker 파견 및 주요 상태 변경을 차단합니다. 다른 세션이나 프로그램이 파일을 직접 수정하는 행위까지 막는 전역 잠금은 아닙니다. 인계 기록과 승인 정보는 `docs/tasks/TASK-ID/`에 유지됩니다. 사용 지침은 `docs/COORDINATOR-RECOVERY.md`에 있습니다.

기존 프로젝트에는 아래를 적용합니다.

```bash
teamdev upgrade-coordinator-recovery
teamdev upgrade-coordinator-recovery --apply
```


## v0.18.2 — OpenCode 기본 설정

신규 프로젝트의 `opencode.json`에는 `default_agent=coordinator`, `permission.read/edit/task/skill=allow`,
`permission.bash`의 commit/push 확인 및 위험 명령 제한, `external_directory=allow`, `doom_loop=ask`, `lsp=true`를 사용합니다.
사용자가 기존에 정의한 프로바이더, 플러그인 등은 보존하면서 프로젝트 설정만 병합하려면:

```bash
teamdev --root . upgrade-opencode-config           # 변경사항 미리보기
teamdev --root . upgrade-opencode-config --apply   # 백업 후 적용
```

기존 프로젝트의 `opencode.json`을 `teamdev init --force`로 덮어쓰지 마세요.
`~/.config/opencode/opencode.json`은 이 명령의 변경 대상이 아닙니다.
전역 권한이 allow여도 에이전트별 frontmatter에서 deny/ask가 지정되어 있으면 제한될 수 있습니다.
이 권한 설정은 실제 위험 명령 실행을 폭넓게 허용하므로 신뢰된 로컬 환경에서만 사용하십시오.

## 자가개선 승인 게이트 (v0.18.2)

```bash
teamdev improve-propose IMPROVE-001 "AGENTS 정본 개선" --problem "반복 오류 관측 내용과 재현 근거"
# Spec/Plan 작성 → teamdev plan-ready → 사용자 plan 승인 → 격리 구현/검증/리뷰
teamdev improve-stage IMPROVE-001 --target AGENTS.md --file /tmp/proposed-AGENTS.md
# 검증/리뷰 완료 및 사용자 최종 승인 후:
teamdev improve-check IMPROVE-001
teamdev improve-apply IMPROVE-001               # 미리보기
teamdev improve-apply IMPROVE-001 --actor USER --confirm APPLY --apply
```

기존 프로젝트에는 `teamdev upgrade-self-improvement`로 미리보기한 뒤 `--apply` 옵션으로 신규 정책 문서 및 AGENTS 지침을 추가합니다. 실제 정본 변경은 별도 승인 게이트를 거칩니다.

## Worker report JSON contract (v0.19.1)

The `teamdev report --file` command accepts JSON, **not** Markdown. The CLI's final
`docs/tasks/TASK-ID/worker-report.json` is output, not input. Use an independent
`implementer-input.json` for the Worker-provided values.

```bash
teamdev --root . report-template TASK-ID --worker implementer --output docs/tasks/TASK-ID/implementer-input.json
# Complete changed_files and evidence with actual results and logs in evidence/.
teamdev --root . report-check TASK-ID --file docs/tasks/TASK-ID/implementer-input.json
teamdev --root . report TASK-ID --actor implementer --file docs/tasks/TASK-ID/implementer-input.json
teamdev --root . next TASK-ID
```

The template intentionally has **no evidence** and cannot pass verification until the
Worker provides real results. `report-check` checks the JSON fields and existing
evidence without transitioning the task. `report` retains TDD requirements and only
advances IMPLEMENT → VERIFY on success. Existing Team AI Dev projects may preview
`teamdev --root . upgrade-report-contract` and explicitly apply with `--apply`;
existing custom content is preserved and appended text is backed up.

This package is a local build candidate; npm Registry publication and real model-based
OpenCode/Claude/Codex end-to-end operation are not verified by the local tests.
