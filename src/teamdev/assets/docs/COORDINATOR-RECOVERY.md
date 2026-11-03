# Orca Coordinator Session Recovery

## Orca Coordinator Session Recovery (v0.16)

- Keep TASK, worktree, approvals and evidence stable. Only the **main Coordinator model conversation** changes; do not spawn another Coordinator as a subagent.
- At a safe stage boundary (or when context pressure is detected), ensure any native Worker call has actually returned and its monitoring record is stopped. Then use `teamdev coordinator-handoff TASK --session-id CURRENT --next-action "one next action" --reason "context pressure"`.
- This command freezes `teamdev next`, native Worker registration and CLI Worker execution for that TASK while PREPARED. The freeze is enforced by cooperating `teamdev` commands, not by Orca or direct file writes.
- In Orca, open a **fresh main Coordinator conversation** in the same project/worktree. Do not resume the old context or have both conversations advance the same TASK.
- After confirming the old Coordinator is inactive, from the NEW session call `teamdev coordinator-resume TASK --new-session-id NEW --old-session-stopped`. The flag is an operator/agent assertion, **not** an independent process-liveness check.
- Read the short `docs/tasks/TASK/coordinator-handoff.md`, run `teamdev startup`, `teamdev status TASK`, `teamdev next TASK` and verify approvals and Worker ownership before dispatch.
- No fictional token percentage: checkpoint at real phase boundaries or contextual pressure. No automatic Orca window creation/clearing is claimed. `teamdev coordinator-session TASK` shows PREPARED/RESUMED state.
- Handoffs preserve original logs externally; never paste secrets, transcript dumps or raw logs into the handoff file. Do not commit or push without separate user approval.
