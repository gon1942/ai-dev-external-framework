# Plan: airun AGENTS.md·AGENTS-opencode.md 인라인 규칙 적용
- 상태: active
- 생성: 2026-10-30, 브랜치: N/A(airun proj는 git 아님), 세션: gon-20261030-opencode
- 요청: airun 프로젝트에 프레임워크 인라인 규칙 직접 수정 적용 (사용자 승인)

## Plan
- **Task Summary**: airun proj의 AGENTS.md §3에 스킬 로드·정본 경로 2줄 추가, AGENTS-opencode.md 코디네이터 절에 worker-start spec 스킬 명시 1줄 추가
- **Scope**: 위 2개 파일, 총 3줄 추가. 문구는 프레임워크 templates/AGENTS.md에 반영한 것과 동일
- **Non-Goals**: AGENTS-codex.md dangling 참조 정리(별도), t2 정리, airun 워커 교체(기존 설계 유지)
- **Affected Areas**: `/home/gon/work/airun_proj/airun-saas/proj/AGENTS.md`, `.../AGENTS-opencode.md`
- **Risks**: 없음 — 문서 추가만. airun proj는 git이 아니라 되돌리기는 수동
- **Verification Strategy**: 수정 후 grep read-back으로 3줄 존재·위치 확인
- **Definition of Done**: 3줄 추가 확인

## Task Breakdown
- [ ] AGENTS.md §3 불릿 2개 추가
- [ ] AGENTS-opencode.md 코디네이터 절 1줄 추가
- [ ] grep 검증

## 완료 기록
- 완료일시: 2026-10-30
- 수정 파일: airun proj/AGENTS.md L38-39 (+2), proj/AGENTS-opencode.md L42 (+1)
- 검증 결과: grep read-back 3줄 위치·존재 확인 (airun proj는 git 아님 — git diff 불가)
- DIFF-REVIEW: PASS (계획 3줄과 정확 일치, 범위 외 변경 없음)
- 커밋: 해당 없음 (git 아님)
