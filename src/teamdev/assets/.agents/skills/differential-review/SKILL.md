---
name: differential-review
description: Framework-authored, offline-distributable review procedure (differential-review); not the upstream third-party skill.
---

# differential-review — TeamDev integrated equivalent

**Provenance:** Original Team AI Dev Framework integration authored for common offline distribution. This is **NOT** a copy of an upstream external skill with the same name.

## Trigger

Use only when the approved task type and current stage make the procedure relevant. Loading a SKILL.md is not proof of execution.

## Procedure

Review patch/diff against baseline for changed trust boundaries, sensitive data access, dependency changes and privilege escalation. Require concrete before/after evidence and explicit severity/uncertainty.

## Evidence / limitations

Record invocation to the task with `teamdev skill-record` and a genuine evidence file where available. Don't fabricate an executed-tool claim or an unrun test. Follow the framework's plan and completion approval gates.
