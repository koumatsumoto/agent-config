#!/usr/bin/env python3
"""Shallow-merge a settings.json template into an existing settings.json.

Existing user values win over template values for shared top-level keys.
A backup is written only when the merged content actually differs from
the existing file. Invalid JSON in the destination is treated as empty
(the destination is replaced wholesale, with a backup of the original).

Usage:
    merge-settings-json.py <template.json> <destination.json>
"""

from __future__ import annotations

import json
import os
import sys


def main() -> int:
    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} <template> <destination>", file=sys.stderr)
        return 2

    src, dest = sys.argv[1], sys.argv[2]

    with open(src, encoding="utf-8") as f:
        template = json.load(f)
    if not isinstance(template, dict):
        print(f"error: template must be a JSON object: {src}", file=sys.stderr)
        return 2

    existing_text: str | None = None
    existing: dict = {}
    if os.path.exists(dest):
        with open(dest, encoding="utf-8") as f:
            existing_text = f.read()
        if existing_text.strip():
            try:
                parsed = json.loads(existing_text)
                if isinstance(parsed, dict):
                    existing = parsed
                else:
                    print(
                        f"warn: {dest} is not a JSON object; treating as empty",
                        file=sys.stderr,
                    )
            except json.JSONDecodeError as exc:
                print(
                    f"warn: {dest} is not valid JSON ({exc}); treating as empty",
                    file=sys.stderr,
                )

    merged = {**template, **existing}
    new_text = json.dumps(merged, indent=2, ensure_ascii=False) + "\n"

    if existing_text == new_text:
        print(f"ok: {dest}")
        return 0

    if existing_text is not None:
        bak = f"{dest}.bak"
        with open(bak, "w", encoding="utf-8") as f:
            f.write(existing_text)
        os.chmod(bak, 0o600)
        print(f"backup: {bak}")

    tmp = f"{dest}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(new_text)
    os.chmod(tmp, 0o600)
    os.replace(tmp, dest)
    label = "created" if existing_text is None else "merged"
    print(f"{label}: {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
