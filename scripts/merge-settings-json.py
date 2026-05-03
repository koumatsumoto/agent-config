#!/usr/bin/env python3
"""Shallow-merge a settings.json template into an existing settings.json.

Existing user values win over template values for shared top-level keys.
A backup is written only when the merged content actually differs from
the existing file. Invalid or missing JSON in the destination is treated
as empty; if the existing text was non-empty it is backed up first.

Usage:
    merge-settings-json.py <template.json> <destination.json>
"""

from __future__ import annotations

import json
import os
import sys
import tempfile


def read_existing(path: str) -> tuple[str | None, dict]:
    try:
        with open(path, encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        return None, {}
    try:
        parsed = json.loads(text) if text.strip() else {}
    except json.JSONDecodeError as exc:
        print(f"warn: {path} is not valid JSON ({exc}); treating as empty", file=sys.stderr)
        return text, {}
    if not isinstance(parsed, dict):
        print(f"warn: {path} is not a JSON object; treating as empty", file=sys.stderr)
        return text, {}
    return text, parsed


def write_secure(path: str, text: str) -> None:
    """Atomically write `text` to `path` with 0600 permissions."""
    parent = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix=os.path.basename(path) + ".", dir=parent)
    moved = False
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(text)
        os.replace(tmp, path)
        moved = True
    finally:
        if not moved:
            try:
                os.unlink(tmp)
            except FileNotFoundError:
                pass


def main() -> int:
    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} <template> <destination>", file=sys.stderr)
        return 2

    src, dest = sys.argv[1], sys.argv[2]
    with open(src, encoding="utf-8") as f:
        template = json.load(f)

    existing_text, existing = read_existing(dest)
    merged = {**template, **existing}
    new_text = json.dumps(merged, indent=2, ensure_ascii=False) + "\n"

    if existing_text == new_text:
        print(f"ok: {dest}")
        return 0

    if existing_text is not None:
        write_secure(f"{dest}.bak", existing_text)
        print(f"backup: {dest}.bak")

    write_secure(dest, new_text)
    print(f"{'created' if existing_text is None else 'merged'}: {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
