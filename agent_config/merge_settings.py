"""Shallow-merge a settings.json template into an existing settings.json.

Existing user values win over template values for shared top-level keys.
A backup is written only when the merged content actually differs from
the existing file. Invalid or missing JSON in the destination is treated
as empty; if the existing text was non-empty it is backed up first.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from agent_config import fs


def read_existing(path: Path) -> tuple[str | None, dict[str, object]]:
    """Return (raw_text_or_None, parsed_dict). Invalid/non-object → empty dict."""
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None, {}
    try:
        parsed = json.loads(text) if text.strip() else {}
    except json.JSONDecodeError as exc:
        print(
            f"warn: {path} is not valid JSON ({exc}); treating as empty",
            file=sys.stderr,
        )
        return text, {}
    if not isinstance(parsed, dict):
        print(
            f"warn: {path} is not a JSON object; treating as empty",
            file=sys.stderr,
        )
        return text, {}
    return text, parsed


def merge(template: dict[str, object], existing: dict[str, object]) -> dict[str, object]:
    """Shallow merge: existing user values win for shared top-level keys."""
    return {**template, **existing}


def render(merged: dict[str, object]) -> str:
    return json.dumps(merged, indent=2, ensure_ascii=False) + "\n"


def merge_into(template_path: Path, dest: Path) -> str:
    """Apply a shallow merge from template_path into dest.

    Returns one of: ok | created | merged.
    """
    template_data = json.loads(template_path.read_text(encoding="utf-8"))
    if not isinstance(template_data, dict):
        raise ValueError(f"template must be a JSON object: {template_path}")

    existing_text, existing = read_existing(dest)
    new_text = render(merge(template_data, existing))

    if existing_text == new_text:
        return "ok"

    if existing_text is not None:
        bak = dest.with_name(dest.name + ".bak")
        fs.atomic_write_text(bak, existing_text, mode=fs.FILE_MODE)

    fs.atomic_write_text(dest, new_text, mode=fs.FILE_MODE)
    return "created" if existing_text is None else "merged"


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(f"usage: {argv[0]} <template> <destination>", file=sys.stderr)
        return 2

    template_path = Path(argv[1])
    dest = Path(argv[2])

    try:
        result = merge_into(template_path, dest)
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if result == "ok":
        print(f"ok: {dest}")
    elif result == "created":
        print(f"created: {dest}")
    elif result == "merged":
        print(f"backup: {dest}.bak")
        print(f"merged: {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
