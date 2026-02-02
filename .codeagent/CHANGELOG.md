## v1.0.3

Workflow improvements and clarifications.

### Changes
- Updated `code-review-nodejs.md` to better handle test execution in different environments
- Enhanced `prompts/readme.md` with feature branch and PR workflow requirements
- Added clarification that code review issues can be used as inputs to feature planning

---

## v1.0.1

Initial stable release of CodeAgent Kit.

### Highlights
- Clear separation between system state (`current/`) and workflows (`prompts/`)
- Unified entry point via `run.md`
- Enforced self-check conventions with BLOCKER/WARNING severity
- Explicit safety rules (no secrets, no PII)
- Safe migration (`migrate.md`) and periodic audit (`audit.md`) workflows

### Notes
- This release establishes the long-term contract for prompt structure and documentation behavior.
