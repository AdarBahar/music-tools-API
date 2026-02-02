# Migrate project documentation to the current CodeAgent Kit

You are migrating an existing project that already contains documentation, history, and operational knowledge.
Your goal is to upgrade the project to the **current CodeAgent Kit structure and rules** without losing knowledge.

## Inputs I will provide

* Current branch name
* (Optional) PR link
* (Recommended) `git diff` or a list of changed/added docs
* (Optional) Notes about what changed in the kit version

---

## Global safety rule (mandatory)

* Do **not** store or repeat secrets, passwords, API keys, tokens, credentials, or connection strings containing secrets.
* Do **not** store PII (emails, phone numbers, addresses, IDs).
* Allowed: placeholders (e.g., `DATABASE_URL`), masked values, and documenting **where** secrets live and **how** to access them.

Any violation is a **BLOCKER**.

---

## Must read before migrating

* `/.codeagent/current/project_history.md`
* `/.codeagent/current/memory-log.md`
* `/.codeagent/current/project_context.md`
* `/.codeagent/current/deployment.md`
* `/.codeagent/current/security.md`
* `/.codeagent/current/database_schema.sql` (if DB exists)
* Project root docs relevant to understanding the system (e.g., `/README.md`, `/docs`, `/architecture.md`)

If files are empty or incomplete, do not assume. Create sections when missing and mark unknowns as TODO.

---

## Migration goals

1. Preserve existing knowledge (no silent loss)
2. Normalize documentation into `/.codeagent/current/`
3. Create a clean baseline that future work can maintain
4. Avoid inventing facts. If unsure, mark TODO.

---

## What to update

### 1) Ensure `/.codeagent/current/` is complete and usable

Update these files as needed:

* `project_history.md`
* `project_context.md`
* `memory-log.md`
* `deployment.md`
* `security.md`
* `database_schema.sql` (if DB exists)
* `design_system.md` (if UI exists)

### 2) Add the top-level operational section

Ensure documentation includes a top section titled:
**“Project paths and deployment context”**

It must cover:

* Local paths: code root, frontend, backend, docs, deployment scripts
* Staging + production server details: hosting, deploy paths, logs, backups
* Database: names, users/roles (no secrets), endpoints (masked), connection method
* Access and operations: how to deploy, how to connect, env var + secrets sources

Missing info must be marked TODO.

---

## Migration procedure

### A) Inventory existing knowledge

* Identify what information exists and where (current files, root docs, wiki, etc.)
* Note conflicts or contradictions

### B) Produce a normalized baseline

* Rewrite/extend `/.codeagent/current/*` to reflect the best known truth
* Resolve contradictions where possible using the most reliable source
* If unresolved, mark as TODO and record the ambiguity in `memory-log.md`

### C) Preserve legacy docs safely

* Do not delete legacy docs.
* If you need to restructure or retire docs, move them to:

  * `/.codeagent/docs/archive/`
* Add pointers from `project_context.md` to archived material when still relevant.

### D) Add a migration entry

* Add a new entry at the TOP of `project_history.md` indicating:

  * the migration occurred
  * what was normalized
  * what was moved/archived
  * follow-ups and TODOs

---

## Output rules

* Return ONLY the updated file contents for each file you changed.
* Do not invent infrastructure details, endpoints, or database schema.
* Keep files concise and skimmable.

---

## Self-check (must follow self-check conventions)

BLOCKERS:

* Any sensitive data leakage
* Any guessed/assumed infra, paths, endpoints, or schema
* Missing “Project paths and deployment context” when required
* Loss of existing knowledge without archiving or explicit justification

Completion statement (one line, verbatim):

> **Self-check passed: migration complete with no blockers.**

