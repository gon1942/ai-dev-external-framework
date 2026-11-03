# 팀 개발 워크플로

## 문서 정본
- `docs/product-specs/<TASK>.md` : 문제, 목표, 범위, 인수 조건(AC).
- `docs/exec-plans/active/<TASK>/plan.md` : 변경할 파일, Task Graph, 테스트, 롤백.
- `docs/tasks/<TASK>/` : 작업 상태, handoff, 보고서, 원본 증거, 승인 기록.
- `docs/architecture/` : 공유 아키텍처, `docs/decisions/` : ADR.

## 6단계
1. **ANALYZE**: 현재 구현과 요구사항 조사. 추정과 확인 사실 구분.
2. **PLAN**: AC가 검증 가능한지 확인, Task Graph와 실행 명령 작성.
3. **IMPLEMENT**: 명시 승인과 문서 지문 확인 후 TDD 기반 최소 범위 수정.
4. **VERIFY**: 독립 검증자가 실제 명령을 실행하고 원본 로그, 종료코드, 환경을 기록.
5. **REVIEW**: 구현/검증과 독립된 검토자가 회귀·보안·유지보수성 검토.
6. **COMPLETE**: 담당자의 명시 승인 후 종료. 회고 기록.

## 작업 파견
Coordinator는 `handoff.json`을 만들지만 **CLI는 실제 AI 워커를 호출하지 않습니다**. 에이전트별 네이티브 위임 기능을 통해 실행합니다. 위임이 지원되지 않으면 같은 CLI를 인간 개발자가 실행할 수 있습니다.

## 증거 신뢰 모델
증거 파일의 **존재/무결성**은 기계적으로 검증하지만, 단순 JSON의 PASS 값이 실제 테스트 실행을 증명하지는 않습니다. 검증 명령은 CI 또는 신뢰 가능한 실행기에서 재실행해야 합니다. 사용자는 PR 보호 규칙과 승인자 권한을 별도 구성해야 합니다.

## 작업 동시성
이 CLI의 작업별 상태 파일에는 DB 락이 없으므로 같은 작업을 여러 사람이 동시에 갱신하지 않습니다. 브랜치/워크트리를 분리하고 각 작업을 한 명이 소유하며 PR로 통합합니다. 원격 협업에서의 권한·동시성 관리는 Git 플랫폼이 담당합니다.

## 컨텍스트
AI에 이전 대화 전체를 전송하지 않습니다. 스펙, 승인 계획, ADR, 관련 코드, 실행 증거의 경로와 해시만 전달하고 필요시 원문 조회합니다. 개인 메모리는 정본이 아닙니다.


## Coordinator 실행 연결 (v0.3.0)
사용자 요청 → ANALYZE → PLAN → 명시적 사용자 계획 승인 → Coordinator가 **실제로** Implementer 호출 → 검증 보고 등록 후 Verifier 호출 → 검증 PASS 등록 후 Reviewer 호출 → 사용자 최종 완료 승인. `handoff.json` 생성은 실행을 의미하지 않습니다.

권장: 코딩 에이전트의 네이티브 Task/Agent/multi-agent 도구로 각 단계의 새 Worker를 실행합니다. Coordinator는 각 호출 직전 `teamdev --root . next TASK-ID`로 상태를 확인합니다. 네이티브 위임이 지원되지 않으면 `teamdev --root . drive TASK-ID --runtime opencode|claude|codex --execute`로 실제 CLI를 순차 호출합니다. 외부 CLI가 설치되어 있어야 합니다. `drive`는 이미 승인된 TASK만 시작하고, 각 워커의 *실제 상태 파일 전이*가 없으면 중단합니다. 단순 종료코드 0은 PASS가 아닙니다. 승인자 신원은 CLI만으로 인증하지 못합니다.

Worker가 회전을 요청하면 `CONTEXT_HANDOFF_REQUIRED` 상태에서 기존 프로세스가 반환된 다음 인계를 검증하고 새 CLI 프로세스를 실행합니다. 작업/worktree를 유지합니다. 원본 로그는 작업 evidence에 보존하고, 회전 중에는 최종 보고를 금지합니다.

기존 v0.2 프로젝트는 `teamdev --root . upgrade-routing`으로 변경 미리보기, `teamdev --root . upgrade-routing --apply`로 설정/역할 파일을 백업한 후 선택 병합합니다. `AGENTS.md`와 `CLAUDE.md` 사용자 지침은 자동 덮어쓰지 않으므로 v0.3 파견 규칙을 직접 반영해야 합니다.

