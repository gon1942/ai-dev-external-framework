# plan: 완료 작업 active 잔존(고아 폴더) 탐지 기능 추가

- 상태: done
- 생성일: 2026-10-30
- 브랜치: main
- 세션 식별자: gon-20261030-0846
- 요청 한 줄: 완료된 작업이 active/completed에 이중 존재하는 잔존 형상의 원인 분석 후, 공통 프레임워크(workflow.py, lib/status.js)에 고아 폴더 탐지·경고 추가

## 요청 유형
MIXED (원인 분석 + 구현)

## 목적
작업 완료 후 active/TASK-xxx 잔존(고아 폴더)이 발생해도 프레임워크가 이를 즉시 발견·경고하고,
고아 폴더가 실제 completed 작업을 가리지 않게 한다.

## 확인된 사실 (원인 분석)
1. `workflow.py complete`는 `p.rename(dst)`로 active→completed 이동. 프레임워크 스스로는 잔존을 만들지 않는다.
2. 잔존 발생 경로: 완료 후 외부 작성자(E2E의 하드코딩 active 경로 + mkdirSync, 에이전트, 사람)가
   `active/TASK-xxx/`를 재생성 → status.json 없는 고아 폴더. (web 프로젝트에서 실제 발생, 동일 패턴)
3. 프레임워크의 취약점 3곳:
   - `scripts/workflow.py` `session`: `glob('*/status.json')`만 스캔 → 고아 불가시.
   - `lib/status.js` `sessionStatus` 6행: `if(!fs.existsSync(file))continue;` → 고아를 조용히 스킵.
     (설치되는 `.ai-dev/session-status.cjs`도 동일 로직)
   - `scripts/workflow.py` `get()`: active 우선 탐색이라 고아가 실제 completed 작업을 가림(섀도잉).
     해당 ID 명령 실행 시 FileNotFoundError로 혼란스러운 BLOCK.
4. `lib/install.js` 38행: 프레임워크의 `scripts/workflow.py`를 사용 프로젝트에 그대로 복사 설치 →
   여기서 고치면 재설치/업그레이드 시 전파된다. ("사본" 디렉터리 diff = SAME, 고아 경고 없음 확인)

## 가설
- web 프로젝트에 적용한 고아 경고는 해당 프로젝트 로컬 workflow.py에만 반영되었고
  공통 프레임워크 원본에는 아직 없다. (diff SAME으로 확인됨 — 가설이 아니라 사실)

## 범위 (변경 대상)
1. `scripts/workflow.py`
   - `get()`: `(p/'status.json').is_file()` 조건 추가 → 고아 폴더는 작업 해석에서 제외.
   - `session`: 상태별(active/completed) status.json 없는 디렉터리 → WARNING 추가.
   - `session`: 같은 ID가 active+completed 양쪽 디렉터리에 존재 → WARNING 추가.
2. `lib/status.js`
   - `sessionStatus`: status.json 없는 active 고아 → warnings push (기존 silent continue 교체).
   - active 작업 ID가 completed에도 존재 → warnings push.
3. `test/workflow.test.js`
   - sessionStatus 고아 경고 테스트 (고아 + completed 실제 → active_count 0, 경고 포함).
   - workflow.py session 고아 경고 테스트 (temp 프로젝트 복사 후 python3 실행, 기존 spawnSync 패턴).

## 비범위 (제외)
- web 프로젝트 evidence-paths.ts (이미 완료된 작업)
- 고아 폴더 자동 삭제/이동 (데이터 파괴 위험 — 경고 후 사람이 판단)
- `next`/`status` 명령의 고아 스캔 (session이 세션 시작 진입점, 최소 변경)
- README 문서화 (요청 시 별도)
- `new`의 중복 ID 처리 변경 (현재 "task exists" 차단이 안전)

## 불변조건
- 기존 세션 출력 형식/phase 분류 불변 (테스트가 형식을 검증함).
- workflow.py 기존 인터페이스(명령/인자) 불변.
- 싱글쿼테이션 등 기코드 스타일 유지 (workflow.py는 세미콜론 압축 스타일, status.js 동일).

## 리스크
- get() 변경 후 "고아만 존재하는 ID"는 unknown task 오류로 바뀜 (기존: FileNotFoundError BLOCK —
  동일하게 차단되므로 회귀 아님, 메시지 개선).
- workflow.py는 사용 프로젝트에 재설치로 전파되는 공유 게이트 — 최소 diff 필수.

## 검증 전략
- `npm test` 전체 통과 (기존 5개 + 신규).
- python 테스트: temp 프로젝트에서 고아/이중 존재 시 WARNING 출력 확인.

## 완료 조건
- 고아 폴더가 있으면 session(python+node) 경고 출력.
- 고아가 completed 실제 작업을 가리지 않음(get 수정).
- npm test 통과.

## Task Breakdown
1. workflow.py: get() + session 고아/이중 존재 경고
2. lib/status.js: 고아/이중 존재 경고
3. test/workflow.test.js: 신규 테스트 2건
4. npm test 검증

## 완료 기록
- 완료일시: 2026-10-30 09:05 KST
- 수정 파일:
  - scripts/workflow.py — get()이 status.json 있는 폴더만 작업으로 해석(고아 섀도잉 제거), session에 고아/이중 존재 WARNING 추가
  - lib/status.js — sessionStatus가 고아 폴더를 silent skip 대신 경고 수집, completed 이중 존재 경고 추가
  - test/workflow.test.js — 신규 테스트 2건(노드 세션 경고, python 세션 경고+completed 작업 정상 해석) 순수 append(+18/-0)
- 검증 결과: npm test 56/56 통과. 엣지 수동 확인: 빈 프로젝트 정상, completed 고아는 session --all에서 경고, status 명령 회귀 없음
- DIFF-REVIEW 판정: PASS (의도한 3개 코드 파일만 변경, test 파일은 append-only, 민감정보 없음)
- 커밋: 미커밋 (사용자 승인 대기)
