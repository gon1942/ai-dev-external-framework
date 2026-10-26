---
description: AI Dev 공통 프레임워크 스킬 관리자 (프로젝트 로컬)
---
현재 프로젝트 루트에서 `node .ai-dev/skill-manager.cjs dashboard`를 실행하고 전체 단계별 스킬 목록을 사용자에게 보여줘.

- 추가/제외/교체 요청은 해당 단계의 기존 구성과 변경 후 구성을 먼저 제시하고 명시적 승인을 받아야 한다.
- 승인 뒤에만 `node .ai-dev/skill-manager.cjs stage add|remove|replace|mode ... --yes`를 실행하고 `node .ai-dev/skill-manager.cjs validate`로 검증한다.
- 프로젝트 내부 `.ai-dev/stage-skills.json`만 변경한다. 이 작업은 중앙 npm 프레임워크에 배포되지 않는다.
- 팀 전체의 중앙 정책을 변경하려면 공통 프레임워크 **소스 저장소**에서 기존 중앙 CLI로 변경하고 새 npm 버전으로 배포해야 한다. 일반 프로젝트에서 중앙 정책을 수정했다고 보고하지 않는다.
- 설치 상태 확인은 `node .ai-dev/dependency-check.cjs`로 수행한다. CRG 및 Playwright의 실제 사용 가능성은 별도 검사한다.
