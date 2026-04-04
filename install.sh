#!/usr/bin/env bash
set -euo pipefail

if [[ "${EUID:-$(id -u)}" -eq 0 ]]; then
  echo "ERROR: Do not run this script as root or with sudo." >&2
  echo "Run as: bash install.sh" >&2
  exit 1
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Restrict default permissions for newly created files/directories
umask 077

# Ensure ~/.claude/ exists with secure permissions before any file operations
mkdir -p "$HOME/.claude" && chmod 700 "$HOME/.claude"

install_item() {
  local src="$1"
  local dest="$2"

  mkdir -p "$(dirname "$dest")"

  # 既存のコピー先と内容が同一ならスキップ
  if [[ -e "$dest" ]] && ! [[ -L "$dest" ]] && diff -rq "$src" "$dest" >/dev/null 2>&1; then
    echo "ok: $dest"
    return 0
  fi

  # 既存ファイル/ディレクトリがあればバックアップ（単一世代）
  if [[ -e "$dest" || -L "$dest" ]]; then
    rm -rf "${dest}.bak"
    mv "$dest" "${dest}.bak"
    echo "backup: ${dest}.bak"
  fi

  # コピー
  if [[ -d "$src" ]]; then
    cp -R "$src" "$dest"
  else
    cp "$src" "$dest"
  fi
  echo "copied: $dest"
}

install_executable() {
  local src="$1"
  local dest="$2"
  install_item "$src" "$dest"
  chmod 700 "$dest"
}

install_template_file() {
  local name="$1"
  local dest_dir="$2"
  install_item "$REPO_ROOT/templates/$name" "$dest_dir/$name"
}

echo "Install Claude + Codex configuration"
install_template_file "CLAUDE.md" "$HOME/.claude"
install_item "$REPO_ROOT/templates/rules" "$HOME/.claude/rules"
install_item "$REPO_ROOT/templates/skills" "$HOME/.claude/skills"
install_template_file "keybindings.json" "$HOME/.claude"
chmod 600 "$HOME/.claude/keybindings.json" || echo "WARN: failed to set permissions on keybindings.json" >&2
install_executable "$REPO_ROOT/templates/statusline.sh" "$HOME/.claude/statusline.sh"

# Harden other deployment directories (umask 077 covers new dirs, chmod for existing)
chmod 700 "$HOME/.codex/" 2>/dev/null || true
chmod 700 "$HOME/.agents/" 2>/dev/null || true

install_template_file "AGENTS.md" "$HOME/.codex"
install_template_file "config.toml" "$HOME/.codex"
install_item "$REPO_ROOT/templates/skills" "$HOME/.agents/skills"

# ~/.claude/ permissions already set at script start (umask 077 + chmod 700)
echo "done"
