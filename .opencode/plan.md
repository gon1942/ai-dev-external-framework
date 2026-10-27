# Plan: README 오류 수정 및 구조 정리
- 상태: done (active/done/blocked 중 하나)
- 생성: 2026-10-27, 브랜치: main, 세션: gon-MS-7C94-0842
- 요청: 버전 이력 표 삭제 + 분석 결과 항목 1,3,4,5 수정

## Plan
- **Task Summary**: README.md의 깨진 플레이스홀더, npx 잔여 `@`, docs 섹션 번호 체계, 가짜 파일 인용, 버전 이력 표를 수정/삭제한다.
- **Objective**: README와 실제 코드(package.json 1.0.0, skill-policy.json, lib/init.js) 간 불일치 제거.
- **Scope**:
  1. L776·L779 깨진 플레이스홀더(`이미 \`\`를`, `# 같은  버전`) 문장 복구
  3. `ai-dev-external-framework@ ` 잔여 `@` 제거 (31곳, `npm view` 라인 포함)
  4. `## docs/ 디렉터리 안내`~`## 중복 관리 방지` 5개 H2를 3장 산하 `###`로 강등
  5. 구조 예시(L200)의 `docs/README.md` 줄 제거 (lib/init.js 생성 없음 확인)
  6. `## 15. 버전 이력` 섹션 전체 삭제 + 목차 15번 항목 삭제 + dangling `참고:` 삭제
- **Non-Goals**: 항목 2(버전 이력 갱신)는 삭제 대체. 목차 15번 제외 목차 변경 없음. 코드/템플릿 변경 없음.
- **Constraints**: README.md만 수정. 나머지 텍스트·포맷 변경 금지. 커밋/푸시 자동 금지.
- **Assumptions**: `pkg@ subcommand` 형태의 잔여 `@`는 61e0b56 의도(버전 명시 제거)에 따른 제거 대상.
- **Affected Areas**: README.md 1개 파일.
- **Implementation Strategy**: sed/Edit로 패턴 치환 후 diff 확인.
- **Risks**:极低 — 문서 파일 단독 수정. 링크 앵커는 15번 삭제 시 목차 동기화 유지.
- **Verification Strategy**: grep으로 잔여 `framework@ `, 빈 백틱, 버전 이력, docs/README.md 참조 0건 확인; 목차 앵커와 H2 헤더 일치 확인; `git diff` 범위 확인.
- **Definition of Done**: 위 6개 항목 모두 반영, README 외 변경 없음.

## Task Breakdown
- [x] 현재 동작과 영향 파일 확인 (분석 단계에서 완료)
- [x] 범위 내 README 수정
- [x] grep/diff 검증
- [x] CHANGE-REVIEW / DIFF-REVIEW

## 완료 기록
- 완료일시: 2026-10-27 08:42
- 수정 파일: README.md — (1) 빈 백틱/이중공백 플레이스홀더 복구 (3) `framework@ ` 잔여 `@` 31곳 제거 (4) docs 섹션 H2→H3 강등 (5) 구조 예시 `docs/README.md` 제거 (6) `## 15. 버전 이력` 표·목차·dangling `참고:` 삭제
- 검증 결과: `framework@ `/버전 이력/docs/README 참조 grep 0건, H2 번호 1~14 연속·목차 일치, 코드펜스 짝수(82)
- DIFF-REVIEW 판정: WARN — diff에 작업 전부터 존재하던 미커밋 변경(docs/ 디렉터리 안내 섹션 삽입, HEAD에 없음)이 섞여 있음. 범위 내 변경 자체는 일치.
- 커밋: 미커밋
