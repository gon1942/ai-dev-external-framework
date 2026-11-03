---
name: code-graph-analysis
description: Use a locally built Code Review Graph to investigate cross-file dependencies, call relationships and change impact before planning or reviewing significant changes.
---
# Code Graph Analysis (CRG integration)

Use only for nontrivial code-impact analysis, architecture refactors, dependency/call-chain investigations, or security-sensitive reviews. Never claim CRG ran merely because the skill is installed.

1. Run `teamdev --root . tools-status` and inspect `crg.installed`. If absent, explicitly say it is unavailable and use `rg`, file reading, and tests instead.
2. Check whether the code graph exists and whether it is current for the active HEAD / modified source. Directory presence alone does **not** prove freshness.
3. To build or refresh the graph when permitted, use `teamdev --root . crg-build --apply`; preserve exact command output and report failures. Building may incur substantial time on large repositories.
4. Use CRG's available MCP tools or CLI supported by the installed version to identify impacted modules, cross-file references and call paths. Do not invent MCP tool names or results. Record node/edge evidence and related source file paths, not a fabricated conclusion.
5. Cross-check findings against actual code. CRG is supportive evidence, not source-of-truth and not a substitute for test execution.
6. Before REVIEW, refresh stale graphs if permitted; otherwise report graph staleness and perform manual review. Never infer PASS from graph alone.

An external CRG install may provide its own `code-review-graph` skill. This bridge skill provides framework routing only; it does not bundle or replace the upstream CRG MCP or graph engine.

## CRG availability / auto (v0.11)
Only for meaningful cross-file analysis: run `teamdev crg-auto` first. SKIP_EMPTY => normal native code search, never block initial task. FALLBACK_NO_CRG => native search. BUILD or REBUILD => `teamdev crg-auto --apply` if project-approved and safe, then check actual graph queries. READY_CANDIDATE is mtime-only, not proof of full freshness. Never claim CRG usage without actual execution. Recommended external skills are optional and loaded only if installed and relevant; no automatic installation.
