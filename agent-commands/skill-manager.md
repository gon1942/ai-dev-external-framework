# 공통 프레임워크 스킬 관리자

사용자가 `/skill-manager` 또는 "스킬 관리"를 요청하면 이 저장소 루트에서 시작한다.

1. `node bin/ai-dev.js skill dashboard`를 실행하여 **모든 단계의 전체 목록**을 보여준다.
2. 관리할 단계와 변경 유형(추가/제외/교체/사용 정책 변경/활성화)을 자연어로 받는다. 이미 명확히 지정한 내용은 재질문하지 않는다.
3. 변경 전후 및 영향을 요약한다. 사용자의 **명시적 승인 전에는 변경하지 않는다**.
4. 승인 후 반드시 `node bin/ai-dev.js skill stage ...` 혹은 `node bin/ai-dev.js skill ...` CLI를 사용한다. `skill-policy.json`을 직접 편집하지 않는다.
5. `node bin/ai-dev.js skill validate`를 실행하고 성공/실패를 보고한다. npm 배포·커밋은 별도 승인 필요.

중앙 정책에서 스킬을 제외하는 것은 물리적 삭제가 아니다. CRG 등록은 실제 MCP 연결의 증거가 아니다.
