# Coordinator 단계별 진행 상황 표시 (v0.14)

`teamdev progress` : 전체 작업의 작업 현황, 단계 파이프라인, 사용자 조치, 다음 실행, Worker 활동을 간결하게 표시합니다.
`teamdev progress --task TASK-ID` : 특정 TASK만 표시합니다.
`teamdev progress --json` : 자동화/대시보드용 구조화 데이터입니다.
`teamdev monitor --task TASK-ID` : 자세한 활동 이벤트를 별도로 조회합니다.
`teamdev monitor --watch --interval 3` : 사용자 별도 터미널에서 실시간에 가까운 관측을 수행합니다.

Coordinator는 새 SESSION 시작, PLAN 승인 요청 직전, 승인 후 Worker 파견 확인 시점, 각 Worker 반환 후, 검증/리뷰 결과 확인 후, 최종 승인 요청 직전, 최종 완료 후에 최신 `teamdev progress --task TASK-ID` 결과를 사용자에게 요약하여 표시합니다.

모니터의 `RECENT_ACTIVITY`는 heartbeat 관측일 뿐 네이티브 Worker 실행 중이라는 확증이 아닙니다. `worker-stop`은 Worker 반환 후에만 기록합니다. 로그·검증 통과·사용자 승인 여부는 별도 근거로 확인해야 합니다. 동기 서브에이전트 호출 중 Coordinator가 임의로 주기적 명령을 수행할 수는 없습니다.

주의: 진척률 퍼센트를 임의 계산하거나, 상태 보고를 이유로 승인 게이트를 우회하지 않습니다. 상태 조회는 읽기 전용입니다.

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

