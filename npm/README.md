# Team AI Dev Framework — npm/npx bootstrap

**Node.js 20+, Python 3.10+ 필요**. Python 엔진 WHL을 npm 패키지에 동봉해 `pip install` 수동 작업 없이 프로젝트 전용 `.ai-dev/.runtime/`에 설치합니다. Python 본체는 별도 설치가 필요합니다. npm 저장소에는 **아직 게시하지 않았습니다**.

```bash
# 신규 프로젝트
npx --yes @gon1942/team-ai-dev-framework@0.19.0 init my-project

# 기존 Team AI Dev 프로젝트 업그레이드 — 기본 미리보기
npx --yes @gon1942/team-ai-dev-framework@0.19.0 upgrade --project .
npx --yes @gon1942/team-ai-dev-framework@0.19.0 upgrade --project . --apply

# 기존 다른 프레임워크 없는 프로젝트에 비파괴 설치
npx --yes @gon1942/team-ai-dev-framework@0.19.0 adopt --project . --apply

# 실행 및 검사
npx --yes @gon1942/team-ai-dev-framework@0.19.0 doctor --project .
npx --yes @gon1942/team-ai-dev-framework@0.19.0 cli --project . -- startup
```

## 주의

- `@gon1942/team-ai-dev-framework`는 **새로운 패키지명 제안**입니다. 패키지 소유자의 npm 게시 전에는 원격 `npx` 명령이 작동하지 않습니다. 배포 전에는 로컬 npm tarball로 시험하세요.
- 기존 `ai-dev-external-framework`의 `scripts/workflow.py`, `.ai-dev/stage-skills.json` 등이 있으면 자동 교체하지 않고 중단합니다. 두 프레임워크는 상태 스키마가 달라 단순 `upgrade`로 이전할 수 없습니다.
- `upgrade`는 기본적으로 미리보기만 제공하며 실제 파일 변경에는 `--apply`가 필요합니다.
- 모델 설치·API 인증·Python 설치·Git 상태 공유는 자동화하지 않습니다.
- `teamdev`를 `PATH` 전역 명령으로 설치하지 않습니다. npm CLI의 `cli --project . -- <command>`를 사용하세요.
- `.ai-dev/.runtime/`은 로컬 전용이며 Git에 포함하지 않습니다.
- `--apply` 시 각 업그레이드의 독립적인 안전 검사가 동작하며, 여러 명령을 묶은 전체 롤백은 아직 지원하지 않습니다. 실행 전 Git 상태와 백업을 확인하세요.

### Worker 보고서 JSON 사전검사 (v0.19.1)

`team-ai-dev cli --project . -- report-template TASK-ID --output docs/tasks/TASK-ID/implementer-input.json`로 입력용 JSON 템플릿을 만들고, 실제 증거를 입력한 후 `report-check`를 수행하세요. `report.md`는 CLI 입력이 아닙니다. 기존 Team AI Dev 프로젝트에는 `upgrade --project . --apply` 실행 시 `upgrade-report-contract`가 적용됩니다. 기존 다른 개발 프레임워크의 상태 자동 이관은 지원하지 않습니다.
