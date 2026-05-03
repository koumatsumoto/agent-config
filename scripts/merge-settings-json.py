#!/usr/bin/env python3
"""Backwards-compatible entry point for agent_config.merge_settings.

Prefer `python -m agent_config.merge_settings`. This wrapper exists so
that older callers using the old script path keep working.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent_config.merge_settings import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main(sys.argv))
