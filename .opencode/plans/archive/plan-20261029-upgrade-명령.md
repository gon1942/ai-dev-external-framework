# Plan: upgrade 명령 구현 (3-way 병합 기반 기존 프로젝트 최신화)
- 상태: done
- 생성: 2026-10-29, 브랜치: main, 세션: gon-20261028-0945
- 요청: 기존 프로젝트 최신화 — 사용자 커스텀 보존 3-way 병합 upgrade 명령 (BUILD 승인됨)

## Task Breakdown
- [x] 과거 템플릿 base 수집 (git history에서 11종: AGENTS 6·PLANS 2·dependency-check 3 → templates-history/)
- [x] lib/upgrade.js — 유사성 게이트(공통 라인 30%)·후보 base 병합 시도(충돌 0 우선)·add/add 자동 병합·같은 줄 수정만 마커·충돌 3+ 제안본 폴백·항상 .bak-upgrade 백업·dry-run
- [x] bin/ai-dev.js upgrade 명령 (스킬·CRG·Playwright·RTK 갱신 + sync + 관리 파일 병합) + help (repair-deps 우발 개명 사고 즉시 복원)
- [x] test/upgrade.test.js 5건 — 순정교체·커스텀보존·충돌마커·제안본·dry-run/생성/UNCHANGED
- [x] README 기존 프로젝트 적용 절 upgrade로 갱신, package.json 1.3.0 + templates-history 배포 포함
- [x] 실전 검증 3프로젝트: t-dd(전부 MERGED·23종), my-project(AGENTS 병합✓·PLANS 1충돌→approver+회고 결합 해결), airun(§5표 충돌→커스텀 유지+자기교정 §7 추가 해결)

## 완료 기록
- 완료일시: 2026-10-29 (세션 gon-20261028-0945)
- 검증: npm test 54/54 + PY 4/4, 실전 3개 프로젝트 upgrade 성공 (백업 보존)
- 개발 중 발견·수정: ① base 탐색 논리 결함(사용자 수정본은 템플릿과 바이트 일치 불가)→병합 시도 기반 탐색으로 재설계 ② add/add(양쪽 말미 섹션 추가)이 마커로 나오는 문제→자동 병합 해결 ③ 무관 파일까지 병합→유사성 게이트 ④ 테스트 쉼표 오타 2회(재발 방지 필요)
- DIFF-REVIEW 판정: PASS (1.2.0 SIA 변경분과 1.3.0 upgrade 변경분이 작업 트리에 함께 존재 — 커밋 시 분리 또는 통합 결정 필요)
- 커밋: 미커밋 — 1.2.0(SIA)이 npm에 발행됐으나 git 커밋은 안 된 상태로 확인됨(사용자가 npm pack으로 발행한 듯). 커밋·1.3.0 발행은 승인 대기
- 유지보수 규칙: 향후 템플릿 수정 시 구버전을 templates-history/에 스냅샷으로 남겨야 이후 upgrade의 base가 됨
