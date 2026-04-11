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

# Note: The following are intentionally NOT removed by clean.sh:
#   - ~/.claude/, ~/.codex/, ~/.agents/ directory permissions
#     (these directories may contain credentials and other sensitive files)
echo "Clean Claude + Codex configuration"
remove_item "$HOME/.claude/CLAUDE.md"
remove_item "$HOME/.claude/rules"
remove_item "$HOME/.claude/skills"
remove_item "$HOME/.claude/keybindings.json"
remove_item "$HOME/.claude/statusline.sh"
remove_item "$HOME/.codex/AGENTS.md"
remove_item "$HOME/.codex/config.toml"
remove_item "$HOME/.agents/skills"
echo "done"
