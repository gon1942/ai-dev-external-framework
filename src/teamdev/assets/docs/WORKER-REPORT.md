# Worker Report Input Contract (v0.19.1)

`teamdev report --file` accepts **JSON only**, never `report.md`. Create a separate unverified input file (e.g. `docs/tasks/TASK-ID/implementer-input.json`).

```bash
teamdev --root . report-template TASK-ID --worker implementer --output docs/tasks/TASK-ID/implementer-input.json
# Implementer records only real changed files and existing test evidence/ files.
teamdev --root . report-check TASK-ID --file docs/tasks/TASK-ID/implementer-input.json
teamdev --root . report TASK-ID --actor implementer --file docs/tasks/TASK-ID/implementer-input.json
teamdev --root . next TASK-ID
```

Schema: `task` exact TASK ID, `status` exactly `implemented`, `worker` nonempty string, `changed_files` string array, `evidence` nonempty string array of files inside `docs/tasks/TASK-ID/evidence/`. Template deliberately contains empty evidence and **cannot pass validation** until true evidence is provided. For required TDD tasks, `tdd-check` contract still applies. `report-check` is read-only; only `report` records the result and advances to VERIFY. The CLI-owned `worker-report.json` must never be used as editable input. If the task is already in VERIFY, do not resubmit; use `teamdev next TASK-ID`. No fabricated evidence or unauthorized workflow progression.
