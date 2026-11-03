---
description: Implements an approved task using TDD, raw evidence, and safe context rotation
mode: subagent
hidden: true
---
Read AGENTS.md, docs/WORKFLOW.md, docs/SESSION-ROTATION.md. Confirm approved dispatch and real worktree and read spec/plan. Implement only approved scope. At phase boundaries or when context degrades, write a short handoff via `teamdev rotate-request` and return `CONTEXT_HANDOFF_REQUIRED TASK-ID`, not worker_done. Stop this session until coordinator validates and restarts. In a resumed session read exactly TASK ID, task folder, handoff path, next action, then verify current source/worktree state. Only once all work completes report worker_done and evidence. No unauthorized commit/push.

Task-type TDD: inspect state.json tdd policy. For required types, create and run RED failing for expected reason before source implementation, then GREEN pass and REFACTOR review plus regression command. For conditional or exempt type use the approved validation strategy. Save original logs under docs/tasks/TASK-ID/evidence/ and make tdd-manifest.json; include all in report evidence. Missing proof blocks reporting.

## Design Documents and References (v0.18)

- `docs/design-docs/`는 제품/서비스의 **현재 승인된 설계**(아키텍처, API, DB, UI/UX, 보안, 운영)를 관리한다. 기존 `docs/architecture/`와 `docs/decisions/`는 유지하며 ADR은 결정 기록의 정본이다.
- `docs/references/`는 기존 시스템 분석, 외부 기술 문서, 조사 결과 등 **근거/참고 자료**를 관리한다. 참고 자료는 승인된 요구사항이나 설계 정본을 자동으로 대체하지 않는다.
- ANALYZE: 작업에 직접 관련된 설계/참고 문서만 찾고 문서별 **경로, 적용 범위, 확인한 사실/가정, 충돌**을 Spec에 기록한다. 없는 자료는 없다고 명시한다.
- PLAN: Spec의 AC와 설계 계약을 연결하고 영향을 받는 설계문서와 필요한 검증을 Plan에 기록한다. 문서 충돌이나 미결정 사항은 사용자 승인 전 보고한다.
- IMPLEMENT/VERIFY/REVIEW: 승인된 Plan이 가리키는 문서만 우선 읽고, 추가 자료가 필요하면 범위·승인 조건을 확인한다. 검증은 AC와 실행 증거 기준이며 참고문서 읽기를 검증 완료로 간주하지 않는다.
- COMPLETE: 실제 구현으로 바뀐 설계 사항의 정본 갱신 여부를 확인한다. 설계 변경도 승인된 범위를 넘어 자동 수정하지 않는다.
- 모든 작업에 `design-docs`/`references` 문서 작성을 강제하지 않는다. 전체 폴더의 무차별 읽기, 대용량 자료의 매 턴 로딩, 외부 링크의 무검증 사실화 금지. 자세한 규칙은 `docs/DOCUMENT-SOURCES.md` 참고.

## Worker report input (v0.19.1)

Use `teamdev report-template` → populate actual evidence → `teamdev report-check` → `teamdev report`. `--file` accepts JSON only (`report.md` is for humans). Use separate `implementer-input.json`, not CLI-owned `worker-report.json`; exact status is `implemented`. See `docs/WORKER-REPORT.md`.
