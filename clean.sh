#!/usr/bin/env bash
# Thin wrapper around the Python harness. Supports Linux and macOS directly,
# plus Windows through Git Bash.
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY=$("$REPO_ROOT/scripts/_find-python.sh") || exit 1
exec "$PY" "$REPO_ROOT/scripts/cli.py" clean "$@"
