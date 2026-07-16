#!/usr/bin/env bash
# Resolve a Python ≥ 3.12 interpreter command name (e.g. python3 / python).
# Prints the resolved command name to stdout. Exits non-zero on failure with
# a human-readable error on stderr.
#
# Used by install.sh / clean.sh / scripts/verify-install.sh. Linux and macOS
# commonly expose `python3`; Windows commonly exposes `python`. Probing both
# keeps the wrappers platform-neutral while enforcing one runtime contract.
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
