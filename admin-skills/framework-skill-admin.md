---
name: framework-skill-admin
description: 사용자 승인 후 중앙 AI Dev External Framework 스킬 목록과 단계별 배정을 관리한다.
---

# 공통프레임워크 스킬 관리자

이 지침은 **공통프레임워크 소스 저장소에서만** 사용하며 일반 설치 프로젝트에는 적용하지 않는다. 루트 `AGENTS.md`와 `skill-policy.json`을 읽는다. `node bin/ai-dev.js skill list`로 현재 단계별 목록을 먼저 보여주고 변경 영향을 비교한 뒤 사용자 승인을 요청한다. 승인한 경우에만 `node bin/ai-dev.js skill add|disable|enable|stage ...`로 수정한다. `node bin/ai-dev.js skill validate` 및 `npm test`로 검증한다. 별도 승인 없이 배포하거나 설치된 스킬을 삭제하지 않는다. 중앙 목록에 CRG가 있다는 사실만으로 MCP가 실제 연결됐다고 주장하지 않는다. RTK는 설치 기록(`.ai-dev/rtk-install.json`)과 실제 바이너리·훅 동작을 구분해 보고하며, 텔레메트리가 기본 OFF임을 유지한다.
