# Optional RTK / CRG integration

This is a **tool integration policy**, not a claim that the external tools are included or activated.

## RTK: all agent shells (when installed)

- CLI output optimization is optional. It MUST NOT replace full test logs, exit status, or stored evidence.
- `teamdev --root . tools-status` detects an `rtk` executable, not verified hook activation.
- Preview: `teamdev --root . tools-setup --tool rtk --runtime opencode|claude|codex`.
- Explicit install of hooks: add `--apply` only after reviewing; **user-global** settings may be changed. Do this on each developer machine, outside PR automation.
- Agent-native initializers: `rtk init -g --opencode`, `rtk init -g --codex`, `rtk init -g --auto-patch` (Claude Code). Verify installed RTK version supports these flags. Restart agent after setup.
- RTK may be source-available with BUSL terms in its standard edition; teams should review edition and license. Install the right RTK product from official RTK releases, not an unrelated namesake package.
- If no RTK binary or hooks, run native commands directly and DO NOT claim token saving occurred.

## CRG: ANALYZE / PLAN / REVIEW on demand

- `teamdev --root . tools-status` checks a CLI executable, project `.code-review-graph/` directory, and bridge skill discovery. Presence does not prove freshness or MCP availability.
- Install from upstream using an approved environment (e.g. `python -m pip install code-review-graph` in a suitable venv). The framework NEVER downloads it automatically.
- Preview the official init: `teamdev --root . tools-setup --tool crg`; apply with `--apply` (may modify native agent config; back up those settings).
- Build project graph: `teamdev --root . crg-build --apply`; re-build when code changed and graph may be stale.
- Use the `code-graph-analysis` routing skill for cross-file analysis. Only call CRG native MCP/CLI tools that really exist in installed version. Never fabricate dependency paths, results, or pass evidence.
- Offline mode: locally installed CLIs and local graph build can be used subject to their own dependencies. If unavailable, fall back to `rg`, code reading and tests.

## Native worker roles

- Coordinator identifies appropriate CRG usage before PLAN and again for REVIEW when graph evidence matters.
- Implementer and Verifier may use RTK for everyday shell commands, but they MUST save **uncompressed original** test output, commands and exit codes in TASK evidence.
- RTK hooks are per developer / runtime, and installing a CLI does not activate a hook. CRG bridge skill does not install the graph engine or MCP.

## CRG auto (v0.11)

- `teamdev crg-auto` (read-only): SKIP_EMPTY, FALLBACK_NO_CRG, BUILD, REBUILD, READY_CANDIDATE.
- `teamdev crg-auto --apply` (on demand): only executes CRG build when installed and code exists; does not initialize a global MCP.
- First empty project request is **not blocked** by missing graph. After first source creation, Reviewer can prepare graph when cross-file analysis is useful.
- mtime-based graph freshness is NOT an authoritative index validity proof.
- External recommended skills remain optional and must be separately installed before use.
