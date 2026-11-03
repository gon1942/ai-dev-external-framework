# TASK Activity Monitor (v0.5)

`teamdev monitor --watch` shows workflow state and worker activity separately.

- `teamdev monitor`: all local tasks
- `teamdev monitor --task TASK-ID`: one task
- `teamdev monitor --watch --interval 3`: keep refreshing
- `teamdev monitor --json`: machine-readable snapshot

Native subagent telemetry is cooperative: when actually launching a role, issue
`teamdev worker-start TASK --role implementer|verifier|reviewer --session-id UNIQUE`,
then `teamdev worker-heartbeat TASK --session-id UNIQUE` on genuine activity,
and `teamdev worker-stop TASK --session-id UNIQUE --status FINISHED|FAILED|STOPPED`
only on actual completion. No worker start/heartbeat means `UNTRACKED`, not `RUNNING`.

The CLI `teamdev drive --execute` emits driver-activity heartbeats automatically.
They reflect a pending CLI process, **not** the LLM's token-level health.
Never infer test PASS or final approval from telemetry.

## Coordinator Progress Reporting (v0.14)

- Run `teamdev progress --task TASK-ID` at meaningful transitions: after PLAN is ready (before requesting approval), after confirmed Worker dispatch, after Worker return, after VERIFY/REVIEW result recording, before final user approval, and after COMPLETE archive. Also show `teamdev progress` at SESSION start when tasks exist.
- Present a concise human-readable status: TASK, stage, workflow status, Worker / observed activity, stage pipeline, user action, and next execution. Report FAIL / BLOCKED immediately.
- Show actual monitored facts, not fabricated progress percentages. `RECENT_ACTIVITY` from heartbeat is not proof of a live native Worker or of successful verification. Never call `worker-start` before confirmed dispatch or `worker-stop` before confirmed return.
- Do not poll `teamdev monitor` inside a synchronous native Task call. During long runs the human may use a separate terminal: `teamdev monitor --watch --interval 3`. Only report genuine new progress on real events, not repetitive messages.
- Preserve both explicit human approval gates. Progress display must never auto-approve, advance workflow, or overwrite TASK evidence.
- Detailed usage: `docs/PROGRESS.md`. `teamdev progress --json` is read-only and machine-readable.

## Native Worker Dispatch and Monitoring (v0.17)

- PLAN: after writing Spec/Plan, run `teamdev plan-ready TASK --actor coordinator` **BEFORE** asking for human plan approval. Never request approval from ANALYZE/DRAFT.
- Record only actual human approval with `teamdev approve TASK --scope plan --actor user --confirm APPROVE`.
- For IMPLEMENT, VERIFY and REVIEW use `teamdev worker-prepare TASK --role implementer|verifier|reviewer` **sequentially** before any native Task/Agent call. IMPLEMENT `APPROVED` is dispatched exactly once by this command. No native Worker is started by `worker-prepare`.
- Run `teamdev monitor --task TASK` and `teamdev progress --task TASK` after preparation; UNTRACKED at this point means **not yet observed**, NOT a runtime failure or RUNNING proof.
- Call the native Task/Agent for that role. Do not run `worker-start` in parallel with native Task. A synchronous native call blocks the Coordinator, so it cannot poll from inside the call. Use `monitor --watch` in another terminal for truly asynchronous telemetry.
- After the native call actually returns, record `teamdev worker-return TASK --role ROLE --session-id UNIQUE --status FINISHED|FAILED|STOPPED` and then call `teamdev monitor --task TASK` and `teamdev progress --task TASK`. This is Coordinator-reported observation, not an independently captured runtime event or workflow PASS.
- Runtime hook-driven/asynchronous calls MAY use `worker-start` only after a genuine launch and `worker-stop` on actual return. Do not use `worker-return` for a session already tracked with `worker-start`/`worker-stop`.
- Verify real `teamdev report` / `verify` / `review` transitions and the underlying evidence before moving to the next role. Never fabricate PASS, re-dispatch an already launched task, or advance on monitoring status alone.
- On a state conflict, stop and inspect `teamdev status TASK`, `teamdev next TASK`, and `teamdev monitor --task TASK`. Do not workaround with ad-hoc state.json edits.

