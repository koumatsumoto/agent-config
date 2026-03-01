#!/usr/bin/env bash
set -euo pipefail

remove_item() {
  local target="$1"

  if [[ ! -e "$target" && ! -L "$target" ]]; then
    echo "skip: $target"
    return 0
  fi

  rm -rf "${target}.bak"
  mv "$target" "${target}.bak"
  echo "backup: ${target}.bak"
  echo "removed: $target"
}

echo "Clean Claude + Codex configuration"
remove_item "$HOME/.claude/rules"
remove_item "$HOME/.claude/skills"
remove_item "$HOME/.agents/skills"
echo "done"
