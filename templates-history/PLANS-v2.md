# 개발 작업 및 승인 절차 — CLI 명령은 사용자가 아닌 **에이전트가 실행**한다

에이전트는 세션 시작 시 `python3 scripts/workflow.py next`로 작업을 확인한 뒤 **설치된 외부 원본 스킬**을 사용한다. OpenCode·Codex·Claude Code는 동일한 `docs/exec-plans/active/TASK-ID/` 작업 폴더를 공유한다.

| 단계 | 에이전트 수행 내용 | 산출물 및 제어 |
|---|---|---|
| 분석(Analyze) | `workflow.py new --id TASK-001 --title '...'` 실행 후 원본 진단 스킬 적용 | `analysis.md` |
| 계획(Plan) | 원본 `to-spec`, `to-tickets`, `writing-plans` 적용 | `spec.md`, `plan.md`, `ac-tests.json` |
| 계획 승인 | **대화에서 사용자에게 승인 요청**. 명시적 승인 후에만 `workflow.py approve --id TASK-001 --user-confirmed` 실행 | 시각·승인 표시만 기록하며 실제 사용자 인증은 아님 |
| 구현(Implement) | `workflow.py gate --id TASK-001 --stage implement` 검사 후 원본 TDD 스킬 적용 | 소스·테스트·선택적 RED 증거 |
| 검증(Verify) | `workflow.py run --id TASK-001 --ac AC-01 -- python3 -m pytest tests/test_feature.py` | 실행 시각이 포함된 로그, 종료 코드, 소스 지문 |
| 리뷰(Review) | `workflow.py gate --id TASK-001 --stage review` 검사, 가능하면 독립적 원본 `code-review` 사용, `workflow.py review --id TASK-001 --verdict PASS --notes-file review.md` 기록 | 실질적 리뷰 메모. 독립성은 자동으로 검증되지 않음 |
| 완료(Complete) | `workflow.py gate --id TASK-001 --stage complete` 검사 후 **대화에서 사용자에게 완료 승인 요청**. 명시적 승인 후에만 `workflow.py complete --id TASK-001 --user-confirmed` 실행 | 작업 폴더를 `completed/`로 이동 |

사용자와는 자연어로 소통하면 충분하다. 에이전트가 내부 명령을 직접 실행하며 사용자에게 명령 복사를 요구하지 않는다. `--user-confirmed`는 에이전트의 승인 확인 기록이지 **사람의 신원을 증명하는 수단이 아니다.** 자동 승인하지 않는다. 리뷰 FAIL이면 구현·검증으로 돌아가 테스트를 다시 수행한다. 오래된 리뷰로 완료 처리할 수 없다.

`ac-tests.json`은 각 AC 식별자에 비어 있지 않은 테스트 명령 설명을 대응시킨다. 게이트는 성공한 명령 실행 기록과 현재 소스 지문을 검사하지만, **테스트가 AC의 의미를 실제로 충족하는지는 판별하지 않는다.** 아무 작업도 하지 않는 명령이나 무관한 테스트를 증거로 사용하지 않는다.

## 새 세션 — 필수 첫 작업

모든 에이전트는 새 세션에서 `python3 scripts/workflow.py session`을 실행하고 **다른 작업을 시작하기 전에** 활성 작업을 대화로 요약한다. 이 명령은 읽기 전용이며 세션 시작만으로 작업 생성·승인·리뷰·완료가 진행되지 않는다. `--json`은 기계 판독을 지원하고 `--all`은 완료 계획도 포함한다. 사용자가 직접 명령을 입력할 필요는 없다. 호스트가 자동으로 시작 명령을 실행한다고 가정하지 않는다. 제공된 실행기를 사용하면 터미널 시작 시 출력을 보장할 수 있지만, 에이전트가 지침을 준수하는지는 호스트별 검증이 필요하다.

OpenSpec을 함께 사용하는 경우 해당 변경 명세를 `product-specs` 아래에 중복 작성하지 않는다. 작업 실행 계획과 증거만 별도로 보관한다.

## 단계별 사용자 보고 의무

분석·계획·구현·검증·리뷰·완료 단계가 끝날 때마다 에이전트는 [`ai-workflow/STAGE-REPORTING.md`](ai-workflow/STAGE-REPORTING.md)에 정의된 **상세한 한국어 사용자 보고**를 대화에 표시한다. 완료한 작업, 증거, 담당자가 명시된 잔여 작업, 다음 사용자 조치(없으면 “사용자 조치 불필요”)를 반드시 포함한다. 검증 단계는 AC별로 보고하고, 리뷰 단계는 심각도·위치·수정·잔여 위험을 보고한다. 사용자 승인이 없는데 승인된 것으로 처리하지 않는다. 파일 기록만으로 대화 보고를 대체하지 않는다.
