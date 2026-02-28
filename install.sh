#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TS="$(date +%Y%m%d%H%M%S)"

install_item() {
  local src="$1"
  local dest="$2"

  mkdir -p "$(dirname "$dest")"
  if [[ -e "$dest" || -L "$dest" ]]; then
    mv "$dest" "${dest}.bak.${TS}"
  fi

  if ln -s "$src" "$dest" 2>/dev/null; then
    echo "linked: $dest -> $src"
    return 0
  fi

  if [[ -d "$src" ]]; then
    cp -R "$src" "$dest"
  else
    cp "$src" "$dest"
  fi
  echo "copied: $src -> $dest"
}

echo "Install Claude + Codex configuration"
install_item "$REPO_ROOT/templates/CLAUDE.md" "$HOME/.claude/CLAUDE.md"
install_item "$REPO_ROOT/templates/agents" "$HOME/.claude/agents"
install_item "$REPO_ROOT/templates/rules" "$HOME/.claude/rules"
install_item "$REPO_ROOT/templates/skills" "$HOME/.claude/skills"

install_item "$REPO_ROOT/templates/CLAUDE.md" "$HOME/.codex/AGENTS.md"
install_item "$REPO_ROOT/templates/config.toml" "$HOME/.codex/config.toml"
install_item "$REPO_ROOT/templates/skills" "$HOME/.agents/skills"
echo "done"
