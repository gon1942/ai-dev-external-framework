# docs/ 디렉터리 안내

이 문서는 `@gon1942/ai-dev-external-framework`의 `init` 또는 `setup`으로 생성되는 프로젝트의 `docs/` 구조를 설명합니다. 설치 템플릿 원본 경로는 `templates/docs/`이며, 해당 내용이 설치 대상의 `docs/`로 복사됩니다.

## 폴더별 역할

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

## docs/ 바로 아래 파일

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

## 작업 생성 후의 구조 예시

```text
my-project/
└── docs/
    ├── README.md
    ├── PLANS.md
    ├── DESIGN.md, FRONTEND.md, PRODUCT_SENSE.md, QUALITY_SCORE.md, RELIABILITY.md, SECURITY.md
    ├── ai-workflow/
    │   ├── POLICY.md
    │   └── EXTERNAL-SKILLS.md
    ├── design-docs/
    │   ├── index.md
    │   └── core-beliefs.md
    ├── exec-plans/
    │   ├── active/
    │   │   └── TASK-001/
    │   │       ├── analysis.md
    │   │       ├── spec.md
    │   │       ├── plan.md
    │   │       ├── ac-tests.json
    │   │       └── status.json
    │   ├── completed/
    │   └── tech-debt-tracker.md
    ├── generated/
    │   └── db-schema.md
    ├── product-specs/
    │   └── index.md
    └── references/
```

`TASK-001/`은 초기 설치 직후부터 있는 폴더가 아니라 아래 명령으로 작업을 생성한 후 생기는 예시입니다.

```bash
python3 scripts/workflow.py new --id TASK-001 --title '기능 개발'
```

에이전트는 `docs/PLANS.md`, `docs/ai-workflow/POLICY.md` 및 해당 작업 문서를 기준으로 업무를 진행합니다. 구현 전 계획 승인과 완료 전 최종 승인 여부는 문서의 존재만으로 보장되지 않습니다.

## 중복 관리 방지

- **작업별 명세 정본:** `exec-plans/active/TASK-ID/spec.md` (완료 후 `completed/TASK-ID/spec.md`)
- **프로젝트 공통 설계:** `design-docs/`
- **주요 명세의 목록·링크:** `product-specs/index.md`
- **자동 생성·검증된 기술 자료:** `generated/`

문서 파일 생성만으로 실제 외부 스킬 실행이나 검증 완료를 선언하지 마세요.
