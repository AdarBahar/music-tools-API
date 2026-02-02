# Updating CodeAgent Kit in a Project

This document defines the **standard, repeatable process** for updating CodeAgent Kit prompts in an existing project.

It is written for **developers and tech leads** and is meant to be followed verbatim.

---

## When to use this

Run this process when:

* Pulling a new CodeAgent Kit version
* Updating prompts under `/.codeagent/prompts/`
* Adopting new workflow rules or documentation requirements

Do **not** run this casually mid-feature unless required.

---

## Step 1: Update the CodeAgent Kit

From the project root, pull the desired version:

```bash
git subtree pull --prefix=.codeagent https://github.com/AdarBahar/codeagent-kit v1.x.x --squash
```

If a nested `.codeagent/.codeagent/` directory appears, flatten it:

```bash
mv .codeagent/.codeagent/* .codeagent/
rmdir .codeagent/.codeagent
git add -A .codeagent/
git commit -m "Flatten CodeAgent Kit structure after update"
```

---

## Step 2: Run documentation migration (mandatory)

After updating prompts, **always run the migration prompt**.

### Agent instruction

```text
Follow @.codeagent/prompts/migrate.md
```

### What migration does

* Preserves all existing knowledge
* Normalizes `/.codeagent/current/` to the latest rules
* Adds missing required sections (e.g., paths and deployment context)
* Archives legacy docs instead of deleting them

### Rules

* Do not invent information
* Mark unknowns as TODO
* Do not store secrets, tokens, or PII

The task is complete only when the migration self-check passes.

---

## Step 3: Optional audit (recommended)

After migration, or before a major release, run a documentation audit.

### Agent instruction

```text
Follow @.codeagent/prompts/audit.md
```

### What audit does

* Finds discrepancies and contradictions
* Flags obsolete or stale information
* Proposes safe cleanups

Audits may propose changes or only report findings.

---

## Step 4: Resume normal work

After migration (and optional audit), resume normal workflows using:

```text
Follow @.codeagent/prompts/run.md
```

---

## Safety guarantees

* No existing documentation is deleted without being archived
* No secrets, credentials, or PII are ever stored
* All changes are explicit and reviewable in Git

---

## Summary (copy-paste)

```text
We updated CodeAgent Kit.
Migration has been run using @.codeagent/prompts/migrate.md.
All existing documentation was preserved and normalized.
```
