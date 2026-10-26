# AI Dev External Framework

**OpenCode · Codex · Claude Code에서 동일한 개발 절차를 적용하기 위한 외부 스킬 기반 공통 프레임워크**

> 버전: **0.8.2** · npm 패키지: **`@gon1942/ai-dev-external-framework`**  
> 이 프로젝트는 별도의 AI 코딩 에이전트가 아니라, 기존 에이전트에 **원본 외부 스킬·작업 기록·검증 게이트·세션 상태 확인 설정**을 추가하는 설치 도구입니다.

## 목차

1. [무엇을 해결하나요?](#1-무엇을-해결하나요)
2. [빠른 시작](#2-빠른-시작)
3. [설치되는 구성 요소](#3-설치되는-구성-요소)
4. [외부 스킬 18개](#4-외부-스킬-18개)
5. [실제 개발 작업 흐름](#5-실제-개발-작업-흐름)
6. [새 세션 시작과 상태 확인](#6-새-세션-시작과-상태-확인)
7. [CLI 명령어](#7-cli-명령어)
8. [기존 프로젝트 업그레이드](#8-기존-프로젝트-업그레이드)
9. [오프라인·재현 가능한 설치](#9-오프라인재현-가능한-설치)
10. [문제 해결](#10-문제-해결)
11. [기술적 한계와 운영 시 주의사항](#11-기술적-한계와-운영-시-주의사항)
12. [개발 및 npm 배포](#12-개발-및-npm-배포)

---

## 1. 무엇을 해결하나요?

AI 코딩 에이전트로 작업하면 도구마다 계획서 형식이 다르거나, 테스트를 실행하지 않고 완료를 보고하거나, 다음 세션에서 이전 작업 상태를 파악하지 못하는 문제가 생길 수 있습니다.

이 프레임워크는 다음 목표를 갖습니다.

- **공통 작업 흐름:** 요구사항 분석 → 계획 → 사용자 승인 → 구현 → 검증 → 리뷰 → 최종 승인
- **외부 원본 스킬 재사용:** Matt Pocock, Superpowers, Ponytail의 스킬 파일을 원본 그대로 설치합니다. 자체 제작 대체 `analyze`/`plan`/`implement` 스킬을 만들지 않습니다.
- **증거 기반 검증:** 인수 조건(AC)에 연결된 실제 명령 실행 기록과 테스트 로그를 남깁니다.
- **세션 이어가기:** 새 세션에서 `active` 작업을 확인하여 진행 중인 작업을 이어갈 수 있게 돕습니다.
- **승인 경계 유지:** 구현 전 계획 승인과 최종 완료 승인은 사용자에게 있습니다. 에이전트가 임의로 승인했다고 간주하지 않아야 합니다.

```text
사용자 요청
   ↓
요구사항 분석 → 명세/AC → 실행 계획
                           ↓
                       사용자 계획 승인
                           ↓
                    구현 → AC별 검증 → 리뷰
                                              ↓
                                           사용자 완료 승인
                                              ↓
                      docs/exec-plans/completed/ 로 이동
```

**역할 구분:** 원본 스킬은 에이전트의 작업 방법을 돕고, 프로젝트 안의 `scripts/workflow.py`는 작업 상태와 검증 기록을 관리합니다. 스킬을 설치했다는 사실만으로 검증이 통과하거나 Hook이 활성화되는 것은 아닙니다.

## 2. 빠른 시작

### 준비 환경

- **Node.js 20 이상**과 npm/npx
- **Python 3**, **Git**
- OpenCode, Codex, Claude Code 중 사용할 에이전트
- 기본 설치 시 GitHub에 접속할 인터넷 환경

### 새 프로젝트에 설치

```bash
npx --yes @gon1942/ai-dev-external-framework@0.8.2 init my-project
cd my-project
```

`init`은 디렉터리가 없다면 생성하고 프로젝트 문서·상태 조회 파일·에이전트 설정·원본 외부 스킬 설치를 순서대로 시도합니다. 기본값은 `--agents all`입니다.

설치가 정상인지 먼저 확인합니다.

```bash
node .ai-dev/session-status.cjs
python3 scripts/workflow.py session

# 설치된 스킬 개수 확인
for dir in .agents .opencode .claude; do
  printf '%s: ' "$dir"
  find "$dir/skills" -name SKILL.md -type f 2>/dev/null | wc -l
done
```

각 에이전트를 모두 선택하고 18개 스킬 설치에 성공했다면 디렉터리별로 **18개**의 `SKILL.md`가 검색됩니다. 설치된 원본 저장소의 구성이나 다운로드 결과에 따라 실제 상태가 다를 수 있으므로 반드시 확인하세요.

그다음 프로젝트 폴더에서 평소 사용하는 에이전트를 실행합니다.

```bash
opencode
# 또는 codex
# 또는 claude
```

예시 요청: **“Todo CLI 기능을 만들어줘. 먼저 요구사항과 인수 조건, 구현 계획을 제시하고 승인받은 뒤 개발해.”**

### 기존 프로젝트에 적용

```bash
cd /path/to/existing-project
npx --yes @gon1942/ai-dev-external-framework@0.8.2 init .
```

기존 `AGENTS.md`가 있으면 보존합니다. 프레임워크 작업 지침이 자동 병합되지는 않으므로 설치 메시지와 파일 내용을 확인하세요. 관리 대상으로 취급되는 일부 파일이 이미 존재하며 내용이 다른 경우, 무단 덮어쓰기 대신 충돌 오류가 발생할 수 있습니다.

### 설치 미리보기

```bash
npx --yes @gon1942/ai-dev-external-framework@0.8.2 init my-project --dry-run
```

파일 변경과 원본 저장소 다운로드를 수행하지 않고 설치 예정 동작을 출력합니다. 새로 생성할 프로젝트라면 전체 파일 목록 대신 예상 동작만 표시될 수 있습니다.

## 3. 설치되는 구성 요소

대표적인 구조는 다음과 같습니다.

```text
my-project/
├── AGENTS.md                      # 세 에이전트에 적용할 공통 운영 지침
├── ARCHITECTURE.md                # 프로젝트 아키텍처 기록용 문서
├── docs/
│   ├── PLANS.md                   # 계획 및 작업 지침
│   ├── ai-workflow/               # 공통 정책
│   └── exec-plans/
│       ├── active/                # 현재 진행 중인 작업
│       └── completed/             # 최종 완료된 작업
├── scripts/
│   └── workflow.py                # 작업 상태·승인·AC 증거·완료 처리
├── .ai-dev/
│   ├── session-status.cjs         # 프로젝트 로컬 세션 상태 조회
│   ├── status-engine.cjs          # 상태 조회 처리 모듈
│   ├── spec-adapter.json          # Markdown/OpenSpec 연결 설정
│   └── verification-profiles.json # 파일 유형별 검증 프로파일
├── .agents/skills/               # Codex용 원본 스킬
├── .opencode/
│   ├── skills/                    # OpenCode용 원본 스킬
│   └── plugins/ai-dev-session.js  # 세션 이벤트용 플러그인 파일
├── .claude/
│   ├── skills/                    # Claude Code용 원본 스킬
│   └── settings.json              # 세션 시작 Hook 설정
├── .codex/hooks.json             # Codex용 Hook 설정 파일
└── .external-skills-lock.json    # 원본 리비전·파일 해시 기록
```

위 구조는 설치되는 주요 요소를 설명하기 위한 것입니다. 일부 폴더와 파일은 설치 옵션, 첫 작업 생성 여부에 따라 달라질 수 있습니다. `.agents/skills`는 이 프레임워크의 **Codex용 설치 대상 경로**입니다.

## 4. 외부 스킬 18개

아래는 현재 설치 프로그램의 **지정 목록**입니다. 실제 GitHub 원본에 같은 경로의 `SKILL.md`가 있어야 설치가 성공합니다. 원본 프로젝트의 향후 변경으로 설치가 실패할 수 있습니다.

### Matt Pocock — 8개

| 스킬 | 활용 목적 |
|---|---|
| `grill-with-docs` | 질문으로 요구사항과 누락 조건 구체화 |
| `diagnosing-bugs` | 버그 원인과 재현 조건 분석 |
| `to-spec` | 요구사항을 명세로 정리 |
| `to-tickets` | 명세를 실행 가능한 작업으로 분해 |
| `implement` | 정의된 작업의 구현 지원 |
| `implement-spec` | 명세에 근거한 구현 지원 |
| `code-review` | 코드 변경 사항 검토 |
| `retro` | 수행 결과 회고 |

출처: [mattpocock/skills](https://github.com/mattpocock/skills)

### Superpowers — 9개

| 스킬 | 활용 목적 |
|---|---|
| `brainstorming` | 구현 전에 문제와 설계 방향 구체화 |
| `writing-plans` | 구현 계획 구체화 |
| `systematic-debugging` | 체계적인 결함 추적 |
| `test-driven-development` | 실패 테스트 → 구현 → 개선 흐름 지원 |
| `using-git-worktrees` | 독립 작업 공간 활용 |
| `subagent-driven-development` | 하위 에이전트 작업 분담 |
| `verification-before-completion` | 완료 선언 전 실행 검증 |
| `requesting-code-review` | 리뷰 요청 |
| `receiving-code-review` | 리뷰 결과 확인 및 반영 |

출처: [obra/superpowers](https://github.com/obra/superpowers)

### Ponytail — 1개

| 스킬 | 활용 목적 |
|---|---|
| `ponytail` | 에이전트 개발 작업 보조 지침 |

출처: [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail)

**주의:** Ponytail은 이 패키지에서 **스킬 파일만 설치**합니다. 원본 Ponytail의 별도 플러그인, 실행 Hook, 모드 전환 등은 자동으로 활성화되지 않습니다. Superpowers나 다른 원본 저장소의 런타임 플러그인도 이 설치 도구가 자동으로 완성해 주는 것은 아닙니다.

## 5. 실제 개발 작업 흐름

사용자는 자연어로 요청하고, 에이전트가 프로젝트에 설치된 스킬과 로컬 `workflow.py`를 이용해 각 단계를 수행하는 방식입니다.

### ① 신규 작업과 계획

```bash
python3 scripts/workflow.py new --id TASK-TODO-CLI --title 'Todo CLI 개발'
```

다음과 같은 작업 디렉터리가 생성됩니다.

```text
docs/exec-plans/active/TASK-TODO-CLI/
├── analysis.md       # 분석 결과
├── spec.md           # 요구사항·인수 조건
├── plan.md           # 실행 계획
├── ac-tests.json     # AC별 검증 명령 등록
└── status.json       # 작업 상태
```

에이전트가 분석·명세·계획을 작성하고 사용자에게 승인 요청을 해야 합니다. 아래 승인 명령은 **실제 사용자 승인 이후에만** 실행해야 합니다.

```bash
python3 scripts/workflow.py approve --id TASK-TODO-CLI --user-confirmed
```

`--user-confirmed`는 에이전트가 사용자 승인이 있었다고 선언하는 플래그이지, 신원 인증이나 승인 사실을 자동 판별하는 기능이 아닙니다.

### ② 구현 및 검증

계획 승인 이후 구현을 시작합니다. 검증 전에 `ac-tests.json`에 AC별 실제 실행 명령을 등록해야 합니다.

```bash
python3 scripts/workflow.py gate --id TASK-TODO-CLI --stage implement
python3 scripts/workflow.py run --id TASK-TODO-CLI --ac AC-01 -- npm test
python3 scripts/workflow.py gate --id TASK-TODO-CLI --stage review
```

위 `npm test`는 **예시**입니다. 실제 프로젝트에 존재하는 테스트 명령이어야 하며 `ac-tests.json`에도 해당 명령이 등록되어 있어야 합니다. `run`은 실행 결과·로그·소스 상태를 검증 증거로 기록합니다.

### ③ 리뷰 및 최종 완료

```bash
# 리뷰 결과 문서를 작성한 후에 실행
python3 scripts/workflow.py review --id TASK-TODO-CLI --verdict PASS --notes-file review-notes.md

# 완료 조건 검사
python3 scripts/workflow.py gate --id TASK-TODO-CLI --stage complete

# 사용자가 최종 완료를 명시적으로 승인한 뒤에만 실행
python3 scripts/workflow.py complete --id TASK-TODO-CLI --user-confirmed
```

정상적으로 완료 처리된 작업은 `active/TASK-TODO-CLI/`에서 `completed/TASK-TODO-CLI/`로 이동합니다. **테스트 파일이나 리뷰 기록이 존재한다는 이유만으로 자동 이동하지 않습니다.** `review` 명령에 PASS를 기록하는 것과 실질적으로 독립적인 코드 리뷰를 수행했다는 것은 서로 다릅니다.

## 6. 새 세션 시작과 상태 확인

v0.8.1에서는 `AGENTS.md`가 `ai-dev status` 명령을 호출했지만, `npx`로 설치한 뒤에는 해당 명령이 PATH에 없어서 실패할 수 있었습니다.

**v0.8.2의 새 프로젝트 템플릿은 프로젝트 로컬 명령을 사용합니다.**

```bash
node .ai-dev/session-status.cjs
```

보다 자세한 작업 관리 상태는 다음 명령으로 확인할 수 있습니다.

```bash
python3 scripts/workflow.py session
python3 scripts/workflow.py session --json
```

세션 상태 조회는 **읽기 전용**입니다. 새 세션이 열렸다는 이유만으로 작업을 생성하거나, 승인 처리하거나, 테스트 완료로 표시하지 않습니다.

OpenCode 플러그인과 Claude/Codex Hook 설정 파일을 생성하지만, **각 호스트의 현재 버전에서 자동 실행되는지는 별도 확인이 필요**합니다. 특히 설정 파일이 있다는 사실만으로 실시간 Hook 동작이 검증된 것은 아닙니다.

## 7. CLI 명령어

패키지를 전역 설치하지 않아도 `npx`로 실행할 수 있습니다.

```bash
# 사용 가능한 명령 보기
npx --yes @gon1942/ai-dev-external-framework@0.8.2 --help

# 프로젝트 생성 + 설정 + 원본 외부 스킬 설치
npx --yes @gon1942/ai-dev-external-framework@0.8.2 init my-project

# 기존 프로젝트에 공통 설정·Hook 설치 (스킬 다운로드는 별도)
npx --yes @gon1942/ai-dev-external-framework@0.8.2 setup --project . --agents all

# 원본 스킬 별도 설치
npx --yes @gon1942/ai-dev-external-framework@0.8.2 install-skills --project . --agents all

# 상태 조회 (현재 프로젝트 지정)
npx --yes @gon1942/ai-dev-external-framework@0.8.2 status --project .

# 설치 파일 점검
npx --yes @gon1942/ai-dev-external-framework@0.8.2 doctor --project .

# 과거 AGENTS.md의 세션 명령 복구
npx --yes @gon1942/ai-dev-external-framework@0.8.2 repair-session --project .
```

| 명령 | 설명 | 참고 |
|---|---|---|
| `init <경로>` | 새/기존 프로젝트 초기화 및 원본 스킬 설치 | 권장 시작점 |
| `setup` | 문서·로컬 상태 조회 파일·Hook 설치 | 원본 스킬 다운로드 안 함 |
| `install-skills` | 원본 외부 스킬 다운로드·설치 | GitHub 또는 `--source-dir` 사용 |
| `status` | 현재 프로젝트의 작업 상태 요약 | 프로젝트 로컬 `node` 명령도 사용 가능 |
| `doctor` | 핵심 파일·스킬 디렉터리 존재 확인 | 실제 Hook 작동 여부까지 검증하지 않음 |
| `repair-session` | 구버전 `AGENTS.md`의 알려진 명령 수정 | 백업 생성, 기존 지침 보존 |
| `work ...` | 로컬 Python 작업 제어기로 인수 전달 | 에이전트 내부 사용에 적합 |

에이전트는 `opencode`, `codex`, `claude`를 평소대로 실행하면 됩니다. 별도의 `ai-dev` 전역 명령이 필수인 구조가 아닙니다.

## 8. 기존 프로젝트 업그레이드

### v0.8.1에서 새 세션 오류 복구

이미 설치한 프로젝트는 원본 외부 스킬을 다시 다운로드하지 않고 안내문만 복구할 수 있습니다.

```bash
cd /path/to/my-project

# 변경 예상 확인
npx --yes @gon1942/ai-dev-external-framework@0.8.2 repair-session --dry-run

# AGENTS.md의 알려진 구버전 명령 교체
npx --yes @gon1942/ai-dev-external-framework@0.8.2 repair-session

# 복구된 로컬 명령 직접 검증
node .ai-dev/session-status.cjs
```

`repair-session`은 `AGENTS.md`의 알려진 구버전 명령만 치환합니다. 변경 전 `AGENTS.md.pre-ai-dev-0.8.2.bak` 백업을 생성하며, 같은 이름의 백업이 이미 있으면 덮어쓰지 않습니다. **현재 파일에 로컬 상태 조회 실행 파일 자체가 없다면 `repair-session`만으로 복구할 수 없습니다.**

기존 프로젝트에 `AGENTS.md`가 이미 있었고 최초 설치 시 보존되었다면, 그 내용은 자동으로 프레임워크 지침과 합쳐지지 않습니다. 필요한 지침을 직접 비교·병합해야 합니다.

### 원본 스킬 갱신

```bash
npx --yes @gon1942/ai-dev-external-framework@0.8.2 install-skills --project . --agents all --update
```

이 명령은 프레임워크가 이전에 설치했고 이후 수정되지 않은 관리 대상에 한해 업데이트를 허용합니다. 직접 수정한 스킬 파일을 덮어쓰는 용도로 사용하지 마세요.

## 9. 오프라인·재현 가능한 설치

기본 설치는 GitHub의 당시 최신 리비전을 가져오므로 설치일이 다르면 스킬 내용도 달라질 수 있습니다.

### 오프라인 설치

```bash
npx --yes @gon1942/ai-dev-external-framework@0.8.2 init my-project \
  --source-dir /path/to/three-repos
```

`--source-dir`는 다음 디렉터리가 준비되어 있어야 합니다.

```text
/path/to/three-repos/
├── mattpocock/
├── superpowers/
└── ponytail/
```

각 소스는 설치 도구가 찾는 원본 `skills/**/<스킬명>/SKILL.md`를 포함해야 합니다. 또한 **패키지 자체를 npx가 처음 내려받는 과정은 별도**이므로, 완전 폐쇄망에서는 npm 패키지도 미리 확보해야 합니다.

### 원본 커밋 고정

팀이 같은 스킬을 쓰려면 공급자별 커밋 SHA를 지정할 수 있습니다.

```json
{
  "mattpocock": "<실제 40자리 커밋 SHA>",
  "superpowers": "<실제 40자리 커밋 SHA>",
  "ponytail": "<실제 40자리 커밋 SHA>"
}
```

위 `<...>` 값은 예시 자리표시자이므로 **실제 SHA로 교체한 뒤** 사용하세요.

```bash
npx --yes @gon1942/ai-dev-external-framework@0.8.2 init my-project --pins pins.json
```

설치 기록은 프로젝트 루트의 `.external-skills-lock.json`에 저장됩니다. 이 파일은 어떤 원본 리비전과 파일이 설치되었는지 추적하는 데 유용합니다.

## 10. 문제 해결

### `ai-dev: command not found`가 표시됩니다

`npx init`은 CLI를 전역 설치하지 않습니다. 프로젝트 루트에서 다음을 실행하세요.

```bash
node .ai-dev/session-status.cjs
```

`AGENTS.md`가 여전히 `ai-dev status`를 요구한다면 [기존 프로젝트 업그레이드](#8-기존-프로젝트-업그레이드)의 `repair-session`을 적용하세요.

### `npx` 실행 시 `E404`가 나옵니다

먼저 패키지 이름·버전·Registry를 확인하세요.

```bash
npm view @gon1942/ai-dev-external-framework@0.8.2 version \
  --registry=https://registry.npmjs.org/
npm config get registry
```

공개 npm Registry에 해당 버전이 실제로 게시되어 있지 않으면 설치할 수 없습니다. **이 README가 포함된 소스가 있다고 해서 npm 배포가 자동 완료되는 것은 아닙니다.**

### `Existing file differs` 또는 `Collision`이 나옵니다

기존 프로젝트 또는 스킬 디렉터리와 내용이 충돌한 경우입니다. 설치 도구는 기본적으로 덮어쓰지 않습니다. 파일을 백업하고 차이를 확인한 후 수동으로 조정하세요. 관리 대상 스킬의 안전한 갱신에는 `install-skills --update`를 사용할 수 있습니다.

### 설치는 되었는데 에이전트가 스킬을 사용하지 않습니다

파일 존재 여부부터 확인하세요.

```bash
find .agents/skills .opencode/skills .claude/skills -name SKILL.md -type f 2>/dev/null
```

스킬 파일 설치, 에이전트의 스킬 검색, 실제 스킬 호출은 서로 다른 단계입니다. 호스트별 스킬 활성화 방식과 플러그인 호환성을 확인해야 합니다.

### `completed/`로 이동하지 않습니다

AC 증거와 리뷰가 완료 Gate를 통과했는지 확인하세요.

```bash
python3 scripts/workflow.py gate --id TASK-TODO-CLI --stage complete
```

Gate 통과 뒤에도 사용자의 최종 완료 승인이 있어야 `complete --user-confirmed` 명령으로 이동합니다. 직접 `mv`로 옮기면 상태 관리 절차를 우회할 수 있습니다.

## 11. 기술적 한계와 운영 시 주의사항

- **원본 스킬 18개는 설치 대상 목록입니다.** 현재 원본 저장소에 모든 경로가 존재하고 각 에이전트가 스킬을 실제 호출할 수 있는지는 환경에서 확인해야 합니다.
- **Hook 실환경 동작은 보장되지 않습니다.** `.codex/hooks.json`, `.claude/settings.json`, `.opencode/plugins/`를 생성하지만 각 호스트의 지원 버전·권한·신뢰 설정에 따라 동작이 달라질 수 있습니다.
- **독립 리뷰의 진위는 자동으로 증명하지 못합니다.** 리뷰 PASS 기록과 실질적인 검토 품질은 구분해야 합니다.
- **테스트가 업무 요구를 충분히 검증하는지도 사람이 확인해야 합니다.** Gate는 명령 종료 코드·증거·소스 변경 여부 등의 구조적 조건을 검사합니다.
- **승인 플래그는 사용자의 신원을 인증하지 않습니다.** 사람의 명시적 승인 없이 에이전트가 `--user-confirmed`를 사용해서는 안 됩니다.
- **Ponytail 플러그인의 전체 기능은 설치하지 않습니다.** 원본 `ponytail` 스킬 파일만 설치합니다.
- **CRG(code-review-graph)는 별도 관리 대상**이며 이 패키지가 자동으로 설치하거나 활성화하지 않습니다.
- **`init`의 설치 후 상태 조회 자동 실행은 현재 구현에 포함되어 있지 않습니다.** 위 빠른 시작의 상태 조회 명령을 별도로 실행하여 점검하세요.
- 사용자의 명시적인 승인 없이 에이전트가 `commit`, `push`, `merge`하거나 정책/검증 게이트를 수정하지 않도록 운영해야 합니다.

## 12. 개발 및 npm 배포

이 저장소는 **npm 패키지 소스**입니다. npm에 공개하기 전 다음을 실행하세요.

```bash
npm test
npm run publish:check
npm pack --dry-run
```

배포 권한이 있는 npm 계정으로 로그인한 뒤:

```bash
npm login
npm publish --access public
```

패키지 이름은 `package.json`의 `@gon1942/ai-dev-external-framework`입니다. 동일한 **이름 + 버전 조합은 npm에 다시 배포할 수 없습니다.** README만 수정했더라도 이미 `0.8.2`를 게시했다면 버전을 올린 뒤 배포해야 합니다.

```bash
# 0.8.2가 이미 배포된 경우에만 다음 버전으로 변경
npm version patch --no-git-tag-version
npm test
npm run publish:check
npm publish --access public
```

배포된 버전 확인:

```bash
npm view @gon1942/ai-dev-external-framework version \
  --registry=https://registry.npmjs.org/
```

---

**핵심 원칙:** 외부 스킬은 *작업을 어떻게 할지* 돕고, 프레임워크는 *무엇이 승인·검증·완료됐는지* 기록합니다. **기록이 있는 것과 기능이 실제로 올바르게 동작하는 것은 구분하여 검증해야 합니다.**
