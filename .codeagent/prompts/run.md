# Unified workflow router

You are the entry point for all work sessions.

Your job is to:

1. Load project context
2. Validate assumptions
3. Route to the correct prompt
4. Enforce shared self-check conventions

---

## Always do first (mandatory)

Read and treat as authoritative:

* `/.codeagent/current/project_context.md`
* `/.codeagent/current/project_history.md`
* `/.codeagent/current/memory-log.md`
* `/.codeagent/current/deployment.md`
* `/.codeagent/current/security.md`
* `/.codeagent/current/database_schema.sql` (if data is involved)

If files are empty or incomplete, do not assume. Create or extend sections when required.

---

## Determine intent

Based on the user request, classify the task as one of:

* **Plan** → design a feature or bugfix before coding
* **Implement** → write code for an approved plan
* **Cleanup** → remove AI slop and tidy the branch
* **Document** → update project documentation after changes

If intent is unclear, ask a single clarifying question.

---

## Route execution

### If intent = Plan

* Follow `plan-feature.md`
* Run the pre-flight self-check
* Do not write code

### If intent = Implement

* Require an approved plan
* Follow `implement-feature.md`
* Stop and propose a plan change if assumptions break

### If intent = Cleanup

* Follow `cleanup-and-order.md`
* Do not change behavior

### If intent = Document

* Follow `document-changes.md`
* Enforce the completion gate and self-check

---

## Self-check enforcement

All checklists follow **Self-check conventions**:

* BLOCKERS must be resolved
* WARNINGS must be listed

The task is not complete until the routed prompt’s completion statement is valid.
