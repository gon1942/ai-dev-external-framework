---
name: verification-before-completion
description: Framework-authored, offline-distributable verify procedure (verification-before-completion); not the upstream third-party skill.
---

# verification-before-completion — TeamDev integrated equivalent

**Provenance:** Original Team AI Dev Framework integration authored for common offline distribution. This is **NOT** a copy of an upstream external skill with the same name.

## Trigger

Use only when the approved task type and current stage make the procedure relevant. Loading a SKILL.md is not proof of execution.

## Procedure

Independently rerun the planned checks; save raw complete logs with command, exit code and environment; inspect expected behavior and negative cases; report PASS/FAIL/BLOCKED/NOT_RUN honestly; never treat agent self-report as independent evidence.

## Evidence / limitations

Record invocation to the task with `teamdev skill-record` and a genuine evidence file where available. Don't fabricate an executed-tool claim or an unrun test. Follow the framework's plan and completion approval gates.
