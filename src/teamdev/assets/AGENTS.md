# Team AI Development — 공통 진입점

이 저장소는 여러 팀원이 OpenCode·Codex·Claude Code 중 어느 것을 사용하든 동일한 정본 문서와 승인·검증 원칙을 공유합니다.

1. 시작 시 `.ai-dev/policy.json`, `.ai-dev/skills.json`, `docs/`의 관련 Spec/Plan, 현재 작업 상태를 확인합니다.
2. 요청 내용을 ANALYZE → PLAN → IMPLEMENT → VERIFY → REVIEW → COMPLETE 단계로 관리합니다.
3. `docs/product-specs/<TASK>.md`는 요구사항 정본, `docs/exec-plans/active/<TASK>/plan.md`는 계획 정본입니다.
4. 구현 전 사용자(권한 있는 담당자)의 **명시적인 계획 승인**을 확인합니다. CLI 기록만으로 신원이 검증되지는 않습니다.
5. 승인된 파일 범위를 벗어나면 중단하고 변경 승인을 다시 받습니다. 승인 없는 commit/push/merge 금지.
6. 구현자는 테스트를 수행하고 원본 로그와 실행 명령/종료코드를 남깁니다. 독립 검증자와 리뷰어의 실제 검토가 필요합니다.
7. 검증 성공을 추측하지 않습니다. 증거 없는 PASS, 셀프 리뷰, 완료 선언을 금지합니다.
8. 비밀정보를 출력·로그·커밋하지 않습니다. 외부 메모리/MCP는 기본 비활성화합니다.
9. 적절한 스킬만 지연 로드합니다. 스킬 설치 여부와 실제 실행 여부를 구분하여 보고합니다.
10. 작업 간 의존성과 동일 파일 변경 위험을 검토한 후에만 병렬 실행합니다.

자세한 절차: `docs/WORKFLOW.md`. 기본 권한 모델: `.ai-dev/policy.json`.

## Coordinator 기본 적용
OpenCode는 `opencode.json`의 기본 primary `coordinator`, Claude Code는 `.claude/settings.json`의 `agent`로 Coordinator를 선택합니다. Codex는 본 AGENTS.md를 읽는 메인 세션에서 **Coordinator 역할**을 수행합니다(별도 기본 agent 자동 선택과 다름).
Coordinator는 분석/계획/승인/파견/증거 확인만 수행하며 **구현 소스 직접 수정 금지**. 구현·검증·리뷰는 가능한 경우 분리된 작업자에게 위임합니다. 실제 하위 에이전트 호출 기능은 런타임마다 다릅니다.

## 장기 Worker 세션 회전
`docs/SESSION-ROTATION.md` 준수. 작업 ID·worktree·승인은 유지하고 모델 대화 세션만 바꿉니다. `CONTEXT_HANDOFF_REQUIRED`는 작업 완료가 아니며, 유효한 인계와 이전 세션 종료 확인 없이 새 세션을 시작하지 않습니다. 세션이 교체되어도 작업 기록과 원본 검증 증거가 우선합니다.


## v0.3.0 실제 파견 규칙
작업 요청을 받으면 Coordinator가 주도한다. Spec/Plan 및 승인 기록을 만든 다음 `teamdev --root . next TASK-ID`로 다음 단계를 결정한다. **명시적 계획 승인 후에만** 구현을 파견한다. OpenCode에서는 네이티브 Task 서브에이전트, Claude Code에서는 Agent 서브에이전트를 사용한다. Codex는 지원되는 multi-agent `spawn_agent`/wait 기능과 `.codex/config.toml` 역할 설정이 있으면 별도 구현·검증·리뷰 워커로 파견한다. 해당 기능이 없는 실행 환경에서는 `teamdev --root . drive TASK-ID --runtime codex --execute`를 사용해 CLI 프로세스를 별도로 호출할 수 있다. 이 CLI 경로는 Codex named subagent 호출이 아니라 역할 지시를 포함한 별도의 `codex exec` 실행이다. 실제 호출이 실패하면 멈추고 보고한다. 파일 생성만으로 파견·검증 완료를 선언하지 않는다. `CONTEXT_HANDOFF_REQUIRED` 시 이전 Worker 프로세스/호출 종료 후 회전한다. 마지막은 사용자 승인 후 COMPLETE.

