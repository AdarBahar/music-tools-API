#!/bin/sh
# POSIX sh. Install/update CodeAgent Kit into a project via git subtree.
# Key fixes:
# - Avoids the .gitignore staging trap that causes: "fatal: working tree has modifications. Cannot add."
# - Fails fast with clear instructions if .DS_Store ignore is missing (unless --commit).
# - Detects git-subtree without relying on manpages (Apple Git issue).

set -eu

REMOTE_URL="https://github.com/AdarBahar/codeagent-kit"
PREFIX=".codeagent"
REF="main"
DO_COMMIT=0
DRY_RUN=0
VERBOSE=0

usage() {
  cat <<'USAGE'
Usage:
  codeagent.sh install [--ref <ref>] [--prefix <dir>] [--commit] [--dry-run] [--verbose]
  codeagent.sh update  [--ref <ref>] [--prefix <dir>] [--commit] [--dry-run] [--verbose]

Behavior:
  - Requires a clean working tree.
  - Requires git subtree.
  - If .DS_Store is not already ignored/committed:
      * with --commit: commits .gitignore first, then runs subtree
      * without --commit: stops and tells you what to commit

USAGE
  exit 1
}

log() { [ "$VERBOSE" -eq 1 ] && printf "%s\n" "$*" >&2 || true; }
die() { printf "ERROR: %s\n" "$*" >&2; exit 1; }

require_git_repo() {
  git rev-parse --is-inside-work-tree >/dev/null 2>&1 || die "Not inside a git repo"
}

require_clean_tree() {
  if [ -n "$(git status --porcelain)" ]; then
    die "Working tree not clean. Commit or stash first."
  fi
}

require_subtree() {
  if ! (git subtree 2>&1 | grep -q 'usage: git subtree'); then
    cat >&2 <<'MSG'
ERROR: git-subtree is not available.

macOS note:
- Apple Git (/usr/bin/git) does not include git subtree.
- Install Homebrew Git and ensure it is first in PATH:
    brew install git
    echo 'export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"' >> ~/.zprofile
    source ~/.zprofile
MSG
    exit 1
  fi
}

ensure_ds_store_policy() {
  if [ -f .gitignore ] && grep -qxF ".DS_Store" .gitignore; then
    return 0
  fi

  if [ "$DRY_RUN" -eq 1 ]; then
    log "[dry-run] .DS_Store missing from .gitignore; would require commit before subtree."
    return 0
  fi

  if [ "$DO_COMMIT" -eq 0 ]; then
    cat >&2 <<'MSG'
ERROR: .DS_Store is not ignored yet, and git subtree requires a clean working tree.

Fix:
  grep -qxF ".DS_Store" .gitignore || printf "\n.DS_Store\n" >> .gitignore
  git add .gitignore
  git commit -m "Ignore .DS_Store"

Then re-run. Or re-run with --commit.
MSG
    exit 1
  fi

  log "Committing .DS_Store ignore (required for subtree safety)"
  [ -f .gitignore ] || : > .gitignore
  grep -qxF ".DS_Store" .gitignore || printf "\n.DS_Store\n" >> .gitignore
  git add .gitignore
  if [ -n "$(git diff --cached --name-only)" ]; then
    git commit -m "Ignore .DS_Store"
  fi
}

subtree_add() {
  if [ "$DRY_RUN" -eq 1 ]; then
    printf "[dry-run] git subtree add --prefix=%s %s %s --squash\n" "$PREFIX" "$REMOTE_URL" "$REF"
    return 0
  fi
  git subtree add --prefix="$PREFIX" "$REMOTE_URL" "$REF" --squash
}

subtree_pull() {
  if [ "$DRY_RUN" -eq 1 ]; then
    printf "[dry-run] git subtree pull --prefix=%s %s %s --squash\n" "$PREFIX" "$REMOTE_URL" "$REF"
    return 0
  fi
  git subtree pull --prefix="$PREFIX" "$REMOTE_URL" "$REF" --squash
}

soft_uncommit_last() {
  # Keep changes staged but remove the subtree commit if user didn't ask for auto-commit.
  if [ "$DO_COMMIT" -eq 1 ] || [ "$DRY_RUN" -eq 1 ]; then
    return 0
  fi
  git reset --soft HEAD~1 >/dev/null 2>&1 || true
  cat <<'MSG'
Changes were applied and staged, but not committed.
Review and commit when ready.
MSG
}

MODE="${1:-}"
shift || true

case "$MODE" in
  install|update) ;;
  *) usage ;;
esac

while [ $# -gt 0 ]; do
  case "$1" in
    --ref) REF="$2"; shift 2 ;;
    --prefix) PREFIX="$2"; shift 2 ;;
    --commit) DO_COMMIT=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    --verbose) VERBOSE=1; shift ;;
    *) die "Unknown argument: $1" ;;
  esac
done

require_git_repo
require_clean_tree
require_subtree
ensure_ds_store_policy
require_clean_tree

if [ "$MODE" = "install" ]; then
  [ -e "$PREFIX" ] && die "$PREFIX already exists. Use update."
  subtree_add
  soft_uncommit_last
else
  [ -d "$PREFIX" ] || die "$PREFIX not found. Use install."
  subtree_pull
  soft_uncommit_last
fi
