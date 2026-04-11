#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

failures=0
checks=0

record_failure() {
  local message="$1"
  echo "$message"
  failures=$((failures + 1))
}

record_check() {
  checks=$((checks + 1))
}

check_file() {
  local src="$1"
  local dest="$2"
  record_check

  if [[ ! -e "$dest" ]]; then
    record_failure "missing: $dest"
    return
  fi

  if ! diff -q "$src" "$dest" >/dev/null 2>&1; then
    record_failure "drift: $dest"
  fi
}

check_mode() {
  local path="$1"
  local expected="$2"
  record_check

  if [[ ! -e "$path" ]]; then
    record_failure "missing: $path"
    return
  fi

  local actual
  actual="$(stat -c '%a' "$path" 2>/dev/null || stat -f '%Lp' "$path" 2>/dev/null || echo '?')"
  if [[ "$actual" != "$expected" ]]; then
    record_failure "mode drift: $path (expected $expected, got $actual)"
  fi
}

check_managed_tree() {
  local src_root="$1"
  local dest_root="$2"
  local dir_mode="$3"
  local file_mode="$4"
  local rel_path
  local src_path
  local dest_path

  record_check
  if [[ ! -e "$dest_root" ]]; then
    record_failure "missing: $dest_root"
    return
  fi
  check_mode "$dest_root" "$dir_mode"

  while IFS= read -r rel_path; do
    src_path="$src_root/$rel_path"
    dest_path="$dest_root/$rel_path"
    if [[ -d "$src_path" ]]; then
      check_mode "$dest_path" "$dir_mode"
    elif [[ -f "$src_path" ]]; then
      check_file "$src_path" "$dest_path"
      check_mode "$dest_path" "$file_mode"
    fi
  done < <(cd "$src_root" && find . -mindepth 1 \( -type d -o -type f \) | sed 's#^\./##' | sort)
}

echo "Verify Claude + Codex configuration"

check_file "$REPO_ROOT/templates/CLAUDE.md" "$HOME/.claude/CLAUDE.md"
check_file "$REPO_ROOT/templates/keybindings.json" "$HOME/.claude/keybindings.json"
check_file "$REPO_ROOT/templates/statusline.sh" "$HOME/.claude/statusline.sh"
check_file "$REPO_ROOT/templates/AGENTS.md" "$HOME/.codex/AGENTS.md"
check_file "$REPO_ROOT/templates/config.toml" "$HOME/.codex/config.toml"

check_mode "$HOME/.claude" "700"
check_mode "$HOME/.claude/CLAUDE.md" "600"
check_mode "$HOME/.claude/keybindings.json" "600"
check_mode "$HOME/.claude/statusline.sh" "700"
check_managed_tree "$REPO_ROOT/templates/rules" "$HOME/.claude/rules" "700" "600"
check_managed_tree "$REPO_ROOT/templates/skills" "$HOME/.claude/skills" "700" "600"

check_mode "$HOME/.codex" "700"
check_mode "$HOME/.codex/AGENTS.md" "600"
check_mode "$HOME/.codex/config.toml" "600"

check_mode "$HOME/.agents" "700"
check_managed_tree "$REPO_ROOT/templates/skills" "$HOME/.agents/skills" "700" "600"

if [[ "$failures" -gt 0 ]]; then
  echo "verify failed: $failures issue(s) across $checks check(s)"
  exit 1
fi

echo "verify ok: $checks check(s)"
