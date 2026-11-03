# Plan: airun에 UI/UX 스킬 3종 반영
- 상태: active
- 생성: 2026-10-30, 브랜치: N/A(airun은 git 아님), 세션: gon-20261030-opencode
- 요청: airun 프로젝트에 frontend-design/ux-audit/tastemaker 설치 (로컬 프레임워크 정책으로 직접 sync)

## Plan
- **Task Summary**: airun 엔진 갱신(루트 레이아웃+라이선스 동반 지원) → 프레임워크 bin으로 sync --install-custom → 3에이전트 경로 검증
- **Scope**: airun/.ai-dev/skill-manager-engine.cjs 교체, skill sync(신규 3종 설치 + stage-skills.json/lock 갱신), 신규 스킬 디렉터리 9개
- **Non-Goals**: 기존 스킬 재설치, AGENTS 문서 변경, npm publish, dependency-check 목록 갱신(프레임워크 후속 과제로 기록)
- **Risks**: airun stage-skills.json에 비관리 수정이 있으면 sync 거부 → 사전 lock hash 확인. airun은 git 아님(되돌리기 수동)
- **Verification Strategy**: dry-run 선행, 설치 후 3에이전트×3종 SKILL.md·라이선스·.git 부재 확인
- **Definition of Done**: 3종 3에이전트 설치 + stage-skills.json 갱신 확인

## Task Breakdown
- [ ] 엔진 파일 교체
- [ ] dry-run 확인
- [ ] 실설치 + 검증

## 완료 기록
- 완료일시: 2026-10-30
- 수정 파일: airun/.ai-dev/skill-manager-engine.cjs(엔진 교체), .ai-dev/stage-skills.json+lock(정책 sync), 신규 스킬 디렉터리 9개(3종×3에이전트)
- 검증: dry-run 통과, 9경로 SKILL.md·라이선스 동반·.git 부재 확인, stage 배정(analyze/verify=ux-audit, plan/implement=frontend-design, review=tastemaker) 반영 확인
- DIFF-REVIEW: PASS (airun은 git 아님 — read-back 검증으로 갈음)
- 커밋: 해당 없음
