---
name: framework-skill-admin
description: Manage central AI Dev External Framework skill registry and stage assignments after human approval.
---

# Framework Skill Admin

Use from the **framework source repository**, not arbitrary downstream projects. Read root `AGENTS.md` and `skill-policy.json`. First show current stages using `node bin/ai-dev.js skill list`; compare changes and ask human approval. After approval, use `node bin/ai-dev.js skill add|disable|enable|stage ...`. Verify with `node bin/ai-dev.js skill validate`, `npm test`. Never publish or delete installed skills without explicit approval. Never claim CRG MCP operational merely from a registry entry.

사용자가 "스킬 관리자" 또는 "스킬 관리"라고 말하면 `node bin/ai-dev.js skill dashboard`로 시작한다. `node bin/ai-dev.js skill dashboard`를 실행하여 **모든 단계의 전체 목록**을 보여준다.
