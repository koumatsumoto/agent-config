#!/usr/bin/env bash
# Thin wrapper around the Python harness. Works on POSIX shells and on
# Git Bash for Windows (which exposes `python` only).
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY=$("$REPO_ROOT/scripts/_find-python.sh") || exit 1
exec "$PY" "$REPO_ROOT/scripts/cli.py" verify "$@"
