# Worker Session Rotation — 작업을 유지하고 대화만 교체

대상: OpenCode, Claude Code, Codex 공통 계약. Coordinator 역할은 별도이고 각 런타임의 Worker 생성 도구는 실제 지원 여부 확인이 필요하다.

## 시작 전
`teamdev new` → Spec/Plan 작성 → `plan-ready` → 사용자 계획 승인 → `dispatch`.
원본 정본은 `docs/product-specs/TASK-ID.md`, `docs/exec-plans/active/TASK-ID/plan.md`; 실행 상태는 `docs/tasks/TASK-ID/state.json`.

## 회전 트리거
- PLAN→BUILD 또는 BUILD→TEST 등 단계 경계에서 필요성 판단 (매번 강제하지 않음)
- 실제 컨텍스트 부족 징후
- 긴 로그/재시도로 안전한 문맥 유지가 어려움

실제 사용률을 알 수 없는 플랫폼에서는 임의의 60% 같은 자동 비율을 표시하지 않는다.

## 회전 절차
1. Worker가 변경 파일, 완료 사항, 실제 검증 요약, 차단 사항, 다음 **한 가지 행동**을 준비한다.
2. 다음 명령으로 `docs/exec-plans/active/TASK-ID/context-handoff.md`를 만든다.

```bash
teamdev --root . rotate-request TASK-001 \
  --actor dev-a --session-id worker-01 --worktree /absolute/path/to/worktree \
  --completed '로그인 경로 수정' --changed-files 'src/login.py' \
  --verification '단위 테스트 8/10 성공, 원본 docs/tasks/TASK-001/evidence/test.log' \
  --blockers '남은 2개 실패 분석 필요' --next-action '실패한 로그인 단위 테스트 재현' \
  --reason 'BUILD→TEST 단계 경계'
```

3. CLI는 `CONTEXT_HANDOFF_REQUIRED`를 기록하고 `worker_done`으로 취급하지 않는다. Worker는 더 이상 소스 변경을 수행하지 않는다.
4. Coordinator는 이전 Worker 종료를 **실제로 확인**하고 새 세션의 새 ID를 확보한다. 다음 명령으로 인계를 검증한다.

```bash
teamdev --root . rotate-resume TASK-001 --actor coordinator \
  --previous-session-stopped --new-session-id worker-02
```

5. 출력의 TASK ID / TASK 정본 폴더 / context-handoff 경로 / next_action만 새 Worker 프롬프트에 전달한다. 동일한 worktree에서 재개한다. 새 Worker는 시작 즉시 인계·승인·Git 상태와 실제 파일 차이를 확인한다.
6. 최종 구현 완료 시에만 `teamdev report`와 `worker_done`을 사용한다.

## 보안·정합성
- 비밀정보, 키, 환경값, 대화 전문, 전체 테스트 로그 인계 금지. 로그는 증거 폴더에 별도 보관.
- 인계 파일 최대 8KiB, 65행, 인식된 짧은 필드만 허용. 일부 민감정보 패턴은 자동 차단하지만 완전한 DLP는 아님.
- 정본 승인 SHA-256, dispatch SHA-256, TASK, worktree, 이전 세션 ID, 인계 파일 지문을 검증한다.
- 현재 CLI는 **이전 세션 종료 주장을 확인하는 플래그**만 받는다. 프로세스가 실제 종료됐는지 감시하거나 새 모델 세션을 시작하지 않는다. 운영 환경에서는 native agent runtime adapter가 이를 보장해야 한다.
- 복수 개발자 공유 저장소의 동시 회전에는 별도 중앙 잠금·충돌 해결이 필요하다. CLI 상태 파일은 서버 기반 동시성 제어를 제공하지 않는다.

## Orca Coordinator Session Recovery (v0.16)

- Keep TASK, worktree, approvals and evidence stable. Only the **main Coordinator model conversation** changes; do not spawn another Coordinator as a subagent.
- At a safe stage boundary (or when context pressure is detected), ensure any native Worker call has actually returned and its monitoring record is stopped. Then use `teamdev coordinator-handoff TASK --session-id CURRENT --next-action "one next action" --reason "context pressure"`.
- This command freezes `teamdev next`, native Worker registration and CLI Worker execution for that TASK while PREPARED. The freeze is enforced by cooperating `teamdev` commands, not by Orca or direct file writes.
- In Orca, open a **fresh main Coordinator conversation** in the same project/worktree. Do not resume the old context or have both conversations advance the same TASK.
- After confirming the old Coordinator is inactive, from the NEW session call `teamdev coordinator-resume TASK --new-session-id NEW --old-session-stopped`. The flag is an operator/agent assertion, **not** an independent process-liveness check.
- Read the short `docs/tasks/TASK/coordinator-handoff.md`, run `teamdev startup`, `teamdev status TASK`, `teamdev next TASK` and verify approvals and Worker ownership before dispatch.
- No fictional token percentage: checkpoint at real phase boundaries or contextual pressure. No automatic Orca window creation/clearing is claimed. `teamdev coordinator-session TASK` shows PREPARED/RESUMED state.
- Handoffs preserve original logs externally; never paste secrets, transcript dumps or raw logs into the handoff file. Do not commit or push without separate user approval.