## RTK / CRG (v0.4)
At session start, Coordinator may call `teamdev --root . tools-status`. CRG is optional for complex ANALYZE/PLAN and security/architecture REVIEW; refresh its project graph only when actually needed. RTK reduces shell output only when hooks are configured for the active agent, never assume it is enabled from CLI discovery. Preserve uncompressed test stdout/stderr plus exit status as evidence. See `docs/TOOLS.md`.


## Session Start and Plan Archive (v0.6)
- 새 세션 시작 시 `teamdev --root . session-summary`를 호출하여 진행 중/완료/차단 TASK와 다음 행동을 확인한다.
- 기존 작업에 활성 Worker 기록이 있으면 소유권과 실행 상태를 확인하기 전 재개하지 않는다.
- `teamdev new TASK-ID "제목"`를 문서 작성보다 먼저 실행한다.
- 최종 사람 승인에만 `teamdev approve TASK-ID --scope completion --actor <approver> --confirm APPROVE`를 실행한다. 이 명령은 실행 계획 폴더 전체를 active에서 completed로 옮긴다.
- 완료 처리는 사용자 승인 증거가 확보된 경우에만 실행하고, commit/push는 별도 승인이다.


TDD policy (v0.9): Create tasks with `teamdev new TASK-ID "title" --type feature|bugfix|behavior_change|api|business_logic|ui_visual|configuration|refactoring|documentation`. Classify during ANALYZE. Use `teamdev tdd-set TASK-ID --type TYPE --actor coordinator` before plan-ready to correct classification. Required types demand evidence/tdd-manifest.json with RED/GREEN/REFACTOR logs. UI/config/refactoring require alternative verification logs; docs require validation logs. `teamdev tdd-check TASK-ID` before verifier PASS. Do not fabricate evidence. Legacy tasks without tdd field remain on legacy workflow until explicitly migrated.

## Lifecycle integrity (v0.10)

- 새 세션 시작 시 `teamdev --root . session-summary`와 `teamdev --root . lifecycle-check --strict`로 진행/완료 TASK와 정본 무결성을 확인한다.
- `docs/product-specs/TASK-ID.md`와 `docs/tasks/TASK-ID/`(상태·승인·evidence 포함)는 완료 후에도 고정 경로에 둔다.
- 최종 승인 시 `docs/exec-plans/active/TASK-ID/` 폴더 전체만 `docs/exec-plans/completed/TASK-ID/`로 이동한다.
- 완료 판정은 `state.json`의 COMPLETED, 사용자 최종 승인, Plan 위치, 승인 당시 Spec/Plan SHA-256이 모두 일치할 때만 가능하다.
- 중복 Plan/Spec 또는 state 누락, 해시 불일치 시 임의 파일 이동·상태 변경 없이 BLOCKED로 보고한다.
- 과거 COMPLETED 상태인데 Plan이 active에 남아 있으면 `teamdev archive-completed TASK-ID`를 먼저 미리보고 승인 후 `--apply`한다.

## Coordinator Progress Reporting (v0.14)

- Run `teamdev progress --task TASK-ID` at meaningful transitions: after PLAN is ready (before requesting approval), after confirmed Worker dispatch, after Worker return, after VERIFY/REVIEW result recording, before final user approval, and after COMPLETE archive. Also show `teamdev progress` at SESSION start when tasks exist.
- Present a concise human-readable status: TASK, stage, workflow status, Worker / observed activity, stage pipeline, user action, and next execution. Report FAIL / BLOCKED immediately.
- Show actual monitored facts, not fabricated progress percentages. `RECENT_ACTIVITY` from heartbeat is not proof of a live native Worker or of successful verification. Never call `worker-start` before confirmed dispatch or `worker-stop` before confirmed return.
- Do not poll `teamdev monitor` inside a synchronous native Task call. During long runs the human may use a separate terminal: `teamdev monitor --watch --interval 3`. Only report genuine new progress on real events, not repetitive messages.
- Preserve both explicit human approval gates. Progress display must never auto-approve, advance workflow, or overwrite TASK evidence.
- Detailed usage: `docs/PROGRESS.md`. `teamdev progress --json` is read-only and machine-readable.

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

## 자가개선 정식 반영 (v0.18.2)

개선 후보는 기존 Spec/Plan/TASK 라이프사이클을 따르되, 검증·리뷰·사용자 최종 승인 이전에는 공식 정책 정본을 수정하지 않습니다. 검증된 후보도 자동 반영하지 않으며, `docs/SELF-IMPROVEMENT.md`의 별도 스테이징 및 apply 게이트를 따릅니다.

## Worker report input (v0.19.1)

Use `teamdev report-template` → populate actual evidence → `teamdev report-check` → `teamdev report`. `--file` accepts JSON only (`report.md` is for humans). Use separate `implementer-input.json`, not CLI-owned `worker-report.json`; exact status is `implemented`. See `docs/WORKER-REPORT.md`.
