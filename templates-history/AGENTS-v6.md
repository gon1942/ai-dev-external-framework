# AGENTS.md — AI 개발 공통 진입점

> 적용 대상: OpenCode · Codex · Claude Code. 상세 규칙의 정본은 `docs/` 및 `.ai-dev/`에 있다.

## 1. 불변 원칙

- 요청 범위 외 변경 금지. 기존 작업 상태와 검증 근거를 확인하고 이어서 수행한다.
- 계획 승인 전 구현 금지. 사용자 확인 없이 최종 완료 처리 금지.
- 승인 없이 commit·push·merge 금지.
- 실제 실행 증거 없는 검증·리뷰 PASS 및 완료 선언 금지.
- 민감정보(비밀번호·API 키·토큰·`.env` 값) 출력·기록·커밋 금지.
- 외부 스킬의 설치·선택·실제 호출을 구분하고, 미실행 도구를 실행했다고 보고하지 않는다.

## 2. 세션 시작

프로젝트 루트에서 실행한다.

```bash
node .ai-dev/dependency-check.cjs
node .ai-dev/session-status.cjs
python3 scripts/workflow.py session
```

실제 출력에 따라 에이전트별 설치·누락 스킬, CRG·Playwright 확인 상태, 활성 작업 및 미완료 항목을 사용자에게 보고한다. 실행 오류를 성공으로 간주하지 않는다. 새 세션 자체를 이유로 작업을 생성·승인·완료하지 않는다.

## 3. 작업 흐름

**Analyze → Plan → Implement → Verify → Review → Complete**

- 작업·승인·단계별 절차: `docs/PLANS.md`
- 승인·보안·검증 정책: `docs/ai-workflow/POLICY.md`
- 단계별 스킬 배정: `.ai-dev/stage-skills.json`
- 실제 작업 제어 및 명령 확인: `python3 scripts/workflow.py --help`


각 단계 진입 시 적용 지침과 활성 원본 스킬을 확인한다. `using-superpowers`가 설치되어 있으면 적용 가능성을 판단하되, 스킬 선택과 실제 호출을 구분한다. 단계 게이트와 검증 증거가 문서상 선언에 우선한다.

## 4. 사용자 보고

각 단계 종료 시 `docs/ai-workflow/STAGE-REPORTING.md`에 따라 사용자 대화에 현재 상태·완료·미완료·검증 근거·사용자 조치·다음 단계를 보고한다. 작업 파일 기록은 대화 보고를 대체하지 않는다.

## 5. 문서 확인 시점

| 정본 | 확인 시점 |
|---|---|
| `docs/PLANS.md` | 작업 시작·단계 전환 |
| `docs/ai-workflow/POLICY.md` | 작업 시작·승인·보안 판단 |
| `docs/ai-workflow/STAGE-REPORTING.md` | 단계 종료 |
| `.ai-dev/stage-skills.json` | 단계 진입 |
| `docs/ai-workflow/PROJECT-RULES.md` | 세션 시작·프로젝트 작업 전 |
| `docs/ai-workflow/ENVIRONMENT.md` | 실행·구현·검증 전 |
| `docs/ai-workflow/CODE-QUALITY.md` | Plan·Implement·Verify·Review 단계 |

프로젝트 전용 문서는 존재 시 적용한다. 파일이 없거나 규칙이 충돌하면 추정하지 않고 보고한다. 프로젝트 지침은 공통 승인·보안·검증 원칙을 완화할 수 없다.
