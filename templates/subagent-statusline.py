#!/usr/bin/env python3
"""Claude Code subagent status line.

Renders the row body for each subagent shown in the agent panel below the
prompt. Claude Code pipes a single JSON object on stdin containing the base hook
fields plus `columns` and a `tasks` array (each task: id, name, type, status,
description, label, startTime, tokenCount, tokenSamples, cwd).

We emit one JSON line per row we want to override, in the form
`{"id": "<task id>", "content": "<row body>"}`. Rows we do not emit keep their
default rendering. `content` is rendered as-is (ANSI colors / OSC 8 allowed).

Layout: `<status glyph> <name> · <token count> tok`.
"""

from __future__ import annotations

import json
import re
import sys

_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f-\x9f]")
_CSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")

STATUS_GLYPH = {
    "completed": "✓",
    "done": "✓",
    "success": "✓",
    "failed": "✗",
    "error": "✗",
    "running": "•",
    "in_progress": "•",
    "active": "•",
    "pending": "·",
    "queued": "·",
}


def sanitize(text: str) -> str:
    return _CONTROL_RE.sub("", _CSI_RE.sub("", text))


def as_str(value: object) -> str:
    return value if isinstance(value, str) else ""


def fmt_tokens(value: object) -> str:
    n = int(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else 0
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}".rstrip("0").rstrip(".") + "M"
    if n >= 1_000:
        return f"{n // 1000}k"
    return str(n)


def row(task: dict[str, object]) -> str | None:
    task_id = task.get("id")
    if not isinstance(task_id, str) or not task_id:
        return None
    name = sanitize(as_str(task.get("name"))) or sanitize(as_str(task.get("type"))) or "agent"
    glyph = STATUS_GLYPH.get(as_str(task.get("status")).lower(), "")
    head = f"{glyph} {name}".strip()
    content = f"{head} · {fmt_tokens(task.get('tokenCount'))} tok"
    return json.dumps({"id": task_id, "content": content})


def main() -> int:
    try:
        payload = json.loads(sys.stdin.buffer.read(65536))
    except (OSError, ValueError, json.JSONDecodeError):
        return 0
    if not isinstance(payload, dict):
        return 0
    tasks = payload.get("tasks")
    if not isinstance(tasks, list):
        return 0
    for task in tasks:
        if isinstance(task, dict):
            line = row(task)
            if line:
                sys.stdout.write(line + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
