## 공통 메타 스킬: using-superpowers (21개 구성 중 1개)

각 개발 단계 진입 시 `using-superpowers` 스킬이 설치되어 있으면 해당 에이전트의 공식 스킬 도구로 읽고, 해당 단계의 `.ai-dev/stage-skills.json` 배정과 작업 요청을 고려하여 다른 원본 스킬을 선택합니다. 이 스킬은 정책을 무시하거나 자동으로 외부 스킬을 설치·강제 실행하는 라우터가 아닙니다. 스킬 선택 이유와 실제 호출 여부를 `docs/exec-plans/active/<TASK-ID>/` 작업 기록에 **구분해** 기재합니다. 호출 여부는 확인 가능한 도구 기록이 없는 경우 자기 보고라고 명시합니다.

# Shared AI development workflow — OpenCode / Codex / Claude Code

**At the start of each development stage**, inspect `.ai-dev/stage-skills.json` and apply enabled stage assignments; do not invoke disabled skills. Project policy is centrally released and may only be updated by approved `skill sync`. The file defines eligibility, not proof a skill executed.

**Use upstream installed skills** (Matt Pocock and Superpowers), not home-grown substitutes. CRG is a required 19th dependency (CLI/MCP rather than a standalone SKILL.md); verify availability before use. Apply this file in all three agents; actual skill discovery/activation must be verified in each host.

## On every new user development request / resumed session
1. **At the start of EVERY NEW AGENT SESSION, before planning or coding**, run `node .ai-dev/dependency-check.cjs` and then `node .ai-dev/session-status.cjs` from the project root. **In the chat response for every new session (including a greeting like 안녕), report all three agents' installed skill counts AND actual installed skill names AND missing skill names, plus CRG AND Playwright CLI status, followed by active tasks.** Use the checker's actual output; never assume 19/19 or CRG success. Do not omit the dependency report when there are no active tasks. The checklist must appear in the visible conversational reply, not only in logs, toast, hidden reasoning, or hook output. Read applicable task files and resume rather than duplicating. This is required for OpenCode, Codex, and Claude Code. If invocation is unavailable, say the session check was not performed; never claim it ran.
2. If dependency-check reports missing items, the **agent** should execute `npx --yes @gon1942/ai-dev-external-framework@1.0.1 repair-deps --project . --agents all`, with user approval if the host requires network/installation permission. Report failures and do not claim installation succeeded. Run the checker again afterward and report the updated installed/missing list and CRG result to the user. Avoid installing on healthy sessions. If npm/network is unavailable, report missing items and continue without claiming them. Read `docs/PLANS.md`, `docs/ai-workflow/POLICY.md`, and the applicable task files. Invoke upstream skills through the host's skill tool; merely reading SKILL.md is not equivalent to invoking a skill.
3. If a new substantive request, **agent** creates task using `python3 scripts/workflow.py new --id TASK-... --title '...'`. Agent writes analysis.md, spec.md, plan.md, ac-tests.json using original upstream skills.
4. Summarize plan and explicitly ask the human for approval. **Do not run approve before human approval.** An explicit natural-language approval (e.g. '계획 승인', '진행해') in response to the presented plan allows the **agent** to run `python3 scripts/workflow.py approve --id TASK-... --user-confirmed`. No person needs to type CLI commands.
5. Before editing source, **agent** runs `python3 scripts/workflow.py gate --id TASK-... --stage implement`. Use upstream TDD/implementation skills. Never bypass a failed gate.
6. **Agent** runs tests through `workflow.py run --id TASK-... --ac AC-.. -- <command>`, reviews real logs, and checks `workflow.py gate --id TASK-... --stage review`. Failed/insufficient coverage: fix and rerun.
7. Invoke original `code-review` / reviewer skill in an independent context where possible, evaluate diff+spec+evidence; write substantial notes and **agent** records `workflow.py review --id TASK-... --verdict PASS|FAIL --notes-file <path>`. A recorded verdict is not proof of reviewer independence.
8. When `workflow.py gate --id TASK-... --stage complete` passes, report `READY_FOR_REVIEW` and ask human to confirm completion. Only after explicit human confirmation may **agent** call `workflow.py complete --id TASK-... --user-confirmed`. No self-approval.
9. For all stages, keep user interaction **natural-language only**; CLI is internal agent tooling. On session changes, any of the three agents resumes the same project files.

## External skill mapping
Analyze: `grill-with-docs`, `systematic-debugging`, CRG MCP graph tools when installed; build the graph once source is present. Plan: `to-spec`, `to-tickets`, `writing-plans`. Implement: `implement`, `test-driven-development`, optional `implement-spec` only with compatible host runtime. Verify: `verification-before-completion`. Review: `code-review`, `requesting-code-review`.

## Boundaries
No automatic commit, push, merge, or PR; never invent test/review evidence. An ambiguous 'yes' not clearly responding to a specific approval question is not consent. Agent runs no approval command on inference, and never claims person identity is verified. The CLI gates are structural; AC semantic adequacy and independent-review authenticity require critical inspection. If original skills aren't available, report that; don't claim successful invocation.

## Native session status hooks
`npx --yes @gon1942/ai-dev-external-framework@0.9.3 setup` installs read-only SessionStart hooks (OpenCode plugin, Codex and Claude hook configs). Agents must report the injected work-state to user once per new session and read the work files before edits. Session status is a snapshot, not proof of current test evidence. Do not create a task just because a session starts.

## Code Review Graph (CRG)
During analysis or review of an existing codebase, check CRG MCP tools first. If the code graph has not been built, run the installed CRG CLI `build` in the project root. If unavailable or indexing fails, report it and fall back to ordinary code inspection. Do not claim CRG was used unless it was actually invoked.

## Playwright browser verification (20th default component)
`playwright-cli` is a conditional Verify-stage skill for web UI changes. Check local `.ai-dev/playwright/node_modules/.bin/playwright-cli` and the agent SKILL.md before invoking it. Verify real browser actions with observed outcomes, record evidence, and do not claim browser execution from skill installation alone. If missing, run the framework `repair-deps` with permission and recheck.
