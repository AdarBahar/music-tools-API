# OpenCode Integration

This document describes how to use **CodeAgent Kit with OpenCode**.

OpenCode provides slash commands and agent separation. CodeAgent Kit provides the workflow discipline and source-of-truth prompts.

---

## When to use this integration

Use **OpenCode Integration** if:

* You use OpenCode as your primary AI interface
* You want `/plan`, `/implement`, `/run` style commands
* You want enforced separation between planning and execution

---

## Architecture overview

```mermaid
flowchart LR
  A[.codeagent/prompts\nWorkflow Source of Truth]
  B[OpenCode Wrapper Generator\nopencode-wrap.sh]
  C[.opencode/commands\nGenerated Commands]
  D[OpenCode Runtime\nAgents: plan | build | review | docs]

  A --> B --> C --> D
```

---

## First-time setup

### Step 1: Install CodeAgent Kit

From your project root:

```sh
bash <(curl -fsSL https://raw.githubusercontent.com/AdarBahar/codeagent-kit/main/scripts/codeagent.sh) install
```

Optional (commit immediately):

```sh
bash <(curl -fsSL https://raw.githubusercontent.com/AdarBahar/codeagent-kit/main/scripts/codeagent.sh) install --commit
```

---

### Step 2: Generate OpenCode command wrappers

```sh
bash <(curl -fsSL https://raw.githubusercontent.com/AdarBahar/codeagent-kit/main/scripts/opencode-wrap.sh) init
```

This creates:

* `.opencode/commands/*.md`

Each file:

* Is generated from a CodeAgent prompt
* Includes metadata and a source hash
* Specifies the correct OpenCode agent

---

## Command-to-agent mapping

| Prompt                      | OpenCode Command          | Agent    |
| --------------------------- | ------------------------- | -------- |
| `plan.md`                   | `/plan`                   | `plan`   |
| `implement.md`              | `/implement`              | `build`  |
| `run.md`                    | `/run`                    | `build`  |
| `audit.md`                  | `/audit`                  | `plan`   |
| `code-review-nodejs.md`     | `/code-review-nodejs`     | `review` |
| `document.md`               | `/document`               | `docs`   |
| `self-check-conventions.md` | `/self-check-conventions` | `plan`   |

---

## Daily usage

Inside OpenCode:

1. Run `/plan` to design changes
2. Review the plan output
3. Run `/implement` to apply changes
4. Run `/run` to execute or document results
5. Finish with `/self-check-conventions`

---

## Updating when the kit changes

### Step 1: Update the embedded kit

```sh
bash <(curl -fsSL https://raw.githubusercontent.com/AdarBahar/codeagent-kit/main/scripts/codeagent.sh) update
```

Optional (commit immediately):

```sh
bash <(curl -fsSL https://raw.githubusercontent.com/AdarBahar/codeagent-kit/main/scripts/codeagent.sh) update --commit
```

---

### Step 2: Regenerate OpenCode wrappers

```sh
bash <(curl -fsSL https://raw.githubusercontent.com/AdarBahar/codeagent-kit/main/scripts/opencode-wrap.sh) update
```

The script:

* Detects prompt drift
* Regenerates wrappers when needed
* Warns about removed or renamed prompts

---

## Conventions and guardrails

* `.codeagent/prompts/` is the single source of truth
* `.opencode/commands/` is generated; do not edit manually
* Custom OpenCode commands should use names not owned by CodeAgent

---

## Why this design works

* Prompts remain tool-agnostic
* Adapters are thin and replaceable
* Workflow semantics stay consistent
* Tool churn does not affect project knowledge

---

## If something looks wrong

1. Run wrapper generation with `--dry-run`
2. Inspect source-hash values in generated files
3. Re-run `init` if wrappers were deleted

---

## Related documentation

* `docs/generic.md` – chat-based integration
* `CHANGELOG.md` – kit evolution
* `COMPATIBILITY.md` – supported tools
