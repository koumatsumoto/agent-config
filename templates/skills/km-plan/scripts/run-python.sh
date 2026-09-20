#!/usr/bin/env bash
# Run the requested script with the first available Python 3.9+ interpreter.
set -euo pipefail

if (($# == 0)); then
  echo "run-python: Python script is required" >&2
  exit 2
fi

for candidate in python3 python; do
  if command -v "$candidate" >/dev/null 2>&1 \
    && "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)' >/dev/null 2>&1; then
    exec "$candidate" "$@"
  fi
done

echo "run-python: Python 3.9+ not found in PATH" >&2
exit 1
