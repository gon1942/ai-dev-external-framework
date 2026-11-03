---
name: tdd-workflow
description: Execute task-type TDD or approved alternative verification, preserving RED/GREEN/REFACTOR evidence.
---
# Task-Type TDD

Read TASK state.json tdd and approved plan. For required types, create a failing test **before production changes**, execute it and confirm the intended failure (not syntax/environment failure); implement minimal code; rerun to GREEN; review refactor and run regression. Save original command output and actual exit codes as evidence/red.log, green.log, refactor.log. For ui_visual, configuration, refactoring use approved alternative checks; for documentation use document validation, with raw logs.

Produce evidence/tdd-manifest.json per docs/TDD-POLICY.md and include manifest plus all logs in worker-report evidence. Use `teamdev tdd-check TASK-ID` before submitting. No fabricated test executions, no bypass of approval; not all work requires TDD but all requires verification. Coordinator sets type before plan approval.