## Optional CLI/code-graph tools (v0.4)
Read `docs/TOOLS.md` and `.ai-dev/tools.json`. Use RTK for shell output only if its hook is actually active in this agent or explicitly invoke supported `rtk` CLI commands. Never replace raw verification evidence with compressed output. For complex impact analysis or REVIEW, consult the `code-graph-analysis` skill and use CRG only if installed and its graph is confirmed current; otherwise use native code search. `teamdev tools-status` is discovery, not proof of actual execution. User-global RTK hooks / CRG MCP settings require explicit local opt-in.

## Worker Activity Monitoring (v0.5)

- When a native subagent is **actually** launched, record `teamdev worker-start TASK --role ROLE --session-id UNIQUE`; record heartbeats only after genuine activity and stop when actual return is observed.
- Use `teamdev monitor --watch` to inspect TASK state separately from Worker activity. `RECENT_ACTIVITY` is not evidence of completed tests or verified LLM progress.
- If telemetry commands are unavailable, leave activity `UNTRACKED`; never fake RUNNING.
- Full instructions: `docs/MONITOR.md` / `worker-activity-monitor` skill.


## Session Start and Plan Archive (v0.6)
- 새 세션 시작 시 `teamdev --root . session-summary`를 호출하여 진행 중/완료/차단 TASK와 다음 행동을 확인한다.
- 기존 작업에 활성 Worker 기록이 있으면 소유권과 실행 상태를 확인하기 전 재개하지 않는다.
- `teamdev new TASK-ID "제목"`를 문서 작성보다 먼저 실행한다.
- 최종 사람 승인에만 `teamdev approve TASK-ID --scope completion --actor <approver> --confirm APPROVE`를 실행한다. 이 명령은 실행 계획 폴더 전체를 active에서 completed로 옮긴다.
- 완료 처리는 사용자 승인 증거가 확보된 경우에만 실행하고, commit/push는 별도 승인이다.

## Startup Dashboard (v0.7)
- 첫 응답 전에 `teamdev --root . startup`을 실제 실행하고 실행 구조, 각 단계의 설치된 스킬, 진행 중/완료 TASK를 짧게 사용자에게 보여준다.
- 시작 명령 실행 실패 시 이유를 명시하고 성공한 척하지 않는다.
- 새 세션에서는 실행 중 Worker의 소유권 확인 없이 재개하지 않는다.
- `teamdev launch opencode|claude|codex`는 에이전트 시작 전 로컬 터미널에 확정적으로 안내를 출력한다. 일반 네이티브 실행은 에이전트 지침 적용 여부에 의존한다.
- 자동으로 모든 스킬을 호출하지 않는다. 역할/작업에 필요한 스킬만 로드하고 실제 사용 증거와 설치를 구분한다.

## Runtime Audit and Skill Evidence (v0.8)
- 새 세션 시작 시 `teamdev --root . startup`과 필요 시 `teamdev --root . audit` 실행. 설정/스킬 파일/추천 스킬을 구분해 출력한다.
- `teamdev audit --strict`는 설정 누락 시 실패한다. 그러나 실제 LLM Worker 파견이나 스킬 로드의 E2E 증거를 대체하지 않는다.
- Worker가 네이티브 스킬을 호출한 근거를 원본 파일로 저장한 경우에 한해 `teamdev skill-record TASK --skill NAME --role ROLE --session-id SESSION --evidence FILE` 사용. 단, 이 기록은 에이전트 신고이며 독립 검증된 자동 후킹 기록이 아니다.
- 네이티브 도구 호출 증거가 없으면 `NOT_VERIFIED` 그대로 보고하고 추측하지 않는다.
- 외부 스킬은 실제 파일이 확인되어도 자동 로드된 것으로 간주하지 않는다. RTK 훅과 CRG graph.db 최신성도 각각 검증 전 상태를 유지한다.
- 작업 시작 전 `teamdev new` 실행. 계획 승인 전 소스 구현 금지. 승인 후 실제 native task 호출 및 반환 증거를 확보한다.
- 일반 shell 권한 허용과 사용자 계획/완료 승인은 별개의 정책이다. 도구 권한 설정을 승인 증거로 사용하지 않는다.


