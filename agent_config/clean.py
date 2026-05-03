"""Move installed templates aside (.bak) and remove them.

Replaces the legacy clean.sh. The user's settings.json is intentionally
preserved because it carries values that the user may have customised on
top of the merged template.
"""

from __future__ import annotations

import sys
from pathlib import Path

from agent_config import fs, paths


def clean(home: Path) -> int:
    print("Clean Claude + Codex configuration")
    for target in paths.clean_targets(home):
        result = fs.remove_with_backup(target)
        if result == "skipped":
            print(f"skip: {target}")
        else:
            print(f"backup: {target}.bak")
            print(f"removed: {target}")
    print("done")
    return 0


def main(argv: list[str]) -> int:
    home = Path.home()
    return clean(home)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
