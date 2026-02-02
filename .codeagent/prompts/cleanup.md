# Cleanup and order (including removing AI slop)

Check the diff against main and clean up the branch.

## Global safety rule (mandatory)

* Do **not** store or repeat secrets, passwords, API keys, tokens, credentials, or connection strings containing secrets.
* Do **not** store PII (emails, phone numbers, addresses, IDs).
* Allowed: placeholders (e.g., `DATABASE_URL`), masked values, and documenting **where** secrets live and **how** to access them.

Any violation is a **BLOCKER** under self-check conventions.

## Goals
1) Remove "AI code slop"
- Remove comments that don't match the repo style.
- Remove unnecessary defensive checks/try-catch that are abnormal for the area.
- Remove `any` casts (or equivalents) used to bypass types without justification.
- Align style with surrounding code.

2) Code cleanup
- Remove unused imports everywhere.
- Simplify code where safe.
- Deduplicate helpers if they were introduced unnecessarily.
- Ensure lint/build/test runs are clean (where applicable).

3) Repo hygiene (docs placement)
- Move Markdown files that are not `README.md` and are not under `/.codeagent/` into `/.codeagent/docs/`.
- Move unneeded/dead documents into an `Archive/` folder (only if clearly obsolete).

## Check list
This checklist follows the shared “Self-check conventions”.
Any failed BLOCKER must be resolved before completion.

## Output rules
- Do not change behavior unless you are fixing a clear bug or removing accidental bloat.
- Report at the end with ONLY a 1–3 sentence summary of what you changed.

## Completion check

- [ ] No behavior changes introduced
- [ ] No unused imports or dead code remain
- [ ] Final diff is clean and minimal

Completion statement:
Self-check passed: cleanup complete with no behavior changes.
