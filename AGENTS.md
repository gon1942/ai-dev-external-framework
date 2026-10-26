# AI Dev External Framework — 중앙 스킬 관리 소스

이 디렉터리는 일반 개발 프로젝트가 아니라 **공통 프레임워크 관리자 소스**이다.

관리자 요청(스킬 목록, 신규 도입, 단계별 배정/제외/교체/비활성화)을 받으면 다음을 따른다.

1. `node bin/ai-dev.js skill list`로 `skill-policy.json` 정본을 읽고 Analyze/Plan/Implement/Verify/Review/Complete 배정을 보여준다.
2. 변경 요청 시 기존 스킬과의 중복·단계 영향·원본 출처/라이선스/커밋 SHA·에이전트 호환성을 검토한다.
3. 변경 전 구체적인 CLI와 영향 내용을 제시하고 **사람의 명시적 승인**을 기다린다.
4. 승인 뒤 `node bin/ai-dev.js skill ...` 명령을 실행한다. 정책 파일을 임의로 직접 편집하지 않는다.
5. `node bin/ai-dev.js skill validate`, `npm test`, `npm run publish:check` 결과를 보고한다. 실행하지 않은 검증은 주장하지 않는다.
6. npm publish, commit/push는 사용자가 명시적으로 요청/승인했을 때만 실행한다.
7. `stage remove`는 사용 정책에서만 제외한다. 설치 파일 삭제나 배포는 별도 작업이다.

독립 대화형 관리자는 `./manage-skills.sh` 또는 `node bin/ai-dev.js skill manage`로 실행한다. 에이전트는 대화형 입력을 자동화하지 않고 **같은 `lib/skill-manager.js` 엔진을 사용하는 비대화형 CLI**를 호출한다.

## 간편 스킬 관리
사용자가 "스킬 관리", "스킬 관리자", `/skill-manager`를 요청하면 `node bin/ai-dev.js skill dashboard`로 단계별 목록을 먼저 보여주고, 승인 후 동일한 CLI 엔진으로 변경한다.
