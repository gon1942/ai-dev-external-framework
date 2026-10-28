# Plan: 공통 프레임워크에 RTK 22번째 구성 요소 추가
- 상태: active
- 생성: 2026-10-29, 브랜치: (framework repo 기본 브랜치), 세션: gon-20261028-0945
- 요청: ai-dev-external-framework(npm @gon1942)에 RTK 설치 통합 (BUILD 승인됨)

## Plan
- **Task Summary**: RTK(CLI 출력 압축, 토큰 60-90% 절감)를 22번째 구성 요소로 추가 — playwright.js 패턴 준용
- **Objective**: npx ai-dev 설치 시 사용자 머신에 RTK 바이너리(공식 소스) + 에이전트별 훅 등록까지 자동화
- **Scope**:
  1. `lib/rtk.js` 신규 — inspect/install (플랫폼 감지: linux/mac curl install.sh, win은 안내; RTK_EDITION env 전달; rtk init -g / --opencode / --codex; claude settings.json 패치는 비대화 모건 한계 안내)
  2. `skill-policy.json` — rtk 항목 등록
  3. `lib/init.js` — --skip-rtk 패턴 호출
  4. `lib/deps.js` + `templates/.ai-dev/dependency-check.cjs` — RTK 상태 검사 (바이너리·버전·opencode 1.18.29+ 경고)
  5. 문서 — README §4(21→22), admin-skills/framework-skill-admin.md, templates/docs/ai-workflow/EXTERNAL-SKILLS.md
  6. `test/` — rtk 모듈 테스트 (inspect/dry-run 중심)
  7. `package.json` — 1.0.5 → 1.1.0
- **Non-Goals**: rtk-proxy(BUSL 데몬) 제외, 바이너리 번들/재배포 없음(공식 다운로드만), macOS/Windows 실기 테스트(문서로 보완)
- **Constraints**: 기존 playwright.js 인터페이스(inspect/install/targets, dry 지원) 준수, MIT 프레임워크 정체성 유지
- **Facts (확인됨)**:
  - RTK 1.1.0 이 머신 설치·검증 완료 (rtk ls 압축 동작, opencode 플러그인 ~/.config/opencode/plugins/rtk.ts 등록)
  - install.sh: 공식 release tar.gz + SHA-256 체크섬 + 경로탈취 검사 후 ~/.local/bin 설치 (sudo 불필요)
  - rtk init -g --opencode: opencode 플러그인 + claude 훅 등록 (claude settings.json 패치는 비대화시 수동 단계)
  - opencode 훅 요구버전 1.18.29+, 현재 1.18.35
- **Affected Areas**: 프레임워크 설치 흐름 전체 (신규/기존 프로젝트)
- **Risks**: 플랫폼별 설치 차이(Linux만 실검), 네트워크 차단 환경(오류 안내 처리), claude settings 자동 패치의 비대화 한계
- **Verification Strategy**: lib/rtk.js dry-run/실동작 테스트, npm test 전체 통과, npx ai-dev 통합 경로 확인
- **Definition of Done**: 7건 반영 + npm test 통과 + 승인 없이 커밋하지 않음

## Task Breakdown
- [x] 1단계: RTK 실설치 검증 (이 머신)
- [ ] lib/rtk.js 구현
- [ ] skill-policy.json / init.js / deps.js / dependency-check.cjs 반영
- [ ] 문서 3종 갱신
- [ ] 테스트 추가 및 npm test 통과
- [ ] 버전 1.1.0