TDD policy (v0.9): Create tasks with `teamdev new TASK-ID "title" --type feature|bugfix|behavior_change|api|business_logic|ui_visual|configuration|refactoring|documentation`. Classify during ANALYZE. Use `teamdev tdd-set TASK-ID --type TYPE --actor coordinator` before plan-ready to correct classification. Required types demand evidence/tdd-manifest.json with RED/GREEN/REFACTOR logs. UI/config/refactoring require alternative verification logs; docs require validation logs. `teamdev tdd-check TASK-ID` before verifier PASS. Do not fabricate evidence. Legacy tasks without tdd field remain on legacy workflow until explicitly migrated.

## Lifecycle integrity (v0.10)

- 새 세션 시작 시 `teamdev --root . session-summary`와 `teamdev --root . lifecycle-check --strict`로 진행/완료 TASK와 정본 무결성을 확인한다.
- `docs/product-specs/TASK-ID.md`와 `docs/tasks/TASK-ID/`(상태·승인·evidence 포함)는 완료 후에도 고정 경로에 둔다.
- 최종 승인 시 `docs/exec-plans/active/TASK-ID/` 폴더 전체만 `docs/exec-plans/completed/TASK-ID/`로 이동한다.
- 완료 판정은 `state.json`의 COMPLETED, 사용자 최종 승인, Plan 위치, 승인 당시 Spec/Plan SHA-256이 모두 일치할 때만 가능하다.
- 중복 Plan/Spec 또는 state 누락, 해시 불일치 시 임의 파일 이동·상태 변경 없이 BLOCKED로 보고한다.
- 과거 COMPLETED 상태인데 Plan이 active에 남아 있으면 `teamdev archive-completed TASK-ID`를 먼저 미리보고 승인 후 `--apply`한다.

## CRG On-Demand Lifecycle (v0.11)
CRG는 코딩 에이전트가 ANALYZE/REVIEW에서 크로스파일 분석이 필요한 경우에만 판단합니다. 빈 프로젝트는 SKIP_EMPTY로 정상 진행합니다. 소스가 생긴 후 `teamdev crg-auto`로 미리 판별하고 BUILD/REBUILD이면 `teamdev crg-auto --apply`를 호출합니다. CRG 미설치/실패 시 소스코드 직접 검색으로 대체하며 검증 PASS를 주장하지 않습니다. READY_CANDIDATE는 파일 수정시각만 본 것으로 그래프 최신성을 보장하지 않습니다.
외부 추천 스킬은 자동 로드되지 않습니다. 실제 설치·발견된 스킬 중 작업 유형에 맞는 것을 에이전트가 선택해 로드합니다. 미설치라면 사용할 수 없습니다. 정책·승인·검증을 외부 스킬 부재 때문에 생략하지 않습니다.

## Startup Dashboard and Skill Usage Ledger (v0.12)
- 첫 세션 시작에는 `teamdev startup`과 `teamdev session-summary`를 실행하여 TASK/상태/사용자 조치를 표시한다.
- `teamdev skill-history`로 단계별 스킬 이력을 확인한다. 기록 없음은 미사용의 증거가 아니다.
- 스킬을 실제 호출한 뒤, TASK evidence/ 아래에 호출 근거를 기록하고 `teamdev skill-record TASK --skill NAME --role ROLE --session-id ID --evidence FILE` 실행한다.
- 사용 기록은 에이전트 선언이므로 실제 런타임 로드의 독립 증명이 아니다. 증거 없는 사용 성공 주장을 금지한다.
- 활성 Worker가 있다면 소유권을 확인하기 전 재개하지 않는다.

