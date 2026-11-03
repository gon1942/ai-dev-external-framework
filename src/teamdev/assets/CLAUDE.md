# Claude Code 기본 진입점

본 프로젝트의 기본 agent는 `.claude/settings.json`의 `coordinator`입니다.
`AGENTS.md` 및 `docs/WORKFLOW.md`가 공통 정책의 정본입니다.
현재 작업 상태를 확인하고, 미승인 구현을 수행하지 마세요.
Worker 작업과 세션 회전은 `docs/SESSION-ROTATION.md`와 `teamdev rotate-*` 계약을 따릅니다.
기존 설정이 존재하면 설치기가 덮어쓰지 않으므로 `teamdev doctor`로 확인하세요.

After explicit plan approval, use native Agent tool implementer -> verifier -> reviewer, recording each state via teamdev. Do not stop at handoff.json. See AGENTS.md.

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
