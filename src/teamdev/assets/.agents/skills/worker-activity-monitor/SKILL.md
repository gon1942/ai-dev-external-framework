---
name: worker-activity-monitor
description: Observe workflow task state and cooperative worker activity without assuming the next worker action is actually running.
---

# Worker activity monitor

1. Use `teamdev --root . monitor --task TASK-ID` or `monitor --watch`.
2. When native worker invocation *actually starts*, record `teamdev worker-start TASK --role ROLE --session-id UNIQUE`. Do not emit start for planned or merely instructed work.
3. Record `worker-heartbeat` only for actual observed activity and `worker-stop` on observed completion/error; never fabricate status.
4. `teamdev report` / `verify` / `review` are still required for workflow advancement, independent of telemetry.
5. Activity telemetry does not prove an agent is thinking, does not bypass approval, and never replaces original logs.
