#!/usr/bin/env bash
# Thin wrapper around the Python harness. Windows users invoke
# `python -m agent_config.verify_install` directly.
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHONPATH="$REPO_ROOT" exec python3 -m agent_config.verify_install "$@"
