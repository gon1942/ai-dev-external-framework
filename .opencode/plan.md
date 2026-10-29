# Plan: upgrade 명령 구현 (3-way 병합 기반 기존 프로젝트 최신화)
- 상태: active
- 생성: 2026-10-29, 브랜치: main, 세션: gon-20261028-0945
- 요청: 기존 프로젝트 최신화 — 사용자 커스텀 보존 3-way 병합 upgrade 명령 (BUILD 승인됨)

## Plan
- **Task Summary**: `npx ai-dev upgrade` 한 명령으로 스킬/도구 갱신 + 관리 파일(AGENTS.md·PLANS.md·dependency-check.cjs) 3-way 병합 갱신
- **Scope**:
  1. `lib/upgrade.js` 신규 — 관리 파일별: 순정(base 매칭)→자동교체/3-way 병합(git merge-file)/base 미발견→제안본/미존재→생성. 항상 .bak-upgrade 백업, --dry-run 지원, 매니페스트(.ai-dev/managed-files.json) 기록·사용
  2. `templates-history/` 신규 — 과거 템플릿 스냅샷(병합 base용, npm 패키지에 포함 — npx엔 git history 없음)
  3. `lib/init.js` — 설치 시 매니페스트 기록(향후 upgrade의 완전한 base)
  4. `bin/ai-dev.js` — upgrade 명령·help
  5. `test/upgrade.test.js` — 순정교체/커스텀보존/충돌마커/제안본/dry-run/매니페스트 (합성 템플릿으로 주입형 테스트)
  6. package.json 1.3.0 + files에 templates-history 추가, README upgrade 절
- **Non-Goals**: docs/ai-workflow 하위 개별 문서 병합(필요 시 후속), 자동 커밋, 충돌 자동해결(사용자 확정)
- **Risks**: base 미매칭 레거시 → 제안본 폴백으로 안전 처리. git merge-file 의존(git 필수 — 이미 installGit이 의존)
- **Verification Strategy**: 단위 테스트 + 실전 검증(t-dd 순정 → 자동교체, my-project → 병합, airun 커스텀 → 보존/충돌 확인)
- **Definition of Done**: 테스트 전부 통과 + 실제 3개 프로젝트(t-dd·my-project·airun) upgrade 성공 + 1.3.0 발행 준비

## Task Breakdown
- [ ] 과거 템플릿 base 수집 (git history + 백업)
- [ ] lib/upgrade.js + init 매니페스트 + bin 명령
- [ ] 테스트 작성·통과
- [ ] 실전 3개 프로젝트 검증
- [ ] README·버전·발행 준비
