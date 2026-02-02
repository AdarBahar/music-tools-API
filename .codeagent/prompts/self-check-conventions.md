# Self-check conventions (shared across all prompts)

This document defines a **common self-check system** used by all CodeAgent prompts.
Each prompt may define its own checklist, but all follow the same rules, language, and severity model.

These conventions exist to prevent silent failures, guessing, and unsafe behavior.

---

## Global safety rule (mandatory)

**Severity: BLOCKER**

The agent must **never**:

* Store or repeat secrets, passwords, API keys, tokens, or credentials
* Store or repeat PII (emails, phone numbers, addresses, personal IDs)

Allowed patterns:

* Placeholders (e.g., `DATABASE_URL`, `API_KEY`)
* Masked values (e.g., `postgres://user:***@host/db`)
* Describing **where** secrets live and **how** they are accessed (not their values)

Any violation of this rule is an immediate **BLOCKER**.

---

## Severity levels

### BLOCKER

A **BLOCKER** means the task **must not complete**.

A check is a BLOCKER when it affects:

* Correctness or safety
* Production behavior
* Deployment, infrastructure, or data integrity
* Security, access, or secrets
* Source-of-truth documentation

Rules:

* Any failed BLOCKER = task FAILED
* The agent must explicitly list all failed BLOCKER items
* The agent must fix them before continuing

---

### WARNING

A **WARNING** highlights risk, uncertainty, or suboptimal quality, but does not block completion.

A check is a WARNING when it affects:

* Maintainability
* Clarity
* Developer experience
* Future work or technical debt

Rules:

* WARNINGS must be explicitly listed
* WARNINGS must include a short rationale
* WARNINGS do not block task completion

---

## Self-check execution rules

All self-checks follow the same execution flow:

1. Run the checklist
2. Classify failures as BLOCKER or WARNING
3. If any BLOCKER exists:

   * Output a failure report
   * Do not complete the task
4. If only WARNINGS exist:

   * List them explicitly
   * Proceed with completion

---

## Failure report format (mandatory)

When BLOCKER items exist, the agent must output:

```md
Self-check FAILED.

BLOCKERS:
- <failed item>
- <failed item>

WARNINGS:
- <warning item> (reason)
```

The task is incomplete until the BLOCKERS list is empty.

---

## Completion statement conventions

Each prompt defines its own completion statement.

Rules:

* The statement must be output **verbatim**
* It must only be output if all BLOCKERS are resolved
* WARNINGS may still exist

Example:

> **Self-check passed: all blockers resolved; warnings listed above.**

---

## How prompts must reference this document

Each prompt must:

* Include a short self-check section
* Reference this document as the governing standard
* Specify which checklist items are BLOCKER vs WARNING

Example reference:

```md
This checklist follows the shared “Self-check conventions”.
Any failed BLOCKER must be fixed before completion.
```

---

## Default severity guidance

Unless explicitly stated otherwise:

* Missing production, deployment, or database information → **BLOCKER**
* Guessing or inferring undocumented behavior → **BLOCKER**
* Security or access ambiguity → **BLOCKER**
* Outdated but non-critical documentation → **WARNING**
* Style, verbosity, or wording issues → **WARNING**
