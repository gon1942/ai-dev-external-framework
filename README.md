# External AI Development Framework v0.8.1

Single npm source tree for OpenCode / Codex / Claude Code. Installs **original upstream** Matt Pocock, Superpowers and Ponytail skills, project docs, session hooks and workflow tracking. No custom replacement Analyze/Plan/Implement/Verify/Review skills.

## Publish (requires your npm account)

```bash
npm test
npm run publish:check
npm login
npm publish --access public
```

Check npm package availability and account permission before publishing; this project is not published automatically.

## Install from npm after publication

```bash
npx --yes @gon1942/ai-dev-external-framework@0.8.1 init my-project
cd my-project
opencode # or codex / claude
```

`init` creates a missing project directory, installs docs / hooks and **downloads and installs original upstream skills** in one operation. Requires Node.js >=20, Python 3, Git and internet access. A failed download is surfaced as a nonzero exit; retry is safe for unchanged files. For an existing project use `init .`; differing project-specific files are preserved, managed-file conflicts are blocked.

Preview without changing files (also skips network fetch):

```bash
npx --yes @gon1942/ai-dev-external-framework@0.8.1 init my-project --dry-run
```

For offline installation of vendored **unchanged original** checkouts:

```bash
npx --yes @gon1942/ai-dev-external-framework@0.8.1 init my-project --source-dir /path/to/three-repos
```

Source directory must contain `mattpocock/`, `superpowers/`, `ponytail/`. Pin exact vendor git revisions via `--pins pins.json`. Without pins, upstream HEAD is fetched, which is not reproducible across installations. Skills are installed under `.agents/skills`, `.opencode/skills`, `.claude/skills`.

`ai-dev setup`, `ai-dev install-skills`, `ai-dev status`, `ai-dev doctor`, `ai-dev work` remain available. `init` is the one-command convenience entrypoint. CRG is not installed. Actual host-specific hook, subagent and Ponytail plugin execution requires validation in each tool. The CLI does not publish to npm and does not modify user approval decisions.
