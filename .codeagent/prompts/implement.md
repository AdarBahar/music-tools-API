# Implement a planned task

You are implementing an approved plan.

## Global safety rule (mandatory)

* Do **not** store or repeat secrets, passwords, API keys, tokens, credentials, or connection strings containing secrets.
* Do **not** store PII (emails, phone numbers, addresses, IDs).
* Allowed: placeholders (e.g., `DATABASE_URL`), masked values, and documenting **where** secrets live and **how** to access them.

Any violation is a **BLOCKER** under self-check conventions.

## Inputs I will provide
- Approved plan: {{TASK_PLAN}}
- Branch name and target base (usually main)
- Any constraints (optional)

## Must read before coding
- /.codeagent/current/memory-log.md
- /.codeagent/dev-rules.md
- /.codeagent/current/project_context.md
- /.codeagent/current/project_history.md
- /.codeagent/current/deployment.md
- /.codeagent/current/security.md
- /.codeagent/current/database_schema.sql (if DB touched)
- /.codeagent/current/design_system.md (if UI touched)
- /architecture.md (or equivalent)

This checklist follows the shared “Self-check conventions”.
Any failed BLOCKER must be resolved before completion.

## Implementation rules
- Do not introduce new paths, services, or deployment assumptions without updating documentation via document-changes.md.
- Follow the project’s established patterns.
- Prefer descriptive method/function names over comments.
- Avoid unnecessary defensive code in trusted codepaths.
- Keep changes minimal and focused on the plan.
- Update or add tests as described in the plan.
- If you discover a better approach, pause and propose a plan change before implementing it.

## Output rules
- Show what you changed and where (high-level).
- Call out any risks, migrations, env var changes, or rollout notes.
- Do not update documentation here (that is handled by `document-changes.md`).

## Mid-flight self-check (BLOCKERS)

- [ ] Implementation matches the approved plan
- [ ] No new infra, paths, or env assumptions introduced
- [ ] Promised tests were added or explicitly deferred

Any failed item is a BLOCKER and must be resolved.

