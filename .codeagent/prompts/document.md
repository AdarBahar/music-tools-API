# Document changes (post-implementation)

You are updating project documentation after code changes were completed.

Your goal is to ensure that `/.codeagent/current/` accurately reflects the **current working state of the system**, without adding historical or speculative content.

---

## Global safety rule (mandatory)

* Do **not** store or repeat secrets, passwords, API keys, tokens, credentials, or connection strings containing secrets.
* Do **not** store PII (emails, phone numbers, addresses, IDs).
* Allowed: placeholders (e.g., `DATABASE_URL`), masked values, and documenting **where** secrets live and **how** they are managed.

Any violation is a **BLOCKER** under self-check conventions.

---

## Inputs I will provide

* Branch name + commit hash(es)
* PR link (optional)
* Git diff summary or `git diff main...HEAD`
* Notes about behavior changes, endpoints, migrations, env var changes (if any)

---

## Mandatory project paths and deployment context

Every documentation update MUST ensure that a section titled **“Project paths and deployment context”** exists at the **TOP** of the documentation.

This section is the operational source of truth.

* Missing information must be marked **TODO**.
* Any change to paths, infrastructure, environments, databases, access, or deployment MUST update this section.
* Do not infer, guess, or rely on memory.

If nothing changed, explicitly state: **No changes required**.

---

## Must read before writing

* `/.codeagent/current/project_history.md`
* `/.codeagent/current/memory-log.md`
* `/.codeagent/current/project_context.md`
* `/.codeagent/current/deployment.md`
* `/.codeagent/current/security.md`
* `/.codeagent/current/database_schema.sql` (if DB changed)
* `/.codeagent/current/design_system.md` (if UI changed)

Always read the **Project paths and deployment context** section first and treat it as authoritative.

---

## Update these files (only when relevant)

1. `project_history.md`

   * Add a new entry at the TOP
   * Include summary, key changes, impact, ops notes, follow-ups

2. `memory-log.md`

   * Durable knowledge only
   * Keep it short and skimmable

3. `project_context.md`

   * Update what the system is and what changed recently

4. `deployment.md`

   * Build/deploy steps
   * Rollback notes if changed

5. `security.md`

   * Auth, permissions, secrets handling, threat notes (if relevant)

6. `database_schema.sql` (only if DB changed)

   * Must match the working database exactly

7. `design_system.md` (only if UI changed)

   * Capture UI patterns and decisions

Empty files are valid but must be progressively filled. Create sections when missing.

---

## Size and scope discipline (important)

* `current/` is **working memory**, not an archive
* Do not add long historical explanations
* Prefer linking to `/.codeagent/docs/` instead of duplicating content
* If a section grows beyond what is required for current correctness, propose moving it to reference docs

---

## Output rules

* Return **ONLY the updated file contents** for each file you changed
* Do not invent changes; everything must be grounded in the diff or inputs
* Keep files concise and skimmable

---

## Self-check (follows Self-check conventions)

BLOCKERS:

* Any sensitive data leakage
* Any guessed or inferred infra, paths, endpoints, or schema
* Missing or outdated Project paths and deployment context section
* Database schema drift

Completion statement (one line, verbatim):

> **Self-check passed: documentation updated with no blockers.**
