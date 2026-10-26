---
name: framework-skill-admin
description: Manage central AI Dev External Framework skill registry and stage assignments after human approval.
---

# Framework Skill Admin

Use from the **framework source repository**, not arbitrary downstream projects. Read root `AGENTS.md` and `skill-policy.json`. First show current stages using `node bin/ai-dev.js skill list`; compare changes and ask human approval. After approval, use `node bin/ai-dev.js skill add|disable|enable|stage ...`. Verify with `node bin/ai-dev.js skill validate`, `npm test`. Never publish or delete installed skills without explicit approval. Never claim CRG MCP operational merely from a registry entry.
