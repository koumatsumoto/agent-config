#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

failures=0

check_file() {
  local src="$1"
  local dest="$2"

  if [[ ! -e "$dest" ]]; then
    echo "missing: $dest"
    failures=$((failures + 1))
    return
  fi

  if diff -rq "$src" "$dest" >/dev/null 2>&1; then
    echo "ok: $dest"
  else
    echo "drift: $dest"
    failures=$((failures + 1))
  fi
}

check_mode() {
  local path="$1"
  local expected="$2"

  if [[ ! -e "$path" ]]; then
    echo "missing: $path"
    failures=$((failures + 1))
    return
  fi

  local actual
  actual="$(stat -c '%a' "$path" 2>/dev/null || stat -f '%Lp' "$path" 2>/dev/null || echo '?')"
  if [[ "$actual" == "$expected" ]]; then
    echo "mode ok: $path ($actual)"
  else
    echo "mode drift: $path (expected $expected, got $actual)"
    failures=$((failures + 1))
  fi
}

echo "Verify Claude + Codex configuration"

check_file "$REPO_ROOT/templates/CLAUDE.md" "$HOME/.claude/CLAUDE.md"
check_file "$REPO_ROOT/templates/rules" "$HOME/.claude/rules"
check_file "$REPO_ROOT/templates/skills" "$HOME/.claude/skills"
check_file "$REPO_ROOT/templates/keybindings.json" "$HOME/.claude/keybindings.json"
check_file "$REPO_ROOT/templates/statusline.sh" "$HOME/.claude/statusline.sh"
check_file "$REPO_ROOT/templates/AGENTS.md" "$HOME/.codex/AGENTS.md"
check_file "$REPO_ROOT/templates/config.toml" "$HOME/.codex/config.toml"
check_file "$REPO_ROOT/templates/skills" "$HOME/.agents/skills"

check_mode "$HOME/.claude" "700"
check_mode "$HOME/.codex" "700"
check_mode "$HOME/.agents" "700"
check_mode "$HOME/.claude/keybindings.json" "600"
check_mode "$HOME/.claude/statusline.sh" "700"

if [[ "$failures" -gt 0 ]]; then
  echo "verify failed: $failures issue(s)"
  exit 1
fi

echo "verify ok"
