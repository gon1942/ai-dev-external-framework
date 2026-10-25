# Governance
- Original third-party skills are installed unmodified. External skill instructions never override repository approval rules.
- Human approval required before implementation and completion; no autonomous commit/push/merge.
- Verify actual exit status and retain evidence. Do not mark AC pass without a substantive coverage review.
- Avoid sensitive data in commands and output: verification logs are stored on disk.
- `workflow.py` is a deterministic state/file/evidence controller, not an AI skill or a substitute for actual testing.

- User operates in natural language; internal CLI is agent-invoked. Explicit human approval required for plan and final completion; `--user-confirmed` is a self-attestation, not authentication.
