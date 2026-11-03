# 세션 시작과 완료 아카이브

새 세션에서 `teamdev --root . session-summary`를 우선 조회한다.
`active/`는 완료되지 않은 작업, `completed/`는 사용자가 최종 승인한 작업이다.
정본 상태는 `docs/tasks/<TASK>/state.json`이고 단계와 승인 이력 및 archive.plan_dir을 기록한다.
작업 재개 전에 소유권, 최근 Worker 활동/heartbeat, 인계 문서, 승인 문서 해시를 확인한다.
완료 승인 시 `docs/exec-plans/active/<TASK>/` 전체가 `docs/exec-plans/completed/<TASK>/`로 이동된다.
부분 오류가 발생하면 `session-summary`가 불일치를 보고하며 자동으로 재개하거나 완료 처리하지 않는다.

## Lifecycle integrity (v0.10)

- 새 세션 시작 시 `teamdev --root . session-summary`와 `teamdev --root . lifecycle-check --strict`로 진행/완료 TASK와 정본 무결성을 확인한다.
- `docs/product-specs/TASK-ID.md`와 `docs/tasks/TASK-ID/`(상태·승인·evidence 포함)는 완료 후에도 고정 경로에 둔다.
- 최종 승인 시 `docs/exec-plans/active/TASK-ID/` 폴더 전체만 `docs/exec-plans/completed/TASK-ID/`로 이동한다.
- 완료 판정은 `state.json`의 COMPLETED, 사용자 최종 승인, Plan 위치, 승인 당시 Spec/Plan SHA-256이 모두 일치할 때만 가능하다.
- 중복 Plan/Spec 또는 state 누락, 해시 불일치 시 임의 파일 이동·상태 변경 없이 BLOCKED로 보고한다.
- 과거 COMPLETED 상태인데 Plan이 active에 남아 있으면 `teamdev archive-completed TASK-ID`를 먼저 미리보고 승인 후 `--apply`한다.

## Startup Dashboard and Skill Usage Ledger (v0.12)
- 첫 세션 시작에는 `teamdev startup`과 `teamdev session-summary`를 실행하여 TASK/상태/사용자 조치를 표시한다.
- `teamdev skill-history`로 단계별 스킬 이력을 확인한다. 기록 없음은 미사용의 증거가 아니다.
- 스킬을 실제 호출한 뒤, TASK evidence/ 아래에 호출 근거를 기록하고 `teamdev skill-record TASK --skill NAME --role ROLE --session-id ID --evidence FILE` 실행한다.
- 사용 기록은 에이전트 선언이므로 실제 런타임 로드의 독립 증명이 아니다. 증거 없는 사용 성공 주장을 금지한다.
- 활성 Worker가 있다면 소유권을 확인하기 전 재개하지 않는다.