## Common Locked Skills (v0.13)
- On startup, run `teamdev skills-status --strict`. All 20 project skills are installed consistently for OpenCode/Claude/Codex; a missing or changed skill is a hard environment error. Do not dispatch workers until repaired with `teamdev skills-sync --apply`, and do not bypass explicit human approvals.
- `docs/COMMON-SKILLS.md` and `.ai-dev/skills.lock.json` are authoritative for local skill file integrity. Use stage/type-specific skills on demand. Never claim that SKILL.md presence proves model loading.
- The 13 added role-equivalent skills are originally authored in this framework, NOT genuine upstream external vendor skills. Do not claim upstream identity or matching semantics.

## Coordinator Progress Reporting (v0.14)

- Run `teamdev progress --task TASK-ID` at meaningful transitions: after PLAN is ready (before requesting approval), after confirmed Worker dispatch, after Worker return, after VERIFY/REVIEW result recording, before final user approval, and after COMPLETE archive. Also show `teamdev progress` at SESSION start when tasks exist.
- Present a concise human-readable status: TASK, stage, workflow status, Worker / observed activity, stage pipeline, user action, and next execution. Report FAIL / BLOCKED immediately.
- Show actual monitored facts, not fabricated progress percentages. `RECENT_ACTIVITY` from heartbeat is not proof of a live native Worker or of successful verification. Never call `worker-start` before confirmed dispatch or `worker-stop` before confirmed return.
- Do not poll `teamdev monitor` inside a synchronous native Task call. During long runs the human may use a separate terminal: `teamdev monitor --watch --interval 3`. Only report genuine new progress on real events, not repetitive messages.
- Preserve both explicit human approval gates. Progress display must never auto-approve, advance workflow, or overwrite TASK evidence.
- Detailed usage: `docs/PROGRESS.md`. `teamdev progress --json` is read-only and machine-readable.

## Orca Coordinator Session Recovery (v0.16)

- Keep TASK, worktree, approvals and evidence stable. Only the **main Coordinator model conversation** changes; do not spawn another Coordinator as a subagent.
- At a safe stage boundary (or when context pressure is detected), ensure any native Worker call has actually returned and its monitoring record is stopped. Then use `teamdev coordinator-handoff TASK --session-id CURRENT --next-action "one next action" --reason "context pressure"`.
- This command freezes `teamdev next`, native Worker registration and CLI Worker execution for that TASK while PREPARED. The freeze is enforced by cooperating `teamdev` commands, not by Orca or direct file writes.
- In Orca, open a **fresh main Coordinator conversation** in the same project/worktree. Do not resume the old context or have both conversations advance the same TASK.
- After confirming the old Coordinator is inactive, from the NEW session call `teamdev coordinator-resume TASK --new-session-id NEW --old-session-stopped`. The flag is an operator/agent assertion, **not** an independent process-liveness check.
- Read the short `docs/tasks/TASK/coordinator-handoff.md`, run `teamdev startup`, `teamdev status TASK`, `teamdev next TASK` and verify approvals and Worker ownership before dispatch.
- No fictional token percentage: checkpoint at real phase boundaries or contextual pressure. No automatic Orca window creation/clearing is claimed. `teamdev coordinator-session TASK` shows PREPARED/RESUMED state.
- Handoffs preserve original logs externally; never paste secrets, transcript dumps or raw logs into the handoff file. Do not commit or push without separate user approval.

## Native Worker Dispatch and Monitoring (v0.17)

