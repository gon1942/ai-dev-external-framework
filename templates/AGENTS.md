# Shared AI development workflow — OpenCode / Codex / Claude Code

**Use upstream installed skills** (Matt Pocock and Superpowers), not home-grown substitutes. CRG is independently managed. Apply this file in all three agents; actual skill discovery/activation must be verified in each host.

## On every new user development request / resumed session
1. **At the start of EVERY NEW AGENT SESSION, before planning or coding**, run `ai-dev status` from the project root. Display the active task summary to the user (ID, phase, next action), even if the user has not asked for a new task. Read applicable task files and resume rather than duplicating. This is required for OpenCode, Codex, and Claude Code. If invocation is unavailable, say the session check was not performed; never claim it ran.
2. Read `docs/PLANS.md`, `docs/ai-workflow/POLICY.md`, and the applicable task files. Invoke upstream skills through the host's skill tool; merely reading SKILL.md is not equivalent to invoking a skill.
3. If a new substantive request, **agent** creates task using `ai-dev work new --id TASK-... --title '...'`. Agent writes analysis.md, spec.md, plan.md, ac-tests.json using original upstream skills.
4. Summarize plan and explicitly ask the human for approval. **Do not run approve before human approval.** An explicit natural-language approval (e.g. '계획 승인', '진행해') in response to the presented plan allows the **agent** to run `ai-dev work approve --id TASK-... --user-confirmed`. No person needs to type CLI commands.
5. Before editing source, **agent** runs `ai-dev work gate --id TASK-... --stage implement`. Use upstream TDD/implementation skills. Never bypass a failed gate.
6. **Agent** runs tests through `workflow.py run --id TASK-... --ac AC-.. -- <command>`, reviews real logs, and checks `workflow.py gate --id TASK-... --stage review`. Failed/insufficient coverage: fix and rerun.
7. Invoke original `code-review` / reviewer skill in an independent context where possible, evaluate diff+spec+evidence; write substantial notes and **agent** records `workflow.py review --id TASK-... --verdict PASS|FAIL --notes-file <path>`. A recorded verdict is not proof of reviewer independence.
8. When `workflow.py gate --id TASK-... --stage complete` passes, report `READY_FOR_REVIEW` and ask human to confirm completion. Only after explicit human confirmation may **agent** call `workflow.py complete --id TASK-... --user-confirmed`. No self-approval.
9. For all stages, keep user interaction **natural-language only**; CLI is internal agent tooling. On session changes, any of the three agents resumes the same project files.

## External skill mapping
Analyze: `grill-with-docs`, `systematic-debugging`, CRG if installed. Plan: `to-spec`, `to-tickets`, `writing-plans`. Implement: `implement`, `test-driven-development`, optional `implement-spec` only with compatible host runtime. Verify: `verification-before-completion`. Review: `code-review`, `requesting-code-review`.

## Boundaries
No automatic commit, push, merge, or PR; never invent test/review evidence. An ambiguous 'yes' not clearly responding to a specific approval question is not consent. Agent runs no approval command on inference, and never claims person identity is verified. The CLI gates are structural; AC semantic adequacy and independent-review authenticity require critical inspection. If original skills aren't available, report that; don't claim successful invocation.

## Native session status hooks
`ai-dev setup` installs read-only SessionStart hooks (OpenCode plugin, Codex and Claude hook configs). Agents must report the injected work-state to user once per new session and read the work files before edits. Session status is a snapshot, not proof of current test evidence. Do not create a task just because a session starts.
