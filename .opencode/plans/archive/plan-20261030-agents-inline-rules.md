# Plan: AGENTS.md 인라인 규칙 추가 (스킬 사용 + 정본 위치)
- 상태: active
- 생성: 2026-10-30, 브랜치: main, 세션: gon-20261030-opencode
- 요청: 공통 프레임워크 templates/AGENTS.md에 스테이지 스킬 사용 규칙과 정본 위치 규칙을 인라인 (사용자 승인)

## Plan
- **Task Summary**: templates/AGENTS.md §3 불릿 2개 추가 — 간접 참조뿐인 §3에 실행 규칙 본문을 넣어 전역 스킬(projflow 등)과의 접근성 경쟁을 해소
- **Objective**: (1) 단계 배정 스킬의 실제 로드 의무화 (2) 정본 문서 경로 고정 (t2 사고 재발 방지)
- **Scope**: `templates/AGENTS.md` §3 불릿 목록 끝에 2줄 추가. 다른 파일·문구 수정 없음
- **Non-Goals**: t2/airun 프로젝트 파일 직접 수정(별도 승인), 세션 훅·workflow.py·PLANS.md 변경
- **Constraints**: 기존 불릿 스타일(평문, 백틱 경로) 유지
- **Affected Areas**: templates/AGENTS.md — 신규 설치 프로젝트에 자동 전파, 기존 프로젝트는 upgrade 3-way 병합 전파
- **Risks**: 템플릿 문구를 검증하는 기존 테스트가 있을 수 있음 → npm test로 확인. 기존 프로젝트 AGENTS.md는 install 시 PRESERVED라 즉시 반영 안 됨(별도 안내)
- **Verification Strategy**: npm test 전체 실행 + git diff 최소성 확인
- **Definition of Done**: §3에 2줄 추가, 테스트 통과, DIFF-REVIEW PASS

## Task Breakdown
- [ ] templates/AGENTS.md §3 불릿 2개 추가
- [ ] npm test 실행
- [ ] CHANGE-REVIEW / DIFF-REVIEW

## 완료 기록
- 완료일시: 2026-10-30
- 수정 파일: templates/AGENTS.md (+2줄, §3 불릿) — 이유: 스킬 로드 의무·정본 경로 규칙 인라인으로 접근성 경쟁 해소
- 검증 결과: npm test 통과 (Node 56/56, Python 4/4)
- DIFF-REVIEW: PASS (작업 분량 = templates/AGENTS.md +2 정확 일치)
- 커밋: 미커밋 (사용자 승인 대기)
