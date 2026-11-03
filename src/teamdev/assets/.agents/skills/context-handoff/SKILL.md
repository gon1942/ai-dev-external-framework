---
name: context-handoff
description: Create a minimal, source-linked handoff between workers and rotate long-running worker conversations without losing task ownership.
---
# Context Handoff
Before dispatch, include authoritative spec, approved plan and the exact TASK/worktree paths. Do not dump the full conversation. During long tasks call `teamdev rotate-request` as documented in `docs/SESSION-ROTATION.md`. Return `CONTEXT_HANDOFF_REQUIRED TASK-ID`, never worker_done. The Coordinator validates with `rotate-resume` only after the old worker stops. A new worker gets TASK ID, task folder, handoff path and one next action; verifies source and Git state before proceeding. Raw evidence stays in docs/tasks/<TASK>/evidence/, not in handoff; never include tokens or full logs.
