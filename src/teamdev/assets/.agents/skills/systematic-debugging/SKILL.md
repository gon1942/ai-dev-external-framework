---
name: systematic-debugging
description: Framework-authored, offline-distributable analyze procedure (systematic-debugging); not the upstream third-party skill.
---

# systematic-debugging — TeamDev integrated equivalent

**Provenance:** Original Team AI Dev Framework integration authored for common offline distribution. This is **NOT** a copy of an upstream external skill with the same name.

## Trigger

Use only when the approved task type and current stage make the procedure relevant. Loading a SKILL.md is not proof of execution.

## Procedure

Reproduce the failure, collect exact commands and stderr/stdout, isolate first incorrect assumption, test a falsifiable root-cause hypothesis, implement smallest fix only after approval, add a regression test; avoid speculative multi-file edits.

## Evidence / limitations

Record invocation to the task with `teamdev skill-record` and a genuine evidence file where available. Don't fabricate an executed-tool claim or an unrun test. Follow the framework's plan and completion approval gates.