- PLAN: after writing Spec/Plan, run `teamdev plan-ready TASK --actor coordinator` **BEFORE** asking for human plan approval. Never request approval from ANALYZE/DRAFT.
- Record only actual human approval with `teamdev approve TASK --scope plan --actor user --confirm APPROVE`.
- For IMPLEMENT, VERIFY and REVIEW use `teamdev worker-prepare TASK --role implementer|verifier|reviewer` **sequentially** before any native Task/Agent call. IMPLEMENT `APPROVED` is dispatched exactly once by this command. No native Worker is started by `worker-prepare`.
- Run `teamdev monitor --task TASK` and `teamdev progress --task TASK` after preparation; UNTRACKED at this point means **not yet observed**, NOT a runtime failure or RUNNING proof.
- Call the native Task/Agent for that role. Do not run `worker-start` in parallel with native Task. A synchronous native call blocks the Coordinator, so it cannot poll from inside the call. Use `monitor --watch` in another terminal for truly asynchronous telemetry.
- After the native call actually returns, record `teamdev worker-return TASK --role ROLE --session-id UNIQUE --status FINISHED|FAILED|STOPPED` and then call `teamdev monitor --task TASK` and `teamdev progress --task TASK`. This is Coordinator-reported observation, not an independently captured runtime event or workflow PASS.
- Runtime hook-driven/asynchronous calls MAY use `worker-start` only after a genuine launch and `worker-stop` on actual return. Do not use `worker-return` for a session already tracked with `worker-start`/`worker-stop`.
- Verify real `teamdev report` / `verify` / `review` transitions and the underlying evidence before moving to the next role. Never fabricate PASS, re-dispatch an already launched task, or advance on monitoring status alone.
- On a state conflict, stop and inspect `teamdev status TASK`, `teamdev next TASK`, and `teamdev monitor --task TASK`. Do not workaround with ad-hoc state.json edits.

## Design Documents and References (v0.18)

- `docs/design-docs/`는 제품/서비스의 **현재 승인된 설계**(아키텍처, API, DB, UI/UX, 보안, 운영)를 관리한다. 기존 `docs/architecture/`와 `docs/decisions/`는 유지하며 ADR은 결정 기록의 정본이다.
- `docs/references/`는 기존 시스템 분석, 외부 기술 문서, 조사 결과 등 **근거/참고 자료**를 관리한다. 참고 자료는 승인된 요구사항이나 설계 정본을 자동으로 대체하지 않는다.
- ANALYZE: 작업에 직접 관련된 설계/참고 문서만 찾고 문서별 **경로, 적용 범위, 확인한 사실/가정, 충돌**을 Spec에 기록한다. 없는 자료는 없다고 명시한다.
- PLAN: Spec의 AC와 설계 계약을 연결하고 영향을 받는 설계문서와 필요한 검증을 Plan에 기록한다. 문서 충돌이나 미결정 사항은 사용자 승인 전 보고한다.
- IMPLEMENT/VERIFY/REVIEW: 승인된 Plan이 가리키는 문서만 우선 읽고, 추가 자료가 필요하면 범위·승인 조건을 확인한다. 검증은 AC와 실행 증거 기준이며 참고문서 읽기를 검증 완료로 간주하지 않는다.
- COMPLETE: 실제 구현으로 바뀐 설계 사항의 정본 갱신 여부를 확인한다. 설계 변경도 승인된 범위를 넘어 자동 수정하지 않는다.
- 모든 작업에 `design-docs`/`references` 문서 작성을 강제하지 않는다. 전체 폴더의 무차별 읽기, 대용량 자료의 매 턴 로딩, 외부 링크의 무검증 사실화 금지. 자세한 규칙은 `docs/DOCUMENT-SOURCES.md` 참고.

## Self-Improvement Approval Gate (v0.18.2)

- AI may **propose** improvements, but may not directly activate edits to AGENTS.md, framework policy, skill contracts or tooling config. Use `teamdev improve-propose TASK "title" --problem "evidence..."` for an ANALYZE candidate.
- Follow **ANALYZE → PLAN → explicit human plan approval → isolated IMPLEMENT → independent VERIFY → REVIEW → explicit human final approval → improve-apply → COMPLETE (activation recorded)**. The existing workflow records COMPLETE before the separate promotion command; treat this as *approved task closure*, not policy activation.
- Keep proposed edits staged with `teamdev improve-stage`; after `teamdev approve --scope completion` and independent evidence, check `teamdev improve-check` and preview `teamdev improve-apply`; only apply on an explicit human action using `--confirm APPLY --apply`. No self-approval or policy self-edit.
- See `docs/SELF-IMPROVEMENT.md` for the authoritative gate, limits, and rollback. Do not repeat every procedure in AGENTS.md.
