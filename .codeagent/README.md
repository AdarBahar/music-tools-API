# CodeAgent Kit

A standardized **workflow and documentation scaffold** for AI-assisted software development.

CodeAgent Kit defines **how work is planned, executed, reviewed, and documented** so that AI assistance stays grounded, auditable, and maintainable over time.

> **Important**
> All projects must install and update CodeAgent Kit using the provided scripts.
> Manual `git subtree` commands are intentionally unsupported.

---

## Table of Contents

- [CodeAgent Kit](#codeagent-kit)
  - [Table of Contents](#table-of-contents)
  - [Requirements](#requirements)
    - [Git requirements](#git-requirements)
      - [macOS note (Apple Git)](#macos-note-apple-git)
    - [Working tree cleanliness (required)](#working-tree-cleanliness-required)
    - [Private repository access](#private-repository-access)
  - [What is CodeAgent Kit](#what-is-codeagent-kit)
  - [Quick Start](#quick-start)
  - [Embedding CodeAgent Kit in a Project](#embedding-codeagent-kit-in-a-project)
    - [Generic CodeAgent Integration](#generic-codeagent-integration)
    - [OpenCode Integration](#opencode-integration)
    - [Other AI Coding Tools (Coming Soon)](#other-ai-coding-tools-coming-soon)
  - [Quick Reference Commands](#quick-reference-commands)
    - [Core Actions](#core-actions)
    - [Do command snippets change per coding agent tool?](#do-command-snippets-change-per-coding-agent-tool)
  - [Standard Workflow](#standard-workflow)
  - [Repository Structure](#repository-structure)
  - [Conventions and Policies](#conventions-and-policies)
    - [`.gitignore` and subtree safety](#gitignore-and-subtree-safety)
  - [Updating and Migrating Documentation](#updating-and-migrating-documentation)
  - [Safety and Trust Model](#safety-and-trust-model)
  - [Versioning](#versioning)
  - [Philosophy](#philosophy)

---

## Requirements

### Git requirements

* `git` must be available
* `git subtree` must be available

#### macOS note (Apple Git)

macOS ships **Apple Git** at `/usr/bin/git`, which does **not** include `git subtree`.

Install Homebrew Git and ensure it is first in your `PATH`:

```sh
brew install git

echo 'export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"' >> ~/.zprofile
source ~/.zprofile

which git
git --version

git subtree >/dev/null && echo "git subtree OK"
```

### Working tree cleanliness (required)

The installer scripts will fail unless the repo is clean.

Before running install/update:

```sh
git status --porcelain
```

It must print nothing.

### Private repository access

If `codeagent-kit` is **private**, `curl https://raw.githubusercontent.com/...` will return **404** unless you authenticate.

Recommended: use GitHub CLI (`gh`) which supports private repos.

---

## What is CodeAgent Kit

CodeAgent Kit is a reusable set of **prompts, conventions, and living documentation** that standardizes AI-assisted engineering workflows.

It helps teams:

* Plan work before writing code
* Implement changes deliberately
* Review, audit, and migrate safely
* Keep documentation synchronized with reality

The kit is designed to be **embedded into projects** and evolved intentionally over time.

---

## Quick Start

If the repo is public, you can run:

```sh
bash <(curl -fsSL https://raw.githubusercontent.com/AdarBahar/codeagent-kit/main/scripts/codeagent.sh) install
```

If the repo is private, use `gh`:

```sh
gh auth login

gh api -H "Accept: application/vnd.github.raw" \
  /repos/AdarBahar/codeagent-kit/contents/scripts/codeagent.sh \
| bash -s -- install
```

---

## Embedding CodeAgent Kit in a Project

All integrations share the same foundation:

* The kit is embedded at `.codeagent/`
* Prompts live in `.codeagent/prompts/`
* Project state lives in `.codeagent/current/`

### Generic CodeAgent Integration

**Use this if you work directly with chat-based AI tools** (copy/paste workflow).

**Short version**:

Public repo:

```sh
bash <(curl -fsSL https://raw.githubusercontent.com/AdarBahar/codeagent-kit/main/scripts/codeagent.sh) install
```

Private repo:

```sh
gh api -H "Accept: application/vnd.github.raw" \
  /repos/AdarBahar/codeagent-kit/contents/scripts/codeagent.sh \
| bash -s -- install
```

**Details**: see `docs/generic.md`

---

### OpenCode Integration

**Use this if you work with OpenCode and slash commands**.

This integration generates OpenCode command wrappers from CodeAgent prompts.

**Short version**:

```sh
# 1. Install the kit
# Public repo:
bash <(curl -fsSL https://raw.githubusercontent.com/AdarBahar/codeagent-kit/main/scripts/codeagent.sh) install

# Private repo (recommended):
# gh api -H "Accept: application/vnd.github.raw" \
#   /repos/AdarBahar/codeagent-kit/contents/scripts/codeagent.sh \
# | bash -s -- install

# 2. Generate OpenCode commands
bash <(curl -fsSL https://raw.githubusercontent.com/AdarBahar/codeagent-kit/main/scripts/opencode-wrap.sh) init
```

If the repo is private, use `gh` for the wrapper generator too:

```sh
gh api -H "Accept: application/vnd.github.raw" \
  /repos/AdarBahar/codeagent-kit/contents/scripts/opencode-wrap.sh \
| bash -s -- init
```

**Details**: see `docs/opencode.md`

---

### Other AI Coding Tools (Coming Soon)

Planned integrations include:

* Cursor
* Continue
* GitHub Copilot Chat
* IDE-native agents

Each integration will:

* Reuse `.codeagent/prompts/` as the source of truth
* Provide a thin adapter layer

**Details**: see `docs/roadmap.md`

---

## Quick Reference Commands

Below are the **canonical workflow actions**. These are tool-agnostic.

For copy-paste blocks, IDE snippets, and slash-command equivalents, see:

* `codeagent-snippets.html`

### Core Actions

| Action               | Alias         | Prompt File                 |
| -------------------- | ------------- | --------------------------- |
| Plan a feature       | `PLAN`        | `plan.md`                   |
| Implement a feature  | `IMPLEMENT`   | `implement.md`              |
| Run / execute tasks  | `RUN`         | `run.md`                    |
| Update documentation | `DOCUMENT`    | `document.md`               |
| Migrate / refactor   | `MIGRATE`     | `migrate.md`                |
| Audit code or docs   | `AUDIT`       | `audit.md`                  |
| Review Node.js code  | `REVIEW_NODE` | `code-review-nodejs.md`     |
| Final self-check     | `SELF_CHECK`  | `self-check-conventions.md` |

### Do command snippets change per coding agent tool?

**No, conceptually. Yes, syntactically.**

* The **intent and structure** of commands are identical across tools.
* The **representation** changes:

  * Chat tools: copy/paste prompt blocks
  * OpenCode: `/plan`, `/implement`, etc.
  * IDE tools: snippets or commands

CodeAgent prompts are the **single source of truth**. Integrations are adapters.

---

## Standard Workflow

```
PLAN → IMPLEMENT → RUN → SELF_CHECK
```

For complex changes:

```
PLAN → AUDIT → IMPLEMENT → REVIEW_NODE → RUN → SELF_CHECK
```

---

## Repository Structure

```
.codeagent/
  prompts/        # Workflow instructions (upstream, do not edit locally)
  current/        # Living project state (project-specific)
  docs/           # Reference docs and archives
CHANGELOG.md
COMPATIBILITY.md
README.md
```

---

## Conventions and Policies

* `.codeagent/prompts/` is treated as vendor code
* `.codeagent/current/` is the project’s living source of truth
* Always plan before implementing non-trivial changes
* Never invent missing information; mark TODOs explicitly

### `.gitignore` and subtree safety

`git subtree` requires a clean working tree.

If the installer needs to add `.DS_Store` to `.gitignore`, it may stage that change. If `git subtree` runs immediately after, Git can error with:

```
fatal: working tree has modifications. Cannot add.
```

Avoid this by doing one of the following:

Option A (recommended): ensure `.DS_Store` is already committed before install/update:

```sh
grep -qxF ".DS_Store" .gitignore || printf "
.DS_Store
" >> .gitignore
git add .gitignore
git commit -m "Ignore .DS_Store"
```

Option B: run install/update with `--commit`, so the script can commit required changes in one run.

---

## Updating and Migrating Documentation

After updating the kit:

1. Update the embedded kit using the script
2. Run documentation migration

```text
Follow @.codeagent/prompts/migrate.md
```

Optional audit:

```text
Follow @.codeagent/prompts/audit.md
```

---

## Safety and Trust Model

* Never store secrets, tokens, or PII
* Document *where* secrets live, not their values
* Violations are blockers

---

## Versioning

Semantic Versioning:

* MAJOR: breaking workflow changes
* MINOR: backward-compatible improvements
* PATCH: wording and clarification

---

## Philosophy

* Workflows are explicit
* Documentation is intentional
* Upgrades are deliberate
* Nothing auto-deletes
