# AI Dev External Framework — 외부 스킬 기반 공통 개발 프레임워크

**OpenCode · Codex · Claude Code에서 동일한 개발 절차를 적용하기 위한 외부 스킬 기반 공통 프레임워크**

## 목차

1. [무엇을 해결하나요?](#1-무엇을-해결하나요)

2. [빠른 시작](#2-빠른-시작)

3. [설치되는 구성 요소](#3-설치되는-구성-요소)

4. [외부 원본 스킬 19개 + CRG + Playwright CLI + RTK (총 22개)](#4-외부-원본-스킬-19개--crg--playwright-cli--rtk-총-22개)

5. [개발 단계별 외부 스킬 활용 가이드](#5-개발-단계별-외부-스킬-활용-가이드)

6. [실제 개발 작업 흐름](#6-실제-개발-작업-흐름)

7. [새 세션 시작과 상태 확인](#7-새-세션-시작과-상태-확인)

8. [CLI 명령어](#8-cli-명령어)

9. [기존 프로젝트 업그레이드](#9-기존-프로젝트-업그레이드)

10. [중앙 스킬 관리 (스킬 정책)](#10-중앙-스킬-관리-스킬-정책)

11. [오프라인·재현 가능한 설치](#11-오프라인재현-가능한-설치)

12. [문제 해결](#12-문제-해결)

13. [기술적 한계와 운영 시 주의사항](#13-기술적-한계와-운영-시-주의사항)

14. [개발 및 npm 배포](#14-개발-및-npm-배포)

---

## 1. 무엇을 해결하나요?

AI 코딩 에이전트로 작업하면 도구마다 계획서 형식이 다르거나, 테스트를 실행하지 않고 완료를 보고하거나, 다음 세션에서 이전 작업 상태를 파악하지 못하는 문제가 생길 수 있습니다.

이 프레임워크는 다음 목표를 갖습니다.

기본 구성은 **외부 원본 스킬 19개(Matt Pocock 8개 + Superpowers 10개 + Ponytail 1개), CRG 1개, Playwright CLI 1개, RTK CLI 1개로 총 22개 구성 요소**입니다.

- **공통 작업 흐름:** 요구사항 분석 → 계획 → 사용자 승인 → 구현 → 검증 → 리뷰 → 최종 승인

- **외부 원본 스킬 재사용:** Matt Pocock, Superpowers, Ponytail의 스킬 파일을 원본 그대로 설치합니다. 자체 제작 대체 `analyze`/`plan`/`implement` 스킬을 만들지 않습니다.

- **중앙 스킬 정책:** 어떤 단계에 어떤 스킬을 쓸지 `skill-policy.json` 하나로 관리하고, 개발자 프로젝트에 동기화합니다.

- **증거 기반 검증:** 인수 조건(AC)에 연결된 실제 명령 실행 기록과 테스트 로그를 남깁니다.

- **세션 이어가기:** 새 세션에서 `active` 작업과 스킬 설치 현황을 확인하여 진행 중인 작업을 이어갈 수 있게 돕습니다.

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

- 기본 설치 시 GitHub·npm에 접속할 인터넷 환경

### 새 프로젝트에 설치

```bash

npx --yes @gon1942/ai-dev-external-framework\@latest init my-project

cd my-project

```

`init`은 디렉터리가 없다면 생성하고 프로젝트 문서·상태 조회 파일·에이전트 설정·원본 외부 스킬·CRG·Playwright CLI·중앙 스킬 정책을 순서대로 설치합니다. 기본값은 `--agents all`이며, CRG 제외는 `--skip-crg`, Playwright 제외는 `--skip-playwright`입니다.

설치가 정상인지 먼저 확인합니다.

```bash

# 읽기 전용 검사: 설치된 스킬 이름, 누락 목록, CRG·Playwright 상태

node .ai-dev/dependency-check.cjs

# 세션 시작 요약(의존성 + 활성 작업)

node .ai-dev/session-status.cjs

python3 scripts/workflow.py session

# 설치된 스킬 개수 확인 (19개 원본 + playwright-cli = 디렉터리별 20개)

for dir in .agents .opencode .claude; do

  printf '%s: ' "$dir"

  find "$dir/skills" -name SKILL.md -type f 2>/dev/null | wc -l

done

```

각 에이전트를 모두 선택하고 설치에 성공했다면 디렉터리별로 **20개**의 `SKILL.md`가 검색됩니다. 원본 저장소 구성·네트워크 상태에 따라 실제 결과는 다를 수 있으므로 반드시 확인하세요.

그다음 프로젝트 폴더에서 평소 사용하는 에이전트를 실행합니다.

```bash

opencode

# 또는 codex

# 또는 claude

```

예시 요청: **"Todo CLI 기능을 만들어줘. 먼저 요구사항과 인수 조건, 구현 계획을 제시하고 승인받은 뒤 개발해."**

### 기존 프로젝트에 적용

```bash

cd /path/to/existing-project

npx --yes @gon1942/ai-dev-external-framework\@latest init .

```

기존 `AGENTS.md`가 있으면 보존합니다. 프레임워크 작업 지침이 자동 병합되지는 않으므로 설치 메시지와 파일 내용을 확인하세요. 관리 대상으로 취급되는 일부 파일이 이미 존재하며 내용이 다른 경우, 무단 덮어쓰기 대신 충돌 오류가 발생할 수 있습니다.

### 설치 미리보기

```bash

npx --yes @gon1942/ai-dev-external-framework\@latest init my-project --dry-run

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

│   ├── dependency-check.cjs       # 원본 스킬 19개·CRG·Playwright 설치 검사 (읽기 전용)

│   ├── session-status.cjs         # 프로젝트 로컬 세션 상태 조회

│   ├── status-engine.cjs          # 상태 조회 처리 모듈

│   ├── skill-manager.cjs          # 프로젝트 로컬 스킬 정책 CLI

│   ├── skill-manager-engine.cjs   # 정책 관리 엔진

│   ├── stage-skills.json          # 중앙에서 동기화된 단계별 스킬 정책

│   ├── spec-adapter.json          # Markdown/OpenSpec 연결 설정

│   ├── verification-profiles.json # 파일 유형별 검증 프로파일

│   ├── crg-venv/                  # CRG Python 가상환경 (init 시 설치)

│   └── playwright/                # Playwright CLI 프로젝트 로컬 설치

├── .agents/skills/                # Codex용 원본 스킬

├── .opencode/

│   ├── skills/                    # OpenCode용 원본 스킬

│   ├── commands/skill-manager.md  # /skill-manager 명령 정의

│   └── plugins/ai-dev-session.js  # 세션 이벤트용 플러그인 파일

├── .claude/

│   ├── skills/                    # Claude Code용 원본 스킬

│   ├── commands/skill-manager.md  # /skill-manager 명령 정의

│   └── settings.json              # 세션 시작 Hook 설정

├── .codex/

│   ├── hooks.json                 # Codex용 Hook 설정 파일

│   └── prompts/skill-manager.md   # 스킬 관리 프롬프트

└── .external-skills-lock.json     # 원본 리비전·파일 해시 기록

```

위 구조는 설치되는 주요 요소를 설명하기 위한 것입니다. 일부 폴더와 파일은 설치 옵션, 첫 작업 생성 여부에 따라 달라질 수 있습니다. `.agents/skills`는 이 프레임워크의 **Codex용 설치 대상 경로**입니다.

### docs/ 디렉터리 안내

이 문서는 `@gon1942/ai-dev-external-framework\@latest`의 `init` 또는 `setup`으로 생성되는 프로젝트의 `docs/` 구조를 설명합니다. 설치 템플릿 원본 경로는 `templates/docs/`이며, 해당 내용이 설치 대상의 `docs/`로 복사됩니다.

### 폴더별 역할

| 경로 | 목적 | 포함 파일·작성 시점 |

|---|---|---|

| `ai-workflow/` | 에이전트 공통 작업 규칙 | `POLICY.md`에 사용자 승인·검증 증거·보안 원칙, `EXTERNAL-SKILLS.md`에 원본 스킬 참고 사항을 기록합니다. 작업 시작 전에 확인합니다. |

| `design-docs/` | 프로젝트 주요 설계 문서 | `index.md`로 중요한 설계 문서를 연결하고, `core-beliefs.md`에 설계 원칙을 정리합니다. 설계·구조 변경 시 작성합니다. |

| `exec-plans/` | 개별 개발 작업의 실행 근거 | 작업별 분석·명세·계획·실행 결과·리뷰 이력을 관리합니다. 공통 기술 부채는 `tech-debt-tracker.md`에 기록합니다. |

| `exec-plans/active/` | 진행 중 작업 | `workflow.py new` 이후 `TASK-ID/` 아래 `analysis.md`, `spec.md`, `plan.md`, `ac-tests.json`, `status.json` 등을 저장합니다. |

| `exec-plans/completed/` | 완료 작업의 보관 | 최종 사용자 승인과 완료 조건 충족 후 `workflow.py complete`가 처리한 작업을 보관합니다. |

| `generated/` | 생성·추출된 기술 문서 | 초기 `db-schema.md`는 자리표시자입니다. 실제 스키마를 추출·검증한 후 교체합니다. |

| `product-specs/` | 주요 제품 명세 색인 | `index.md`에서 주요 명세로 연결합니다. 작업별 정본 `spec.md`를 이곳에 중복 복제하지 않습니다. |

| `references/` | 외부 기술 참고자료 | `uv-llms.txt`, `nixpacks-llms.txt`, `design-system-reference-llms.txt`는 초기 자리표시자이므로 공식 최신 문서로 간주하지 않습니다. |

### docs/ 바로 아래 파일

| 파일 | 용도 |

|---|---|

| `PLANS.md` | 분석·계획 승인·구현·검증·리뷰·완료 흐름과 `workflow.py` 실행 규칙 |

| `DESIGN.md` | UI/UX 및 프로젝트 설계 제약을 정리할 기본 문서 |

| `FRONTEND.md` | 프런트엔드 구현 기준의 초기 문서 |

| `PRODUCT_SENSE.md` | 제품 목적과 사용자 가치에 대한 초기 문서 |

| `QUALITY_SCORE.md` | 품질 관점의 지표를 정리할 초기 문서 |

| `RELIABILITY.md` | 서비스 안정성과 운영 요구를 정리할 초기 문서 |

| `SECURITY.md` | 프로젝트 보안 요구를 정리할 초기 문서 |

이 문서들 중 일부는 초기 양식으로만 제공됩니다. 파일이 존재한다고 해당 기준이 이미 정의되거나 검증됐다는 뜻은 아닙니다.

### 작업 생성 후의 docs 구조와 파일별 역할

`docs/`는 모든 작업 문서를 한곳에 보관하지만, **프로젝트 공통 문서**와 **작업별 실행 기록**의 역할은 다릅니다.

- **프로젝트 공통 문서:** `ai-workflow/`, `design-docs/`, `generated/`, `product-specs/`, `references/` 및 `docs/` 루트의 기준 문서. `init` 또는 `setup` 시 템플릿이 배치됩니다.
- **개별 작업 문서:** `exec-plans/active/TASK-ID/`. 사용자 요청마다 `workflow.py new`로 생성되며 작업의 분석 → 계획 → 구현 → 검증 → 리뷰 → 완료 기록을 관리합니다.
- **완료 문서:** `exec-plans/completed/TASK-ID/`. 검증·리뷰 조건과 **사용자 최종 승인**을 충족한 뒤 이동합니다.

#### ① 프로젝트 설치 직후

```text
my-project/
└── docs/
    ├── PLANS.md                  # 작업 진행 절차와 workflow.py 운영 규칙
    ├── DESIGN.md                 # 프로젝트 설계·UI/UX 기준 (초기 양식)
    ├── FRONTEND.md               # 프런트엔드 기준 (초기 양식)
    ├── PRODUCT_SENSE.md          # 제품 목표·사용자 가치 (초기 양식)
    ├── QUALITY_SCORE.md          # 품질 평가 기준 (초기 양식)
    ├── RELIABILITY.md            # 안정성·운영 기준 (초기 양식)
    ├── SECURITY.md               # 보안 기준 (초기 양식)
    ├── ai-workflow/
    │   ├── POLICY.md             # 승인·검증·보안 공통 정책
    │   └── EXTERNAL-SKILLS.md    # 설치한 외부 스킬의 출처·사용 참고
    ├── design-docs/
    │   ├── index.md              # 주요 설계 문서 색인
    │   └── core-beliefs.md       # 설계 원칙 초안
    ├── exec-plans/
    │   ├── active/               # 진행 중인 작업 폴더
    │   ├── completed/            # 최종 완료된 작업 폴더
    │   └── tech-debt-tracker.md  # 작업과 별도로 추적할 기술 부채
    ├── generated/
    │   └── db-schema.md          # 초기에는 자리표시자; 생성 결과가 아님
    ├── product-specs/
    │   └── index.md              # 작업별 정식 명세를 찾는 링크
    └── references/               # 외부 기술 문서 참고 파일
```

**참고:** 위 루트 문서 중 일부는 기본 제목만 있는 빈 양식입니다. 해당 파일이 존재한다고 프로젝트 요구사항이 완성됐다는 의미는 아닙니다.

#### ② 새로운 개발 작업을 생성한 직후

예를 들어 사용자가 “로그인 기능을 개발해줘”라고 요청하면 에이전트가 아래 명령으로 작업을 생성합니다.

```bash
python3 scripts/workflow.py new --id TASK-LOGIN-001 --title '로그인 기능 개발'
```

이 명령을 실행하면 `docs/exec-plans/active/TASK-LOGIN-001/`에 **정확히 다음 다섯 파일이 초기 생성**됩니다.

```text
docs/exec-plans/
├── active/
│   └── TASK-LOGIN-001/
│       ├── analysis.md           # 현행 동작·문제·요구 분석
│       ├── spec.md               # 기능 요구사항과 인수 조건(AC)
│       ├── plan.md               # 구현 순서·영향 파일·검증 계획
│       ├── ac-tests.json         # AC별 실행할 테스트 명령 목록 (초기 {})
│       └── status.json           # 작업 ID·제목·생성 시각·승인/리뷰 상태
├── completed/
└── tech-debt-tracker.md
```

| 작업 파일 | 누가/언제 작성·갱신하는가 | 기록할 내용 |
| --- | --- | --- |
| `analysis.md` | **Analyze:** 에이전트가 작업 생성 후 작성 | 사용자 요청, 기존 코드 및 관련 기능 분석, 현행/기대 동작, 오류 재현 조건, 제약, 미확정 사항 |
| `spec.md` | **Analyze / Plan:** 계획 승인 전에 작성 | 구현 범위, 제외 범위, 기능 요구사항, 확인 가능한 인수 조건 `AC-01`, `AC-02` 등 |
| `plan.md` | **Plan:** 사용자 승인 전에 작성 | 변경할 파일·컴포넌트, 단계별 작업 순서와 의존성, 테스트 전략, 위험 및 롤백 고려사항 |
| `ac-tests.json` | **Plan:** 각 AC에 실제 실행할 테스트 명령을 등록 | AC 식별자별 허용 테스트 명령. 처음에는 `{}`이며, 승인·검증 전에 채워야 함 |
| `status.json` | **워크플로 명령이 생성·갱신** | 작업 식별자, 생성 시각, 승인 여부·시각, 리뷰 판정, 최종 완료 시각 등. 임의로 수정하지 않음 |

> `analysis.md`, `spec.md`, `plan.md`는 새 작업 생성 시 제목만 있는 **초기 파일**입니다. 생성됐다는 사실만으로 분석이나 계획이 완료된 것이 아닙니다.

#### ③ 구현·검증·리뷰를 진행한 이후

테스트와 리뷰를 실제 실행하면 작업 폴더에 **추가 파일 및 디렉터리**가 생길 수 있습니다.

```text
docs/exec-plans/active/TASK-LOGIN-001/
├── analysis.md
├── spec.md
├── plan.md
├── ac-tests.json
├── status.json
├── evidence.jsonl                  # 실제 테스트 실행별 증거 (최초 run 후 생성)
├── logs/                           # 실제 실행 출력 로그 (최초 run 후 생성)
│   ├── 20261027T000000000000Z-AC-01.log  # 파일명 예시
│   └── 20261027T000100000000Z-AC-02.log
└── reviews/                        # 리뷰 결과 등록 시 생성
    └── review-2026-10-27T00-10-00Z.md     # 파일명 예시
```

| 추가 기록 | 생성 시점 | 의미 |
| --- | --- | --- |
| `logs/*.log` | `workflow.py run`으로 명령을 실제 실행한 뒤 | 테스트 명령과 표준 출력·오류를 보관 |
| `evidence.jsonl` | `workflow.py run`이 최초 실행될 때 | AC 번호, 실행 명령, 종료 코드, 실행 시각, 로그 경로, 소스 지문 및 테스트 중 변경 여부 등을 JSON Lines로 누적 |
| `reviews/review-*.md` | `workflow.py review`에 리뷰 문서를 전달한 뒤 | 실제 검토 의견 파일을 작업 폴더로 복사해 보관 |
| `status.json` | `approve`, `review`, `complete` 명령 실행 시 | 승인·리뷰·완료 상태 갱신 |

`evidence.jsonl`과 `logs/`는 **작업 생성 직후에는 존재하지 않습니다.** 성공이든 실패든 테스트 명령을 실제 실행하고 나서 만들어집니다. `reviews/`도 리뷰 등록 이후 생성됩니다. 단순히 로그가 있다는 사실만으로 AC의 업무 요구 충족이 보장되지는 않습니다.

#### ④ 단계별 파일 사용 흐름

| 단계 | 주로 읽는 문서 | 작성·갱신하는 작업 파일 | 다음 단계로 넘어가기 위한 조건 |
| --- | --- | --- | --- |
| **Analyze** | `PLANS.md`, `ai-workflow/POLICY.md`, 기존 소스 | `analysis.md`, `spec.md` 초안 | 요구사항·현행 동작·재현 조건을 파악 |
| **Plan** | 분석 결과 및 관련 `design-docs/` | `spec.md`, `plan.md`, `ac-tests.json` | 인수 조건에 맞는 실행 명령을 정의하고 **사용자 계획 승인** 요청 |
| **Implement** | 승인된 명세·계획 | 애플리케이션 소스·테스트 코드, 필요 시 `plan.md` | 승인 후 `workflow.py gate --stage implement` 통과 |
| **Verify** | `spec.md`, `ac-tests.json` | `logs/`, `evidence.jsonl` | 등록된 명령의 실제 실행 결과와 AC별 적합성 확인 |
| **Review** | 변경 코드, 명세, 테스트 증거 | `reviews/`, `status.json` | 실질적 코드 리뷰를 수행하고 `workflow.py review`로 결과 등록 |
| **Complete** | 전체 작업 문서·증거·리뷰 | `status.json`, 이후 `completed/TASK-ID/` 이동 | 완료 게이트 통과 및 **사용자 최종 승인** |

작업 진행에 사용하는 대표 명령:

```bash
# 생성 이후 명세·계획·AC별 테스트 명령을 채우고 사용자 계획 승인 요청

# 사용자가 실제로 계획을 승인한 이후
python3 scripts/workflow.py approve --id TASK-LOGIN-001 --user-confirmed
python3 scripts/workflow.py gate --id TASK-LOGIN-001 --stage implement

# ac-tests.json에 해당 명령이 등록된 뒤 실제 실행
python3 scripts/workflow.py run --id TASK-LOGIN-001 --ac AC-01 -- npm test

# 증거를 검토한 후 리뷰 단계 확인
python3 scripts/workflow.py gate --id TASK-LOGIN-001 --stage review

# 검토 의견 파일을 작성하고 리뷰 등록
python3 scripts/workflow.py review --id TASK-LOGIN-001 --verdict PASS --notes-file review-notes.md

# 완료 게이트 확인 후 사용자 최종 승인을 받아 완료 처리
python3 scripts/workflow.py gate --id TASK-LOGIN-001 --stage complete
python3 scripts/workflow.py complete --id TASK-LOGIN-001 --user-confirmed
```

위의 `npm test`는 예시입니다. 실제로 프로젝트에 존재하고 해당 AC를 검증하는 명령으로 바꾸어 `ac-tests.json`에 등록해야 합니다. `--user-confirmed`는 실제 사용자 승인이 **이미 있었을 때만** 사용합니다.

#### ⑤ 완료 처리 후

완료 처리되면 동일한 작업 디렉터리가 이동합니다. 분석·명세·계획·테스트 증거·리뷰 기록은 해당 작업 폴더에 함께 유지됩니다.

```text
docs/exec-plans/
├── active/                          # 계속 진행 중인 다른 작업
└── completed/
    └── TASK-LOGIN-001/
        ├── analysis.md
        ├── spec.md
        ├── plan.md
        ├── ac-tests.json
        ├── status.json
        ├── evidence.jsonl
        ├── logs/
        └── reviews/
```

#### ⑥ 외부 스킬 사용 기록과 작업 문서의 관계

`using-superpowers`는 작업 성격에 맞는 원본 스킬을 확인하도록 돕는 스킬입니다. **현재 `workflow.py new`는 `skill-usage.json`을 만들지 않으며, `using-superpowers` 자체에도 작업 파일 자동 기록 기능은 없습니다.**

필요하면 향후 `skill-usage.json`(선택 스킬·선택 이유·실제 호출 근거)을 별도 기능으로 추가할 수 있으나, 현재는 에이전트의 자기 보고와 실제 스킬 호출 증거를 구분해야 합니다.

### 중복 관리 방지

- **작업별 명세 정본:** `exec-plans/active/TASK-ID/spec.md` (완료 후 `completed/TASK-ID/spec.md`)

- **프로젝트 공통 설계:** `design-docs/`

- **주요 명세의 목록·링크:** `product-specs/index.md`

- **자동 생성·검증된 기술 자료:** `generated/`

문서 파일 생성만으로 실제 외부 스킬 실행이나 검증 완료를 선언하지 마세요.

## 4. 외부 원본 스킬 19개 + CRG + Playwright CLI + RTK (총 22개)

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

출처: [mattpocock/skills](https\://github.com/mattpocock/skills)

### Superpowers — 10개

| 스킬 | 활용 목적 |

|---|---|

| `using-superpowers` | 요청·단계에 맞는 관련 스킬을 사전 탐색하고 적용 순서를 판단하도록 안내하는 메타 스킬 |
| `brainstorming` | 구현 전에 문제와 설계 방향 구체화 |

| `writing-plans` | 구현 계획 구체화 |

| `systematic-debugging` | 체계적인 결함 추적 |

| `test-driven-development` | 실패 테스트 → 구현 → 개선 흐름 지원 |

| `using-git-worktrees` | 독립 작업 공간 활용 |

| `subagent-driven-development` | 하위 에이전트 작업 분담 |

| `verification-before-completion` | 완료 선언 전 실행 검증 |

| `requesting-code-review` | 리뷰 요청 |

| `receiving-code-review` | 리뷰 결과 확인 및 반영 |

출처: [obra/superpowers](https\://github.com/obra/superpowers)

### Ponytail — 1개

| 스킬 | 활용 목적 |

|---|---|

| `ponytail` | 에이전트 개발 작업 보조 지침 |

출처: [DietrichGebert/ponytail](https\://github.com/DietrichGebert/ponytail)

**주의:** Ponytail은 이 패키지에서 **스킬 파일만 설치**합니다. 원본 Ponytail의 별도 플러그인, 실행 Hook, 모드 전환 등은 자동으로 활성화되지 않습니다. Superpowers나 다른 원본 저장소의 런타임 플러그인도 이 설치 도구가 자동으로 완성해 주는 것은 아닙니다.

### Code Review Graph(CRG) — 20번째 구성 요소

| 구성 요소 | 역할 | 구분 |

|---|---|---|

| **`code-review-graph` (CRG)** | 코드 구조·호출 관계·의존성·변경 영향 분석을 지원 | **Python CLI + MCP + 코드 그래프** (일반 스킬과 별도) |

출처: [tirth8205/code-review-graph](https\://github.com/tirth8205/code-review-graph)

- CRG는 `.ai-dev/crg-venv`에 설치하며, 공식 설치 명령을 통해 지원 에이전트의 MCP·스킬 연결을 시도합니다. 프레임워크의 자체 `AGENTS.md`·세션 Hook을 덮어쓰지 않도록 CRG Hook·지침 설치는 제외합니다.

- **CLI 설치 확인 → MCP 연결 확인 → 그래프 생성·조회 성공**은 각각 다른 단계입니다. 설치 기록만으로 실제 MCP 분석 가능 상태라고 말하지 않습니다.

- 빈 프로젝트는 분석할 코드가 없어 `init` 시점에 그래프를 자동 구축하지 않습니다. 코드가 준비된 뒤 빌드합니다.

```bash

# CRG 설치 상태 확인

cat .ai-dev/crg-install.json

.ai-dev/crg-venv/bin/code-review-graph --help

# 소스코드가 준비된 후 실행

.ai-dev/crg-venv/bin/code-review-graph build

.ai-dev/crg-venv/bin/code-review-graph status

```

### Playwright CLI — 21번째 구성 요소

Microsoft 공식 **Playwright CLI + `playwright-cli` 스킬**을 기본 설치 구성에 포함합니다. 웹 UI 변경 시 **VERIFY 단계의 조건부 도구**(conditional)로, 실제 브라우저 열기·탐색·사용자 시나리오 확인에 사용합니다.

- 신규 프로젝트 `init`은 Playwright CLI를 `.ai-dev/playwright` 하위에 프로젝트별 설치하고, 공식 스킬을 `.agents/skills`, `.claude/skills`에 배치한 뒤 OpenCode용으로 `.opencode/skills`에 복사합니다. 기존 파일은 자동 덮어쓰지 않습니다.

- 런타임 설치는 인터넷 연결과 npm 패키지 다운로드가 필요하며, 오류 발생 시 `init`은 실패를 보고합니다.

- **설치와 실제 검증은 다릅니다.** 브라우저 바이너리가 준비되어야 실제 화면 검증을 수행할 수 있습니다. CLI 사용법은 `playwright-cli --help`를 확인하고, 브라우저·OS 종속성은 공식 설치 안내에 따라 준비하세요.

- 로그인·데이터 삭제 등 파괴적 시나리오는 별도 승인 후 수행하며, 화면 캡처만으로 AC 테스트 통과를 선언하지 않습니다. Playwright Test 통합 및 증거 Gate 자동 연결은 별도 개발 대상입니다.

공식 출처: https\://playwright.dev/agent-cli/installation , https\://playwright.dev/agent-cli/skills

```bash

# 기존 프로젝트에 Playwright만 설치

npx --yes @gon1942/ai-dev-external-framework\@latest install-playwright --project . --agents all

# 프로젝트 내부 실행 파일 사용

.ai-dev/playwright/node_modules/.bin/playwright-cli --help

```

### RTK — 22번째 구성 요소

[rtk-ai/rtk](https://github.com/rtk-ai/rtk) 공식 **RTK CLI**를 기본 설치 구성에 포함합니다. 에이전트가 읽는 셸 명령 출력(git·pytest·npm·ls 등 100+ 명령)을 자동으로 압축해 토큰 사용을 60-90% 줄입니다. **실패 라인은 보존**되므로 AC 검증 증거가 손실되지 않습니다.

- `init`은 공식 install 스크립트를 **다운로드 후 실행**해(원격 파이프 없음) 사용자 머신의 `~/.local/bin`에 Rust 바이너리를 설치하고, `rtk init -g` / `--opencode` / `--codex`로 에이전트별 훅을 등록합니다. 바이너리가 이미 있으면 재다운로드하지 않습니다.

- OpenCode 플러그인은 **1.18.29+**가 필요하며, 미만이면 경고만 출력합니다. Windows는 `winget install rtk-ai.rtk` 수동 설치 후 재실행하세요.

- Claude Code의 `settings.json` 훅 패치는 비대화 모드에서 자동 적용되지 않으므로 `rtk init`이 출력하는 스니펫을 1회 수동 적용합니다.

- 텔레메트리는 **기본 OFF**입니다. 개별 명령의 원본 출력이 필요하면 `rtk bypass <cmd>`를 사용하고, 절감 통계는 `rtk gain`으로 확인합니다.

- 라이선스: CLI는 Apache-2.0(내부 엔진 BUSL-1.1, 프로덕션 사용 무료). 본 프레임워크는 공식 배포판을 다운로드만 하며 재배포하지 않습니다. `rtk-proxy` 데몬은 구성에서 제외했습니다.

```bash
# 기존 프로젝트에 RTK만 설치
npx --yes @gon1942/ai-dev-external-framework@latest install-rtk --project . --agents all
```

## 5. 개발 단계별 외부 스킬 활용 가이드

이 표는 **프레임워크에 설치되는 19개 원본 스킬과 CRG·Playwright의 권장 활용 위치**를 정리한 운영 가이드입니다. **현재 코드가 모든 단계에서 해당 스킬을 자동 선택·강제 호출한다는 뜻은 아닙니다.** 에이전트는 사용자 요청, 설치 여부, 원본 스킬의 사용 조건에 따라 필요한 스킬을 선택합니다. 스킬 간 역할이 겹치면 모두 실행할 필요는 없습니다. 단계별 배정은 [중앙 스킬 정책](#10-중앙-스킬-관리-스킬-정책)으로 관리됩니다.

### using-superpowers: 단계별 스킬 선택 절차

1. 사용자 요청과 현재 작업 단계(Analyze, Plan, Implement, Verify, Review, Complete)를 확인합니다.
2. `using-superpowers`를 사용할 수 있다면 해당 스킬을 로드하고, 현재 설치된 원본 스킬 및 `.ai-dev/stage-skills.json`의 단계별 사용 정책을 확인합니다.
3. 비활성화된 스킬을 제외하고 필요한 스킬을 선택합니다. 하나의 단계에서 모든 후보를 사용할 필요는 없습니다.
4. 사용 예정 스킬과 실제 호출한 스킬을 구분해 사용자 및 작업 기록에 남깁니다. **원본 스킬만으로 자동 작업 로그가 생성되지는 않습니다.**
5. 검증 결과는 `workflow.py`의 실제 명령 실행·AC 기록으로 따로 확인합니다. 스킬 호출 여부가 검증 PASS를 의미하지 않습니다.

**적용 범위:** OpenCode `.opencode/skills/using-superpowers/SKILL.md`, Codex `.agents/skills/using-superpowers/SKILL.md`, Claude Code `.claude/skills/using-superpowers/SKILL.md`. 에이전트별 파일 존재, 스킬 인식, 실제 호출은 각각 별도 확인이 필요합니다.

### 5.1 단계별 권장 조합

| 단계 | 우선 고려할 외부 스킬 | 필요할 때 추가할 스킬/도구 | 기대 결과 |

|---|---|---|---|

| **분석 (Analyze)** | `using-superpowers`로 후보 검토 후 `grill-with-docs`, `brainstorming`, `to-spec` | 버그: `diagnosing-bugs`, `systematic-debugging`; 코드 구조: **CRG** | 요구사항, 재현 조건, 범위, AC 초안 |

| **계획 (Plan)** | `writing-plans`, `to-tickets` | `using-git-worktrees`, `subagent-driven-development` | 작업 분해, 순서·의존성, 파일 변경 범위, 검증 명령 |

| **구현 (Implement)** | `implement-spec` 또는 `implement`, `test-driven-development` | `subagent-driven-development`, `using-git-worktrees`, `ponytail` | 요구사항에 맞는 소스 변경, 실패 테스트 확인 및 구현 |

| **검증 (Verify)** | `verification-before-completion`, `test-driven-development` | 웹 UI: **Playwright CLI**; 실패 분석: `systematic-debugging`, `diagnosing-bugs`; 영향 범위: **CRG** | 실제 테스트 로그, AC별 PASS/FAIL 근거 |

| **리뷰 (Review)** | `code-review`, `requesting-code-review`, `receiving-code-review` | 의존관계·영향도 검토: **CRG** | 리뷰 의견, 수정 사항, 재검증 근거 |

| **종료·개선 (Complete)** | `retro` | 완료 Gate: `scripts/workflow.py` | 회고, 최종 승인 기록, `completed/` 이동 |

**구분:** CRG는 CLI·프로젝트 그래프·MCP 연결을 이용하는 코드 분석 도구이고, Playwright CLI는 브라우저 실행 도구입니다. 둘 다 일반 스킬 19개와 같은 단일 `SKILL.md` 구성이 아닙니다. `ponytail`은 보조 스킬 파일이며, 별도 플러그인/Hook 기능까지 자동 활성화되는 것은 아닙니다.

### 5.2 작업 유형별 사용 예시

| 사용자 요청 예시 | 권장 흐름 | 핵심 도구 |

|---|---|---|

| "신규 기능을 만들어줘" | 요구 분석 → 명세·AC → 계획 승인 → TDD 구현 → 검증 → 리뷰 | `to-spec` → `writing-plans` → `implement-spec` + `test-driven-development` → `verification-before-completion` → `code-review` |

| "기존 버그를 수정해줘" | 재현·원인 분석 → 수정 계획 → 회귀 테스트 → 검증 | `diagnosing-bugs` / `systematic-debugging` → `writing-plans` → `test-driven-development` → `verification-before-completion` |

| "대규모 리팩터링을 해줘" | 구조·의존성 파악 → 작업 분해 → 격리 구현 → 영향 검증 | **CRG** → `to-tickets` + `writing-plans` → `using-git-worktrees` / `subagent-driven-development` → `code-review` |

| "변경한 코드를 검토해줘" | 리뷰 요청 → 코드·영향도 분석 → 피드백 반영 → 재검증 | `requesting-code-review` → `code-review` + **CRG(선택)** → `receiving-code-review` → `verification-before-completion` |

| "웹 UI가 실제로 동작하는지 확인해줘" | 시나리오 정의 → 브라우저 실행 → 결과 기록 | **Playwright CLI** → `verification-before-completion` |

### 5.3 각 단계의 적용 원칙

1. **분석:** 요구사항이 불명확하면 `grill-with-docs`나 `brainstorming`으로 먼저 확인합니다. 기존 결함이라면 재현과 근본 원인 파악을 우선합니다.

2. **계획:** `to-spec`은 **무엇을 만들지**, `writing-plans`는 **어떻게 구현·검증할지**, `to-tickets`는 **어떤 단위로 나눌지**에 초점을 둡니다. 실행 계획과 AC별 테스트 명령을 프로젝트 작업 파일에 기록합니다.

3. **구현:** `implement`와 `implement-spec`은 작업 성격에 따라 선택합니다. 테스트 가능한 동작 변경은 `test-driven-development`의 RED → GREEN → REFACTOR 흐름을 고려하되, 테스트 실행 기록 없이 RED/GREEN을 완료했다고 보고하지 않습니다.

4. **검증:** 스킬이 '완료'라고 평가하는 것만으로 Gate가 통과하지 않습니다. `scripts/workflow.py run` 등으로 실제 테스트를 실행하고, 명세의 AC와 일치하는 증거를 남깁니다. 실행 환경과 프로젝트 언어에 맞는 명령을 사용합니다.

5. **리뷰:** `code-review`는 리뷰 작업의 방법을 돕고, CRG는 호출 가능할 때 코드 관계·영향도 근거를 제공합니다. CRG 설치 기록이 있어도 **MCP 연결·그래프 생성·실제 질의 성공 여부는 별도로 확인**해야 합니다.

6. **완료:** 스킬 사용 여부와 무관하게 리뷰·검증 Gate를 통과하고 **사용자의 최종 승인**을 받은 뒤에만 `completed/`로 이동합니다. `retro`는 선택적인 개선 활동입니다.

### 5.4 에이전트에 요청하는 예시

```text

현재 프로젝트에서 요청한 기능을 공통 개발 절차로 진행해줘.
각 단계 시작 전에 `using-superpowers`를 사용 가능한지 확인하고, 단계별 스킬 정책에 맞는 후보를 검토해줘.

1. Analyze: 요구사항과 기존 코드를 분석하고 적합한 원본 스킬을 선택해줘.

   코드 의존성 확인이 필요하면 CRG 사용 가능 여부부터 점검해줘.

2. Plan: Spec, AC, 작업 분해 및 검증 명령을 작성하고 내 승인을 받아줘.

3. Implement: 승인된 계획에 따라 구현하고 필요한 테스트를 먼저 실행해줘.

4. Verify: AC별 테스트를 실제 실행하고 로그와 PASS/FAIL 근거를 남겨줘.

   웹 UI 변경이면 Playwright CLI로 실제 브라우저 동작을 확인해줘.

5. Review: 변경 사항을 검토하고 리뷰 의견 및 재검증 결과를 남겨줘.

6. 완료: 내 최종 승인 전에는 completed 상태로 이동하지 마.

각 단계에서 실제로 사용한 스킬과 호출한 도구를 보고해줘.

```

---

## 6. 실제 개발 작업 흐름

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

## 7. 새 세션 시작과 상태 확인

v0.8.1에서는 `AGENTS.md`가 `ai-dev status` 명령을 호출했지만, `npx`로 설치한 뒤에는 해당 명령이 PATH에 없어서 실패할 수 있었습니다. **현재 템플릿은 프로젝트 로컬 명령을 사용합니다.**

```bash

# 읽기 전용 검사: 설치된 스킬 이름, 누락 목록, CRG·Playwright 상태

node .ai-dev/dependency-check.cjs

# 세션 시작 요약(의존성 + 활성 작업)

node .ai-dev/session-status.cjs

# 보다 자세한 작업 관리 상태

python3 scripts/workflow.py session

python3 scripts/workflow.py session --json

```

v0.9.0부터 세션 시작 시 **세 에이전트별 설치·미설치 원본 스킬 이름, CRG·Playwright 설치 상태, 활성 작업**을 안내문에 표시하도록 안내합니다.

**보고 예:** `OpenCode 19/19`, `Codex 19/19`, `Claude 19/19`, `CRG: 설치 확인(MCP 미검증)`, `Playwright: 설치`, `누락: 없음`, `활성 작업: 0건`. 이는 예시로, 실제 현황은 검사를 실행하여 확인해야 합니다. 에이전트가 지침을 생략하면 사용자 메시지에 모두 표시되지 않을 수 있으므로 위 로컬 명령으로 확인하세요.

- 설치 누락이 발견돼도 세션 조회 자체는 **읽기 전용**이며 파일을 변경하지 않습니다. 새 세션이 열렸다는 이유만으로 작업을 생성하거나, 승인 처리하거나, 테스트 완료로 표시하지 않습니다.

- 미설치 항목 복구는 에이전트가 권한에 따라 별도로 실행합니다.

```bash

# 미설치 항목만 복구 (별도 실행; 필요 시 네트워크/Python 사용)

npx --yes @gon1942/ai-dev-external-framework\@latest repair-deps --project . --agents all

```

OpenCode 플러그인과 Claude/Codex Hook 설정 파일을 생성하지만, **각 호스트의 현재 버전에서 자동 실행되는지는 별도 확인이 필요**합니다. 특히 설정 파일이 있다는 사실만으로 실시간 Hook 동작이 검증된 것은 아닙니다.

## 8. CLI 명령어

패키지를 전역 설치하지 않아도 `npx`로 실행할 수 있습니다.

```bash

# 사용 가능한 명령 보기

npx --yes @gon1942/ai-dev-external-framework\@latest --help

# 프로젝트 생성 + 설정 + 원본 외부 스킬 설치

npx --yes @gon1942/ai-dev-external-framework\@latest init my-project

# 기존 프로젝트에 공통 설정·Hook 설치 (스킬 다운로드는 별도)

npx --yes @gon1942/ai-dev-external-framework\@latest setup --project . --agents all

# 원본 스킬 별도 설치

npx --yes @gon1942/ai-dev-external-framework\@latest install-skills --project . --agents all

# 원본 스킬 + CRG + Playwright 설치 상태 확인 (읽기 전용)

npx --yes @gon1942/ai-dev-external-framework\@latest check-deps --project .

# 누락 항목만 설치·복구

npx --yes @gon1942/ai-dev-external-framework\@latest repair-deps --project . --agents all

# CRG / Playwright 개별 설치·재시도

npx --yes @gon1942/ai-dev-external-framework\@latest install-crg --project . --agents all

npx --yes @gon1942/ai-dev-external-framework\@latest install-playwright --project . --agents all

# 상태 조회 / 설치 파일 점검

npx --yes @gon1942/ai-dev-external-framework\@latest status --project .

npx --yes @gon1942/ai-dev-external-framework\@latest doctor --project .

# 기존 v0.8.x 프로젝트의 세션 보고 지침 갱신

npx --yes @gon1942/ai-dev-external-framework\@latest upgrade-session-report --project .

# 과거 AGENTS.md의 세션 명령 복구

npx --yes @gon1942/ai-dev-external-framework\@latest repair-session --project .

```

| 명령 | 설명 | 참고 |

|---|---|---|

| `init <경로>` | 새/기존 프로젝트 초기화 및 원본 스킬·CRG·Playwright·정책 설치 | 권장 시작점, `--skip-crg`/`--skip-playwright` 가능 |

| `setup` | 문서·로컬 상태 조회 파일·Hook·스킬 관리 명령 설치 | 원본 스킬 다운로드 안 함 |

| `install-skills` | 원본 외부 스킬 다운로드·설치 | GitHub 또는 `--source-dir` 사용 |

| `check-deps` | 스킬·CRG·Playwright 설치 상태 및 누락 항목 조회 | 읽기 전용 |

| `repair-deps` | 누락 스킬·CRG·Playwright만 복구 시도 | 네트워크/권한 필요 |

| `install-crg` | CRG 설치·재시도 | Python 환경 필요 |

| `install-playwright` | Playwright CLI·공식 스킬 설치 | npm 네트워크 필요 |

| `upgrade-session-report` | 기존 프로젝트의 세션 보고 구성 갱신 | 백업 생성 |

| `status` | 현재 프로젝트의 작업 상태 요약 | 프로젝트 로컬 `node` 명령도 사용 가능 |

| `doctor` | 핵심 파일·스킬 디렉터리 존재 확인 | 실제 Hook 작동 여부까지 검증하지 않음 |

| `repair-session` | 구버전 `AGENTS.md`의 알려진 명령 수정 | 백업 생성, 기존 지침 보존 |

| `skill ...` | 중앙 스킬 정책 관리 (목록·배정·동기화 등) | [중앙 스킬 관리](#10-중앙-스킬-관리-스킬-정책) 참고 |

| `work ...` | 로컬 Python 작업 제어기로 인수 전달 | 에이전트 내부 사용에 적합 |

에이전트는 `opencode`, `codex`, `claude`를 평소대로 실행하면 됩니다. 별도의 `ai-dev` 전역 명령이 필수인 구조가 아닙니다.

## 9. 기존 프로젝트 업그레이드

### v0.8.1에서 새 세션 오류 복구

이미 설치한 프로젝트는 원본 외부 스킬을 다시 다운로드하지 않고 안내문만 복구할 수 있습니다.

```bash

cd /path/to/my-project

# 변경 예상 확인

npx --yes @gon1942/ai-dev-external-framework\@latest repair-session --dry-run

# AGENTS.md의 알려진 구버전 명령 교체

npx --yes @gon1942/ai-dev-external-framework\@latest repair-session

# 복구된 로컬 명령 직접 검증

node .ai-dev/session-status.cjs

```

`repair-session`은 `AGENTS.md`의 알려진 구버전 명령만 치환합니다. 변경 전 `AGENTS.md.pre-ai-dev-0.8.2.bak` 백업을 생성하며, 같은 이름의 백업이 이미 있으면 덮어쓰지 않습니다. **현재 파일에 로컬 상태 조회 실행 파일 자체가 없다면 `repair-session`만으로 복구할 수 없습니다.**

기존 프로젝트에 `AGENTS.md`가 이미 있었고 최초 설치 시 보존되었다면, 그 내용은 자동으로 프레임워크 지침과 합쳐지지 않습니다. 필요한 지침을 직접 비교·병합해야 합니다.

### v0.8.4 이하 프로젝트에 세션 보고·의존성 검사 반영

```bash

cd /path/to/my-project

npx --yes @gon1942/ai-dev-external-framework\@latest upgrade-session-report --dry-run

npx --yes @gon1942/ai-dev-external-framework\@latest upgrade-session-report

node .ai-dev/session-status.cjs

```

이 명령은 기존 `AGENTS.md`와 검사 스크립트의 변경 전 파일을 백업(`.pre-ai-dev-0.8.5.bak`)하고, 보고 기능만 갱신합니다. 외부 스킬·CRG를 재설치하거나 작업 상태를 변경하지 않습니다. 빠진 항목이 있다면 `repair-deps`를 별도로 실행합니다.

### 누락된 관리 명령·정책 파일 추가

기존 설치 프로젝트에 `/skill-manager` 명령 파일과 `.ai-dev/skill-manager.cjs`가 없다면 `setup`으로 추가할 수 있습니다. 기존 파일 내용이 달라 설치 충돌이 있을 수 있으므로 먼저 `--dry-run`으로 확인하세요.

```bash

npx --yes @gon1942/ai-dev-external-framework\@latest setup --project . --agents all --dry-run

npx --yes @gon1942/ai-dev-external-framework\@latest setup --project . --agents all

```

### v1.0.1: using-superpowers 추가 후 설치 확인

기존 설치에서 `18/18`로 표시되거나 미설치 목록에 `using-superpowers`가 전혀 나오지 않는다면 **구버전 검사 스크립트**일 수 있습니다. 새 설치는 아래처럼 패키지 버전을 명확히 지정합니다. `@`만 붙이고 버전을 생략하지 않습니다.

```bash
npx --yes @gon1942/ai-dev-external-framework@1.0.1 init my-project --agents all
cd my-project
node .ai-dev/dependency-check.cjs

for dir in .opencode .agents .claude; do
  test -f "$dir/skills/using-superpowers/SKILL.md" && echo "PASS: $dir" || echo "FAIL: $dir"
done

node .ai-dev/skill-manager.cjs dashboard
```

정상 설치 시 원본 스킬 검사 결과는 **OpenCode·Codex·Claude 각각 19/19**, 별도 도구까지 포함한 전체 구성은 **19개 원본 + CRG + Playwright CLI + RTK CLI = 22개**입니다. 브라우저 스킬 파일까지 포함하면 에이전트별 `SKILL.md`는 통상 **20개**입니다. 스킬 파일 존재와 에이전트에서 실제 호출 가능한지는 구분해야 합니다.

### 원본 스킬 갱신

```bash

npx --yes @gon1942/ai-dev-external-framework\@latest install-skills --project . --agents all --update

```

이 명령은 프레임워크가 이전에 설치했고 이후 수정되지 않은 관리 대상에 한해 업데이트를 허용합니다. 직접 수정한 스킬 파일을 덮어쓰는 용도로 사용하지 마세요.

## 10. 중앙 스킬 관리 (스킬 정책)

### 10.1 정책 구조

프레임워크 관리자는 배포 소스의 `skill-policy.json`을 **단일 기준(SSOT)**으로 관리합니다. 개발자 프로젝트는 이 정책을 `.ai-dev/stage-skills.json`으로 동기화받아 사용합니다.

- 6개 단계(`analyze`, `plan`, `implement`, `verify`, `review`, `complete`)별로 스킬을 배정하고 사용 모드(`required`/`recommended`/`optional`/`conditional`)를 지정합니다.

- 임의 GitHub 스킬은 **고정된 40자리 Git 커밋 SHA**로 등록해야 하며, 원본 디렉터리의 `SKILL.md`를 그대로 복사합니다.

- CRG는 `kind: crg`, Playwright는 `kind: playwright`인 특수 구성 요소로 관리되며 일반 `SKILL.md` 스킬과 구분됩니다.

- 활성 단계 정책은 외부 스킬 사용 **후보**를 제시합니다. 실제 에이전트가 해당 스킬을 사용했는지는 실행 증거를 별도로 확인해야 합니다.

### 10.2 관리자 워크플로 (프레임워크 배포 소스에서)

대화형 관리자를 사용합니다. 단계/스킬을 번호로 선택하고 변경 내용을 확인한 뒤 `yes`로 승인합니다. 스킬 ID를 외우지 않아도 됩니다.

```bash

./manage-skills.sh

# 또는

node bin/ai-dev.js skill manage

```

비대화형 CLI도 같은 엔진(`lib/skill-manager.js`)을 사용합니다.

```bash

node bin/ai-dev.js skill list

node bin/ai-dev.js skill dashboard          # 6개 단계 현재 배정 한눈에 보기

node bin/ai-dev.js skill add custom-review https\://github.com/ORG/REPO.git 0123456789abcdef0123456789abcdef01234567 skills/custom-review

node bin/ai-dev.js skill stage add review custom-review recommended

node bin/ai-dev.js skill stage remove review requesting-code-review

node bin/ai-dev.js skill stage replace plan writing-plans to-tickets

node bin/ai-dev.js skill disable ponytail   # 모든 단계에서 사용 불가 (중앙 승인 필요)

node bin/ai-dev.js skill validate

```

에이전트(OpenCode/Codex/Claude Code)에서 자연어로 관리할 수도 있습니다. 저장소 루트의 `AGENTS.md`와 `framework-skill-admin` 스킬이 같은 CLI를 사용하도록 안내합니다.

\> 중앙 스킬 정책을 보여줘. Verify 단계의 스킬을 비교하고 교체 후보를 추천해줘. 변경하기 전 승인받고, 승인 후 공통 관리 명령으로 반영해줘.

변경 전 정책을 `skill-policy.json.bak`으로 백업합니다. 백업은 마지막 변경 1회분이므로 장기 이력은 Git으로 관리하세요.

**규칙:** `add`는 **등록**이고 `stage add`는 **단계별 사용 정책 배정**입니다. `stage remove`는 사용 정책에서 제외하는 것일 뿐 설치 파일 삭제가 아닙니다. `disable`은 모든 단계에서 사용 불가 처리하므로 중앙 승인 후 사용합니다. 원본 스킬의 임의 변경이나 정책의 무단 수정을 금지합니다.

정책 변경 후 배포 전 검증:

```bash

node bin/ai-dev.js skill validate

npm test

npm run publish:check

# 관리자 승인 후 package.json 버전 상승 및 npm publish

```

### 10.3 개발자 프로젝트에 승인된 정책 적용

```bash

# 신규 설치는 설치본의 정책을 자동 복사

npx --yes @gon1942/ai-dev-external-framework\@latest init my-project

# 기존 프로젝트는 새 버전의 승인 정책을 동기화

cd my-project

npx --yes @gon1942/ai-dev-external-framework\@latest skill sync --project . --dry-run

npx --yes @gon1942/ai-dev-external-framework\@latest skill sync --project . --install-custom

npx --yes @gon1942/ai-dev-external-framework\@latest skill show-stage review

```

**제한 사항:** `skill sync`는 승인된 단계별 정책 파일과 등록된 사용자 Git 스킬의 누락 설치를 반영합니다. 기존 19개 원본 스킬과 CRG를 대체하거나 제거하는 전체 생명주기 관리, 타사 MCP 연결의 자동 검증, 개별 에이전트별 동작 보장은 아직 구현되지 않았습니다. 프레임워크 배포 버전을 지정해야 중앙 정책이 동일하게 유지됩니다. 프로젝트 정책의 수동 변경은 해시 검사에서 차단하며, 기존 정책은 `.bak`으로 백업됩니다.

### 10.4 프로젝트 로컬 관리 명령

`init`/`setup`은 프로젝트에 `/skill-manager` 명령(`.opencode/commands/`, `.claude/commands/`, `.codex/prompts/`)과 로컬 CLI를 생성합니다.

```bash

node .ai-dev/skill-manager.cjs dashboard

node .ai-dev/skill-manager.cjs validate

node .ai-dev/skill-manager.cjs stage list verify

```

로컬 변경은 사용자가 명시적으로 승인한 경우에만 `--yes`로 실행합니다. 로컬 정책 변경은 중앙 팀 정책과 별개이며, 팀 전체에 반영하려면 소스의 중앙 정책을 변경해 npm 새 버전으로 배포해야 합니다.

## 11. 오프라인·재현 가능한 설치

기본 설치는 GitHub의 당시 최신 리비전을 가져오므로 설치일이 다르면 스킬 내용도 달라질 수 있습니다.

### 오프라인 설치

```bash

npx --yes @gon1942/ai-dev-external-framework\@latest init my-project \\

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

npx --yes @gon1942/ai-dev-external-framework\@latest init my-project --pins pins.json

```

설치 기록은 프로젝트 루트의 `.external-skills-lock.json`에 저장됩니다. 이 파일은 어떤 원본 리비전과 파일이 설치되었는지 추적하는 데 유용합니다.

## 12. 문제 해결

### `ai-dev: command not found`가 표시됩니다

`npx init`은 CLI를 전역 설치하지 않습니다. 프로젝트 루트에서 다음을 실행하세요.

```bash

node .ai-dev/session-status.cjs

```

`AGENTS.md`가 여전히 `ai-dev status`를 요구한다면 [기존 프로젝트 업그레이드](#9-기존-프로젝트-업그레이드)의 `repair-session`을 적용하세요.

### `npx` 실행 시 `E404`가 나옵니다

먼저 패키지 이름·버전·Registry를 확인하세요.

```bash

npm view @gon1942/ai-dev-external-framework\@latest version \\

  --registry=https\://registry.npmjs.org/

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

### CRG 그래프 조회가 실패합니다

CLI 설치, MCP 연결, 그래프 생성·조회는 별개 단계입니다. `.ai-dev/crg-venv/bin/code-review-graph status`로 현재 상태를 확인하고, 필요하면 `build`를 다시 실행하세요.

### `completed/`로 이동하지 않습니다

AC 증거와 리뷰가 완료 Gate를 통과했는지 확인하세요.

```bash

python3 scripts/workflow.py gate --id TASK-TODO-CLI --stage complete

```

Gate 통과 뒤에도 사용자의 최종 완료 승인이 있어야 `complete --user-confirmed` 명령으로 이동합니다. 직접 `mv`로 옮기면 상태 관리 절차를 우회할 수 있습니다.

## 13. 기술적 한계와 운영 시 주의사항

- **원본 스킬 19개는 설치 대상 목록입니다.** 현재 원본 저장소에 모든 경로가 존재하고 각 에이전트가 스킬을 실제 호출할 수 있는지는 환경에서 확인해야 합니다.

- **Hook 실환경 동작은 보장되지 않습니다.** `.codex/hooks.json`, `.claude/settings.json`, `.opencode/plugins/`를 생성하지만 각 호스트의 지원 버전·권한·신뢰 설정에 따라 동작이 달라질 수 있습니다.

- **독립 리뷰의 진위는 자동으로 증명하지 못합니다.** 리뷰 PASS 기록과 실질적인 검토 품질은 구분해야 합니다.

- **테스트가 업무 요구를 충분히 검증하는지도 사람이 확인해야 합니다.** Gate는 명령 종료 코드·증거·소스 변경 여부 등의 구조적 조건을 검사합니다.

- **승인 플래그는 사용자의 신원을 인증하지 않습니다.** 사람의 명시적 승인 없이 에이전트가 `--user-confirmed`를 사용해서는 안 됩니다.

- **Ponytail 플러그인의 전체 기능은 설치하지 않습니다.** 원본 `ponytail` 스킬 파일만 설치합니다.

- **CRG·Playwright는 설치와 실행 가능이 다릅니다.** CRG는 MCP 연결·그래프 빌드 성공을 별도 확인해야 하고, Playwright는 브라우저 바이너리가 준비되어야 실제 화면 검증이 가능합니다.

- **스킬 정책은 사용 후보 관리입니다.** 단계 배정·활성화 정책이 에이전트의 실제 스킬 호출을 강제·증명하지는 않습니다.

- **`init`의 설치 후 상태 조회 자동 실행은 현재 구현에 포함되어 있지 않습니다.** 위 빠른 시작의 상태 조회 명령을 별도로 실행하여 점검하세요.

- 사용자의 명시적인 승인 없이 에이전트가 `commit`, `push`, `merge`하거나 정책/검증 게이트를 수정하지 않도록 운영해야 합니다.

## 14. 개발 및 npm 배포

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

패키지 이름은 `package.json`의 `@gon1942/ai-dev-external-framework\@latest`입니다. 동일한 **이름 + 버전 조합은 npm에 다시 배포할 수 없습니다.** README만 수정했더라도 이미 해당 버전을 게시했다면 버전을 올린 뒤 배포해야 합니다.

```bash

# 같은 버전이 이미 배포됐다면 버전을 올린 뒤 게시

npm version patch --no-git-tag-version

npm test

npm run publish:check

npm publish --access public

```

배포된 버전 확인:

```bash

npm view @gon1942/ai-dev-external-framework\@latest version \\

  --registry=https\://registry.npmjs.org/

```

---

**핵심 원칙:** 외부 스킬은 **작업을 어떻게 할지** 돕고, 프레임워크는 **무엇이 승인·검증·완료됐는지** 기록합니다. **기록이 있는 것과 기능이 실제로 올바르게 동작하는 것은 구분하여 검증해야 합니다.**
