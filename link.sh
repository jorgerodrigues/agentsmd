#!/bin/sh
# Points the agent instruction files at this repo's agents.md, and each agent's
# skills directory at this repo's skills.
# Run after cloning, on macOS or Linux: ./link.sh [--dry-run]

set -eu

REPO=$(cd "$(dirname "$0")" && pwd -P)
SOURCE="$REPO/agents.md"

DRY_RUN=false
case "${1:-}" in
  "") ;;
  --dry-run) DRY_RUN=true ;;
  *) echo "usage: $(basename "$0") [--dry-run]" >&2; exit 2 ;;
esac

# Path of $1 written relative to directory $2, so the links carry no machine-specific prefix.
# Both must be physical paths: the kernel resolves a relative symlink against its
# parent's real location, not the lexical path used to reach it.
relpath() {
  target=$1
  base=$2
  up=""
  while [ "$base" != "/" ] && [ "${target#"$base"/}" = "$target" ]; do
    base=$(dirname "$base")
    up="../$up"
  done
  [ "$base" = "/" ] && base=""
  printf '%s%s\n' "$up" "${target#"$base"/}"
}

# backup <path> [dest-base]. Pass dest-base to park the copy outside the directory
# $path lives in — a skill backup left among the skills would still be scanned, and
# its SKILL.md would register a stale second copy of the same skill name.
backup() {
  path=$1
  dest="${2:-$path}.backup"
  [ -e "$dest" ] && dest="${2:-$path}.backup.$(date +%Y%m%d%H%M%S)"
  # A directory has to move rather than copy: `ln -s` pointed at an existing
  # directory creates the link inside it instead of replacing it.
  if [ -d "$path" ]; then
    $DRY_RUN || mv "$path" "$dest"
    verb=moved
  else
    $DRY_RUN || cp "$path" "$dest"
    verb=copied
  fi
  if $DRY_RUN; then
    echo "  would be $verb to $dest"
  else
    echo "  $verb to $dest"
  fi
}

[ -f "$SOURCE" ] || { echo "no agents.md in $REPO" >&2; exit 1; }

# Each link is created only when its parent directory already exists.
# Both Claude paths are needed: $HOME/CLAUDE.md is picked up by the project
# instruction ancestor walk, which only reaches it for repos under $HOME, while
# $HOME/.claude/CLAUDE.md is user memory and loads from anywhere. Inside $HOME
# they resolve to the same physical file, so the overlap costs nothing.
for link in "$HOME/AGENTS.md" "$HOME/CLAUDE.md" "$HOME/.claude/CLAUDE.md" "$HOME/.codex/AGENTS.md"; do
  dir=$(dirname "$link")
  if [ ! -d "$dir" ]; then
    echo "skip  $link ($dir does not exist)"
    continue
  fi

  target=$(relpath "$SOURCE" "$(cd "$dir" && pwd -P)")

  if [ -L "$link" ] && [ "$(readlink "$link")" = "$target" ]; then
    echo "ok    $link"
    continue
  fi

  if [ -L "$link" ]; then
    echo "relink $link (was -> $(readlink "$link"))"
  elif [ -e "$link" ]; then
    echo "move  $link"
    backup "$link"
  else
    echo "new   $link"
  fi

  $DRY_RUN || ln -sfn "$target" "$link"
done

# Each skill in skills/ is linked into every agent's skills directory. The agent's
# own config directory must exist, but skills/ under it may not yet: it is created
# on first install, so a fresh machine would otherwise silently link nothing.
for skills_dir in "$HOME/.claude/skills" "$HOME/.codex/skills"; do
  agent_dir=$(dirname "$skills_dir")
  if [ ! -d "$agent_dir" ]; then
    echo "skip  $skills_dir ($agent_dir does not exist)"
    continue
  fi
  if [ ! -d "$skills_dir" ]; then
    echo "mkdir $skills_dir"
    $DRY_RUN || mkdir -p "$skills_dir"
    $DRY_RUN && continue
  fi

  for skill in "$REPO"/skills/*/; do
    skill=${skill%/}
    [ -d "$skill" ] || continue

    link="$skills_dir/$(basename "$skill")"
    target=$(relpath "$skill" "$(cd "$skills_dir" && pwd -P)")

    if [ -L "$link" ] && [ "$(readlink "$link")" = "$target" ]; then
      echo "ok    $link"
      continue
    fi

    if [ -L "$link" ]; then
      echo "relink $link (was -> $(readlink "$link"))"
    elif [ -e "$link" ]; then
      echo "move  $link"
      backup "$link" "$agent_dir/$(basename "$skill")"
    else
      echo "new   $link"
    fi

    $DRY_RUN || ln -sfn "$target" "$link"
  done
done

$DRY_RUN && echo "(dry run — nothing changed)"
exit 0
