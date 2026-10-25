# Work tracking — CLI commands are **for agents**, not users

Agents start each session with `python3 scripts/workflow.py next`, then use the **original externally installed skills**. All three hosts share `docs/exec-plans/active/TASK-ID/`.

| Stage | Agent operation | Artifact / control |
|---|---|---|
| Analyze | `workflow.py new --id TASK-001 --title '...'` then upstream diagnostic skills | `analysis.md` |
| Plan | upstream `to-spec`, `to-tickets`, `writing-plans` | `spec.md`, `plan.md`, `ac-tests.json` |
| Approval | **ask user in chat**; only after explicit user plan approval: `workflow.py approve --id TASK-001 --user-confirmed` | timestamp/flag only; not user authentication |
| Implement | `workflow.py gate --id TASK-001 --stage implement`; upstream TDD skills | code, tests, optional RED record |
| Verify | `workflow.py run --id TASK-001 --ac AC-01 -- python3 -m pytest tests/test_feature.py` | timestamped execution log, exit code, source digest |
| Review | `workflow.py gate --id TASK-001 --stage review`, independent original `code-review`; `workflow.py review --id TASK-001 --verdict PASS --notes-file review.md` | substantive reviewer notes; independence not automatically verified |
| Completion | `workflow.py gate --id TASK-001 --stage complete`; **ask user in chat**; only after explicit completion approval run `workflow.py complete --id TASK-001 --user-confirmed` | moves task folder to `completed/` |

Natural language interaction with user is sufficient; the agent must issue internal commands without asking user to copy commands. `--user-confirmed` is an attestation by the agent, **not** proof of human identity. Never silently auto-approve. On review FAIL, return to implementation/verification and rerun tests; a stale review cannot complete.

`ac-tests.json` maps each AC ID to nonempty descriptions of test commands. Gate checks successful recorded command executions and current source digest, **not** semantic adequacy of test-to-AC mapping. Do not use a no-op or unrelated test as evidence.

## New session — required first action

All agents run `python3 scripts/workflow.py session` on a new session and summarize active tasks in chat **before proceeding with any work**. It is read-only: session start alone never creates, approves, reviews, or completes tasks. `--json` supports machine parsing and `--all` includes completed plans. The user does not need to type the command. Native host startup execution is not assumed: use the supplied launcher for guaranteed terminal start-time printing; host prompt compliance still needs host-level testing.

When OpenSpec is active, do not duplicate its change spec under product-specs; store only task execution plan and evidence.
