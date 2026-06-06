#!/usr/bin/env python3
"""Claude Code status line — rich two-line layout.

Reads the session JSON that Claude Code pipes on stdin and prints up to two
lines:

    Line 1: 🤖 model [agent] [·effort] │ bar pct% (used/window) [♻️cacheN%] │ $cost ⏱wall 🌐api
    Line 2: 🌳 branch N files +A/-R [🔗PR#num] │ 5h:N% ~reset │ 7d:N% ~DAY.hAM

Maintainer notes (why it is shaped this way):
- Cross-platform: pure stdlib, no jq. Works under Linux/macOS and Windows
  (Git Bash / PowerShell-launched python). Time and weekday formatting is done
  manually because strftime "%-I" is glibc-only.
- Fast path: the script runs on every status update (300 ms debounced), so the
  git subprocess result is cached per `session_id` for a few seconds.
- Untrusted input: model/branch/agent values are sanitized to strip control and
  ANSI bytes before rendering, preventing escape-sequence injection from a
  repository or session payload.
- Context tokens "used" follows Claude Code's own `used_percentage`: input
  tokens only (input + cache read + cache write), output excluded.
- ♻️% = cache_read / (input + cache_creation + cache_read): the share of this
  turn's input served cheaply from the prompt cache.
- ⏱ is wall-clock time; 🌐 is cumulative API (network) time.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

# --- ANSI ------------------------------------------------------------------- #
RESET = "\033[0m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
RED_BG = "\033[41;97m"  # red background + bright white

GIT_CACHE_TTL_SEC = 5
STDIN_LIMIT_BYTES = 65536
GIT_TIMEOUT_SEC = 2
BAR_WIDTH = 6
SEP = " │ "

_CSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
_SGR_REMNANT_RE = re.compile(r"\[[0-9;]*[mGHJKsu]")
_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f-\x9f]")


# --- payload access --------------------------------------------------------- #
def read_payload() -> dict[str, object]:
    """Read size-limited stdin and parse JSON; return {} on any failure."""
    try:
        raw = sys.stdin.buffer.read(STDIN_LIMIT_BYTES)
    except (OSError, ValueError):
        return {}
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def dig(data: object, *path: str) -> object:
    """Walk nested dicts by key path; return None if any hop is missing."""
    cur = data
    for key in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    return cur


def as_str(value: object) -> str:
    return value if isinstance(value, str) else ""


def as_num(value: object) -> float:
    if isinstance(value, bool):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return 0.0
    return 0.0


def sanitize(text: str) -> str:
    """Strip ANSI escape sequences and control bytes from external strings."""
    text = _CSI_RE.sub("", text)
    text = _CONTROL_RE.sub("", text)
    return _SGR_REMNANT_RE.sub("", text)


# --- formatting ------------------------------------------------------------- #
def fmt_tokens(n: float) -> str:
    """120 -> '120', 90000 -> '90k', 1500000 -> '1.5M'."""
    n = int(n)
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}".rstrip("0").rstrip(".") + "M"
    if n >= 1_000:
        return f"{n // 1000}k"
    return str(n)


def fmt_window(size: float) -> str:
    size = int(size)
    if size >= 1_000_000:
        return f"{size // 1_000_000}M"
    if size >= 1_000:
        return f"{size // 1000}k"
    return str(size) if size else ""


def fmt_cost(usd: float) -> str:
    return f"${usd:.2f}"


def fmt_duration(ms: float) -> str:
    sec = int(ms) // 1000
    if sec < 60:
        return f"{sec}s"
    if sec < 3600:
        return f"{sec // 60}m"
    return f"{sec // 3600}h{(sec % 3600) // 60}m"


def fmt_reset(epoch: float, *, with_day: bool = False) -> str:
    """Unix epoch -> '6PM' or 'MON.3PM' (local time, locale-independent)."""
    if epoch <= 0:
        return ""
    try:
        dt = datetime.fromtimestamp(epoch)
    except (OverflowError, OSError, ValueError):
        return ""
    hour12 = dt.hour % 12 or 12
    ampm = "AM" if dt.hour < 12 else "PM"
    clock = f"{hour12}{ampm}"
    if with_day:
        days = ("MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN")
        return f"{days[dt.weekday()]}.{clock}"
    return clock


def visible_len(text: str) -> int:
    """Length of `text` ignoring ANSI/OSC escape sequences."""
    stripped = _CSI_RE.sub("", text)
    stripped = re.sub(r"\x1b\].*?(\x07|\x1b\\)", "", stripped)
    return len(stripped)


# --- segments --------------------------------------------------------------- #
def context_color(pct: int) -> str:
    if pct >= 90:
        return RED_BG
    if pct >= 80:
        return RED
    if pct >= 50:
        return YELLOW
    return GREEN


def rate_color(pct: int) -> str:
    if pct >= 80:
        return RED
    if pct >= 50:
        return YELLOW
    return ""


def effort_segment(level: str) -> str:
    return f" ·{level}" if level else ""


def context_segment(payload: dict[str, object]) -> str:
    pct = int(round(as_num(dig(payload, "context_window", "used_percentage"))))
    pct = max(0, min(100, pct))
    used = as_num(dig(payload, "context_window", "total_input_tokens"))
    window = fmt_window(as_num(dig(payload, "context_window", "context_window_size")))

    filled = pct * BAR_WIDTH // 100
    bar = context_color(pct) + "█" * filled + "░" * (BAR_WIDTH - filled) + RESET

    if used > 0 and window:
        detail = f" ({fmt_tokens(used)}/{window})"
    elif window:
        detail = f" ({window})"
    else:
        detail = ""
    return f"{bar} {pct}%{detail}"


def cost_segment(payload: dict[str, object]) -> str:
    cost = fmt_cost(as_num(dig(payload, "cost", "total_cost_usd")))
    wall = as_num(dig(payload, "cost", "total_duration_ms"))
    api = as_num(dig(payload, "cost", "total_api_duration_ms"))
    out = cost
    if wall > 0:
        out += f" ⏱{fmt_duration(wall)}"
        if api > 0:
            out += f" 🌐{fmt_duration(api)}"
    return out


def cache_segment(payload: dict[str, object]) -> str:
    usage = dig(payload, "context_window", "current_usage")
    if not isinstance(usage, dict):
        return ""
    fresh = as_num(usage.get("input_tokens"))
    created = as_num(usage.get("cache_creation_input_tokens"))
    read = as_num(usage.get("cache_read_input_tokens"))
    total = fresh + created + read
    if total <= 0:
        return ""
    return f"♻️{int(round(100 * read / total))}%"


def rate_segment(payload: dict[str, object], window: str, label: str, *, with_day: bool) -> str:
    """Return e.g. '5h:32% ~6PM', or '' when this rate window is absent."""
    node = dig(payload, "rate_limits", window)
    if not isinstance(node, dict) or "used_percentage" not in node:
        return ""
    pct = int(round(as_num(node.get("used_percentage"))))
    reset = fmt_reset(as_num(node.get("resets_at")), with_day=with_day)
    color = rate_color(pct)
    body = f"{color}{label}:{pct}%{RESET}" if color else f"{label}:{pct}%"
    return f"{body} ~{reset}" if reset else body


# --- git -------------------------------------------------------------------- #
def git_env() -> dict[str, str]:
    """Environment with repo/config redirection vars cleared (hardening)."""
    env = dict(os.environ)
    for var in (
        "GIT_DIR", "GIT_WORK_TREE", "GIT_CONFIG", "GIT_CONFIG_GLOBAL",
        "GIT_EXEC_PATH", "GIT_EXTERNAL_DIFF",
    ):
        env.pop(var, None)
    env["GIT_OPTIONAL_LOCKS"] = "0"
    return env


def run_git(args: list[str], cwd: str) -> str:
    try:
        result = subprocess.run(
            ["git", "-c", "core.fsmonitor=", *args],
            cwd=cwd or None,
            env=git_env(),
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT_SEC,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return result.stdout if result.returncode == 0 else ""


def compute_git(cwd: str) -> dict[str, object]:
    """Branch + tracked-file change counts for `cwd`. {} when not a repo."""
    inside = run_git(["rev-parse", "--is-inside-work-tree"], cwd).strip()
    if inside != "true":
        return {}
    branch = run_git(["rev-parse", "--abbrev-ref", "HEAD"], cwd).strip()
    if branch == "HEAD":
        branch = ""  # detached
    files = added = removed = 0
    for line in run_git(["diff", "--numstat", "HEAD"], cwd).splitlines()[:10000]:
        parts = line.split("\t")
        if len(parts) < 2:
            continue
        files += 1
        if parts[0].isdigit():
            added += int(parts[0])
        if parts[1].isdigit():
            removed += int(parts[1])
    return {"branch": branch, "files": files, "added": added, "removed": removed}


def git_info(payload: dict[str, object]) -> dict[str, object]:
    """Cached git lookup keyed by session_id (cache TTL: GIT_CACHE_TTL_SEC)."""
    cwd = as_str(dig(payload, "workspace", "current_dir")) or as_str(payload.get("cwd"))
    session_id = as_str(payload.get("session_id"))
    if not session_id:
        return compute_git(cwd)

    safe = re.sub(r"[^A-Za-z0-9_-]", "", session_id)[:64]
    cache = Path(tempfile.gettempdir()) / f"statusline-git-{safe}"
    try:
        if time.time() - cache.stat().st_mtime < GIT_CACHE_TTL_SEC:
            return json.loads(cache.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass

    info = compute_git(cwd)
    try:
        tmp = cache.with_name(cache.name + f".{os.getpid()}")
        tmp.write_text(json.dumps(info), encoding="utf-8")
        os.replace(tmp, cache)
    except OSError:
        pass
    return info


# --- assembly --------------------------------------------------------------- #
def build_line1(payload: dict[str, object]) -> str:
    model = sanitize(as_str(dig(payload, "model", "display_name"))) or "?"
    head = f"🤖 {model}"
    agent = sanitize(as_str(dig(payload, "agent", "name")))
    if agent:
        head += f" {agent}"
    head += effort_segment(sanitize(as_str(dig(payload, "effort", "level"))))
    ctx = context_segment(payload)
    cache = cache_segment(payload)
    if cache:
        ctx = f"{ctx} {cache}"
    return SEP.join([head, ctx, cost_segment(payload)])


def git_segment(payload: dict[str, object]) -> str:
    branch = sanitize(as_str(dig(payload, "worktree", "branch")))
    info = git_info(payload)
    if not branch:
        branch = sanitize(as_str(info.get("branch")))
    if not branch and not info:
        return ""
    if not branch:
        branch = "(detached)"

    out = f"🌳 {branch}"
    files = int(as_num(info.get("files")))
    if files > 0:
        out += f" {files} files"
        added = int(as_num(info.get("added")))
        removed = int(as_num(info.get("removed")))
        if added or removed:
            out += f" +{added}/-{removed}"

    pr_num = dig(payload, "pr", "number")
    if isinstance(pr_num, (int, float)) and not isinstance(pr_num, bool):
        pr_url = as_str(dig(payload, "pr", "url"))
        label = f"PR#{int(pr_num)}"
        link = f"\033]8;;{pr_url}\a🔗{label}\033]8;;\a" if pr_url else f"🔗{label}"
        out += f" {link}"
    return out


def build_line2(payload: dict[str, object]) -> str:
    parts = [
        git_segment(payload),
        rate_segment(payload, "five_hour", "5h", with_day=False),
        rate_segment(payload, "seven_day", "7d", with_day=True),
    ]
    return SEP.join(p for p in parts if p)


def truncate_branch(line: str, columns: int) -> str:
    """Shorten an over-wide line2 by trimming the branch name with an ellipsis."""
    if columns <= 0 or visible_len(line) <= columns:
        return line
    over = visible_len(line) - columns + 1
    match = re.match(r"(🌳 )(\S+)(.*)", line, re.DOTALL)
    if not match:
        return line
    prefix, branch, rest = match.groups()
    keep = max(1, len(branch) - over)
    return f"{prefix}{branch[:keep]}…{rest}"


def main() -> int:
    payload = read_payload()
    try:
        columns = int(os.environ.get("COLUMNS", "0"))
    except ValueError:
        columns = 0

    lines = [build_line1(payload)]
    line2 = build_line2(payload)
    if line2:
        lines.append(truncate_branch(line2, columns))

    sys.stdout.write("\n".join(lines) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
