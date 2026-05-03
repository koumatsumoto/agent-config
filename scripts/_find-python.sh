#!/usr/bin/env bash
# Resolve a Python ≥ 3.12 interpreter command name (e.g. python3 / python).
# Prints the resolved command name to stdout. Exits non-zero on failure with
# a human-readable error on stderr.
#
# Used by install.sh / clean.sh / scripts/verify-install.sh so they work both
# on POSIX (where the convention is `python3`) and on Windows under Git Bash
# (where the official Python installer only exposes `python`).
set -euo pipefail

for candidate in python3 python; do
  if command -v "$candidate" >/dev/null 2>&1 \
    && "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)' >/dev/null 2>&1; then
    echo "$candidate"
    exit 0
  fi
done

echo "ERROR: Python 3.12+ not found in PATH (tried: python3, python)" >&2
exit 1
