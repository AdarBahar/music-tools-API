# Audit and refresh `/.codeagent/current/` documentation

You are auditing the project’s living documentation for **accuracy, relevance, and drift**.
Your goal is to identify discrepancies, safely handle obsolete information, and keep `current/` usable as working memory.

This is a **diagnostic and corrective** workflow, not a rewrite.

---

## Global safety rule (mandatory)

* Do **not** store or repeat secrets, passwords, API keys, tokens, credentials, or connection strings containing secrets.
* Do **not** store PII (emails, phone numbers, addresses, IDs).
* Allowed: placeholders (e.g., `DATABASE_URL`), masked values, and documenting **where** secrets live and **how** to access them.

Any violation is a **BLOCKER** under self-check conventions.

---

## Inputs I will provide

* (Recommended) Branch name
* (Optional) PR link
* (Optional) Known areas of concern (deployment, DB, security, etc.)
* (Optional) `git diff` or recent commits that may have caused drift

---

## Must read

* `/.codeagent/current/project_context.md`
* `/.codeagent/current/project_history.md`
* `/.codeagent/current/memory-log.md`
* `/.codeagent/current/deployment.md`
* `/.codeagent/current/security.md`
* `/.codeagent/current/database_schema.sql` (if DB exists)
* `/.codeagent/current/design_system.md` (if UI exists)

---

## Audit goals

1. Identify factual inaccuracies and contradictions
2. Identify obsolete or misleading information
3. Reduce noise while preserving important history
4. Enforce size and scope discipline in `current/`

---

## Audit procedure

### A. Consistency check

* Look for contradictions across docs (deployment vs context vs history)
* Look for duplicated instructions that diverged

### B. Accuracy check

Validate that:

* Deployment steps are coherent and current
* Environment and path information is consistent
* Security notes match actual auth and secrets handling
* `database_schema.sql` reflects the current schema

### C. Relevance and scope check

* Flag content as:

  * Still valid
  * Likely stale
  * Clearly obsolete

Do not delete aggressively. Prefer moving obsolete but potentially useful content to `/.codeagent/docs/archive/`.

Treat `current/` as **working memory**, not long-term storage. If information is not required to make a correct decision today, propose moving it out.

---

## Output format

### 1. Findings

* **BLOCKERS**: issues that could cause incorrect work, broken deploys, security issues, or production mistakes
* **WARNINGS**: issues that reduce clarity or add tech debt

### 2. Proposed fixes

For each finding:

* File
* Section
* Recommended action (fix, archive, shorten, mark TODO)

### 3. Apply fixes (only if safe)

* Apply fixes only when they are clearly grounded in existing information
* Otherwise, leave as proposals

---

## Output rules

* If you change files, return **ONLY the updated file contents**
* If you do not change files, return **ONLY the findings and proposals**
* Do not invent details. Mark unknowns as TODO

---

## Self-check (follows Self-check conventions)

BLOCKERS:

* Any sensitive data leakage
* Any invented or assumed infra, paths, endpoints, or schema
* Any unresolved contradiction not explicitly flagged

Completion statement (one line, verbatim):

> **Self-check passed: audit complete with no blockers.**
