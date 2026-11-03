# 세션 시작 화면 (v0.7)

`teamdev startup`은 읽기 전용으로 단계/스킬, 미완료/완료 TASK, RTK/CRG 발견 상태를 표시합니다.
`teamdev launch opencode` 또는 `teamdev launch claude|codex`는 실행 전에 터미널 배너를 보여줍니다.
일반 `opencode` 등으로 시작하는 경우 Coordinator가 `teamdev startup`을 호출하도록 지침을 제공하지만 네이티브 첫 화면의 자동 출력은 보장하지 않습니다.

스킬 표시는 프로젝트 번들 설치 여부에 기반하며 실제 로딩/성공과 다릅니다. 전역 스킬은 별도 확인해야 합니다.
권한: Coordinator는 OpenCode `edit` 도구로 Spec/Plan/상태 경로만 수정하도록 제한합니다. Shell 명령 자동 허용은 별개이므로 임의 명령을 통제하는 완전한 경계가 아닙니다.

## Startup Dashboard and Skill Usage Ledger (v0.12)
- 첫 세션 시작에는 `teamdev startup`과 `teamdev session-summary`를 실행하여 TASK/상태/사용자 조치를 표시한다.
- `teamdev skill-history`로 단계별 스킬 이력을 확인한다. 기록 없음은 미사용의 증거가 아니다.
- 스킬을 실제 호출한 뒤, TASK evidence/ 아래에 호출 근거를 기록하고 `teamdev skill-record TASK --skill NAME --role ROLE --session-id ID --evidence FILE` 실행한다.
- 사용 기록은 에이전트 선언이므로 실제 런타임 로드의 독립 증명이 아니다. 증거 없는 사용 성공 주장을 금지한다.
- 활성 Worker가 있다면 소유권을 확인하기 전 재개하지 않는다.

## Coordinator Progress Reporting (v0.14)

- Run `teamdev progress --task TASK-ID` at meaningful transitions: after PLAN is ready (before requesting approval), after confirmed Worker dispatch, after Worker return, after VERIFY/REVIEW result recording, before final user approval, and after COMPLETE archive. Also show `teamdev progress` at SESSION start when tasks exist.
- Present a concise human-readable status: TASK, stage, workflow status, Worker / observed activity, stage pipeline, user action, and next execution. Report FAIL / BLOCKED immediately.
- Show actual monitored facts, not fabricated progress percentages. `RECENT_ACTIVITY` from heartbeat is not proof of a live native Worker or of successful verification. Never call `worker-start` before confirmed dispatch or `worker-stop` before confirmed return.
- Do not poll `teamdev monitor` inside a synchronous native Task call. During long runs the human may use a separate terminal: `teamdev monitor --watch --interval 3`. Only report genuine new progress on real events, not repetitive messages.
- Preserve both explicit human approval gates. Progress display must never auto-approve, advance workflow, or overwrite TASK evidence.
- Detailed usage: `docs/PROGRESS.md`. `teamdev progress --json` is read-only and machine-readable.
