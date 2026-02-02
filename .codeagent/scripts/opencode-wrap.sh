#!/bin/sh
# POSIX sh. Generate OpenCode command wrappers from CodeAgent kit prompts.
# Key fix:
# - On update, optionally preserve manual (non-generated) wrappers via --no-overwrite-manual.

set -eu

PREFIX=".codeagent"
OPENCODE_DIR=".opencode"
MODE=""
DRY_RUN=0
VERBOSE=0
NO_OVERWRITE_MANUAL=0

usage() {
  cat <<'USAGE'
Usage:
  opencode-wrap.sh init   [--prefix <dir>] [--opencode <dir>] [--dry-run] [--verbose]
  opencode-wrap.sh update [--prefix <dir>] [--opencode <dir>] [--dry-run] [--verbose] [--no-overwrite-manual]

Outputs:
  - Reads:  <prefix>/prompts/*.md
  - Writes: <opencode>/commands/*.md

USAGE
  exit 1
}

log() { [ "$VERBOSE" -eq 1 ] && printf "%s\n" "$*" >&2 || true; }
die() { printf "ERROR: %s\n" "$*" >&2; exit 1; }

hash_text() {
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 | awk '{print $1}'
  elif command -v sha256sum >/dev/null 2>&1; then
    sha256sum | awk '{print $1}'
  elif command -v openssl >/dev/null 2>&1; then
    openssl dgst -sha256 | awk '{print $2}'
  else
    cksum | awk '{print $1}'
  fi
}

agent_for_prompt() {
  case "$1" in
    plan.md|audit.md|self-check-conventions.md) echo "plan" ;;
    code-review-nodejs.md) echo "review" ;;
    document.md) echo "build" ;;
    implement.md|run.md|migrate.md|codeagent_update.md) echo "build" ;;
    *) echo "build" ;;
  esac
}

desc_for_prompt() {
  case "$1" in
    plan.md) echo "CodeAgent PLAN: Plan a feature" ;;
    implement.md) echo "CodeAgent IMPLEMENT: Implement a feature" ;;
    run.md) echo "CodeAgent RUN: Run or execute a task" ;;
    document.md) echo "CodeAgent DOCUMENT: Update or improve documentation" ;;
    migrate.md) echo "CodeAgent MIGRATE: Migrate or refactor code" ;;
    audit.md) echo "CodeAgent AUDIT: Audit code" ;;
    code-review-nodejs.md) echo "CodeAgent REVIEW_NODE: Review Node.js code" ;;
    self-check-conventions.md) echo "CodeAgent SELF_CHECK: Self-check before final answer" ;;
    codeagent_update.md) echo "CodeAgent UPDATE: Update CodeAgent kit usage" ;;
    *) echo "CodeAgent: $1" ;;
  esac
}

[ $# -ge 1 ] || usage
MODE="$1"
shift || true

case "$MODE" in init|update) ;; *) usage ;; esac

while [ $# -gt 0 ]; do
  case "$1" in
    --prefix) PREFIX="$2"; shift 2 ;;
    --opencode) OPENCODE_DIR="$2"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    --verbose) VERBOSE=1; shift ;;
    --no-overwrite-manual) NO_OVERWRITE_MANUAL=1; shift ;;
    *) die "Unknown argument: $1" ;;
  esac
done

PROMPTS_DIR="$PREFIX/prompts"
COMMANDS_DIR="$OPENCODE_DIR/commands"

[ -d "$PROMPTS_DIR" ] || die "Prompts directory not found: $PROMPTS_DIR"

if [ "$DRY_RUN" -eq 0 ]; then
  [ -d "$COMMANDS_DIR" ] || mkdir -p "$COMMANDS_DIR"
else
  log "[dry-run] would ensure directories exist: $COMMANDS_DIR"
fi

found_any=0

for src in "$PROMPTS_DIR"/*.md; do
  [ -f "$src" ] || continue
  found_any=1

  base=$(basename "$src")
  name=${base%.md}
  dest="$COMMANDS_DIR/$name.md"

  agent=$(agent_for_prompt "$base")
  desc=$(desc_for_prompt "$base")
  src_hash=$(cat "$src" | hash_text)

  is_generated=0
  drift=1

  if [ -f "$dest" ]; then
    old_gen=$(awk -F': *' '/^generated-by:/{print $2; exit}' "$dest" 2>/dev/null || true)
    if [ "$old_gen" = "codeagent-kit" ]; then
      is_generated=1
      old_hash=$(awk -F': *' '/^source-hash:/{print $2; exit}' "$dest" 2>/dev/null || true)
      old_src=$(awk -F': *' '/^source-path:/{print $2; exit}' "$dest" 2>/dev/null || true)
      old_agent=$(awk -F': *' '/^agent:/{print $2; exit}' "$dest" 2>/dev/null || true)
      if [ "$old_hash" = "$src_hash" ] && [ "$old_src" = "$src" ]; then
        # Also treat agent mapping changes as drift
        if [ "$old_agent" = "$agent" ]; then
          drift=0
        fi
      fi
    fi
  fi

  if [ -f "$dest" ] && [ "$is_generated" -eq 0 ]; then
    if [ "$MODE" = "init" ]; then
      printf "SKIP (manual exists): %s\n" "$dest" >&2
      continue
    fi
    if [ "$NO_OVERWRITE_MANUAL" -eq 1 ]; then
      printf "SKIP (manual preserved): %s\n" "$dest" >&2
      continue
    fi
    printf "OVERWRITE (manual): %s\n" "$dest" >&2
  fi

  if [ -f "$dest" ] && [ "$is_generated" -eq 1 ] && [ "$drift" -eq 0 ]; then
    log "OK: $dest"
    continue
  fi

  [ -f "$dest" ] && [ "$is_generated" -eq 1 ] && printf "DRIFT: %s\n" "$dest" >&2 || true

  if [ "$DRY_RUN" -eq 1 ]; then
    printf "[dry-run] would write %s (agent=%s)\n" "$dest" "$agent" >&2
    continue
  fi

  tmp="$dest.tmp.$$"
  {
    printf "%s\n" "---"
    printf "description: %s\n" "$desc"
    printf "agent: %s\n" "$agent"
    printf "generated-by: codeagent-kit\n"
    printf "source-path: %s\n" "$src"
    printf "source-hash: %s\n" "$src_hash"
    printf "%s\n" "---"
    printf "\n"
    printf "This command is generated from CodeAgent Kit prompt: `%s`.\n\n" "$base"
    cat "$src"
    printf "\n"
  } > "$tmp"
  mv "$tmp" "$dest"
done

[ "$found_any" -eq 1 ] || die "No prompts found in $PROMPTS_DIR"

printf "Done. OpenCode commands are in %s\n" "$COMMANDS_DIR"
[ "$DRY_RUN" -eq 1 ] && printf "Dry run only. No files were changed.\n" || true
