---
name: evidence-driven-verification
description: Verify outcomes with commands, exit codes and original evidence
---

# evidence-driven-verification

Follow AGENTS.md and docs/WORKFLOW.md. Use this skill only when the current task needs its expertise.

1. Confirm AC-to-test mapping for each requirement.
2. Run tests/lint/typecheck and other necessary project commands rather than relying on claims.
3. Keep the original output and execution environment. The RTK summary is supplementary only.
4. Distinguish FAIL, BLOCKED, NOT_RUN and PASS. Exit code alone may not prove AC coverage.
5. Report discovered risk, changed artifact hashes and missing coverage.
