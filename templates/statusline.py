#!/usr/bin/env python3
"""Claude Code status line — rich two-line layout.

Reads the session JSON that Claude Code pipes on stdin and prints up to two
lines:

    Line 1: 🤖 model [agent] [·effort] [[style]] │ bar pct% (used/window) $cost [⟲ cacheN%] [⇌ api ◷ wall]
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
- ⟲% = cache_read / (input + cache_creation + cache_read): the share of this
  turn's input served cheaply from the prompt cache.
- ⇌ is cumulative API (network) time; ◷ is wall-clock time. The four metric
  glyphs ($ ⟲ ⇌ ◷) are text-presentation symbols: they render in the terminal
  foreground color (one uniform color) and occupy a single cell, sidestepping
  the width/overlap quirks of emoji like ⏱ that lack a variation selector.
"""

from __future__ import annotations

import json
import math
import os
import re
import stat
import subprocess
import sys
import tempfile
import time
import unicodedata
from datetime import datetime
from pathlib import Path

# --- ANSI ------------------------------------------------------------------- #
RESET = "\033[0m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
RED_BG = "\033[41;97m"  # red background + bright white

GIT_CACHE_TTL_SEC = 5
GIT_CACHE_MAX_BYTES = 4096
STDIN_LIMIT_BYTES = 65536
GIT_TIMEOUT_SEC = 2
BAR_WIDTH = 6
MODEL_NAME_MAX = 128
SEP = " │ "

_CSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
_OSC_RE = re.compile(r"\x1b\].*?(?:\x07|\x1b\\)")
_SGR_REMNANT_RE = re.compile(r"\[[0-9;]*[mGHJKsu]")
_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f-\x9f]")
# Model display names append a context-window note (e.g. "Opus 5 (1M
# context)") that the bar's used/window readout already shows; strip it.
_MODEL_CTX_RE = re.compile(r"\s*\([^)]*context[^)]*\)\s*$", re.IGNORECASE)


# --- payload access --------------------------------------------------------- #
def _reject_constant(_: str) -> None:
    """Map JSON NaN/Infinity/-Infinity to None so numeric coercion stays safe.

    json.loads accepts these non-finite literals by default; left as floats they
    would blow up downstream int()/round() calls.
    """
    return None


def read_payload() -> dict[str, object]:
    """Read size-limited stdin and parse JSON; return {} on any failure."""
    try:
        raw = sys.stdin.buffer.read(STDIN_LIMIT_BYTES)
    except (OSError, ValueError):
        return {}
    try:
        data = json.loads(raw, parse_constant=_reject_constant)
    except (json.JSONDecodeError, ValueError, RecursionError):
        # RecursionError: deeply nested JSON overflows the C scanner.
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
    """Coerce to a finite float; non-numeric, non-finite, or out-of-range inputs
    yield 0.0 (an arbitrary-precision int can overflow float())."""
    if isinstance(value, bool):
        return 0.0
    if isinstance(value, (int, float, str)):
        try:
            num = float(value)
        except (OverflowError, ValueError):
            return 0.0
        return num if math.isfinite(num) else 0.0
    return 0.0


def sanitize(text: str) -> str:
    """Strip ANSI escape sequences and control bytes from external strings."""
    text = _CSI_RE.sub("", text)
    text = _CONTROL_RE.sub("", text)
    return _SGR_REMNANT_RE.sub("", text)


def safe_osc8_uri(url: str) -> str:
    """Return `url` only if it is a plain http(s) link safe to embed in an
    OSC 8 hyperlink, else ''. Control bytes (including the ESC/BEL that could
    close the escape early and inject terminal commands) are stripped first,
    then the scheme is allowlisted (CWE-150)."""
    url = _CONTROL_RE.sub("", url)
    return url if url.startswith(("https://", "http://")) else ""


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
    """Display width of `text`, ignoring ANSI/OSC escapes. East-Asian wide and
    fullwidth code points count as 2 cells and zero-width combining marks as 0,
    so line-2 truncation matches what the terminal actually renders."""
    stripped = _OSC_RE.sub("", _CSI_RE.sub("", text))
    width = 0
    for ch in stripped:
        if unicodedata.combining(ch):
            continue
        width += 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
    return width


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


def output_style_segment(name: str) -> str:
    """Show a non-default output style as `[name]`.

    Claude Code's built-in "default" style is the null state, so tagging it is
    noise; only a custom style earns a segment. Square brackets set it apart
    from the ·effort marker that precedes it in the model cluster.
    """
    return f" [{name}]" if name and name.lower() != "default" else ""


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


def metrics_segment(payload: dict[str, object]) -> str:
    """`$cost ⟲ cache ⇌ api ◷ wall` — order: cost, cache, API time, wall time.

    Glyphs are text-presentation symbols (uniform terminal color). The thin
    ASCII $ hugs its value; ⟲/⇌/◷ are padded with a space from theirs so the
    cluster does not look cramped.
    """
    parts = [fmt_cost(as_num(dig(payload, "cost", "total_cost_usd")))]
    cache = cache_segment(payload)
    if cache:
        parts.append(cache)
    api = as_num(dig(payload, "cost", "total_api_duration_ms"))
    wall = as_num(dig(payload, "cost", "total_duration_ms"))
    # Sub-second cumulative times render as a meaningless "0s"; show only >=1s.
    if api >= 1000:
        parts.append(f"⇌ {fmt_duration(api)}")
    if wall >= 1000:
        parts.append(f"◷ {fmt_duration(wall)}")
    return " ".join(parts)


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
    return f"⟲ {int(round(100 * read / total))}%"


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
    """Environment with repo/config redirection vars cleared (hardening).

    A session payload cannot set our environment, but the surrounding shell
    might; stripping these stops an injected GIT_* var from pointing our
    read-only queries at attacker-controlled config, hooks, object stores, or a
    proxy/ssh command. GIT_CONFIG_NOSYSTEM neutralizes /etc/gitconfig too.
    """
    env = dict(os.environ)
    for var in (
        "GIT_DIR", "GIT_WORK_TREE", "GIT_CONFIG", "GIT_CONFIG_GLOBAL",
        "GIT_CONFIG_SYSTEM", "GIT_CONFIG_COUNT", "GIT_EXEC_PATH",
        "GIT_EXTERNAL_DIFF", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_PROXY_COMMAND", "GIT_SSH_COMMAND", "GIT_PAGER",
    ):
        env.pop(var, None)
    # GIT_TRACE* would append diagnostics to an inherited (possibly hostile)
    # path; drop every variant rather than enumerate them.
    for key in [k for k in env if k.startswith("GIT_TRACE")]:
        env.pop(key, None)
    env["GIT_OPTIONAL_LOCKS"] = "0"
    env["GIT_CONFIG_NOSYSTEM"] = "1"
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


def _read_git_cache(cache: Path) -> dict[str, object] | None:
    """Return fresh, well-formed cached git info, or None to recompute.

    Refuses to follow a symlink at the cache path (O_NOFOLLOW) and caps the read
    so a file planted in the shared temp dir cannot be slurped wholesale
    (CWE-59 / CWE-377). A non-dict JSON body is treated as a cache miss.
    """
    try:
        if time.time() - cache.stat().st_mtime >= GIT_CACHE_TTL_SEC:
            return None
        # O_NOFOLLOW rejects a symlink; O_NONBLOCK + S_ISREG reject a planted
        # FIFO/device (a read-only open of a FIFO would otherwise block).
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
        fd = os.open(cache, flags)
        try:
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                return None
            raw = os.read(fd, GIT_CACHE_MAX_BYTES)
        finally:
            os.close(fd)
        data = json.loads(raw, parse_constant=_reject_constant)
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def _write_git_cache(cache: Path, info: dict[str, object]) -> None:
    """Atomically replace the cache via a private temp file in the same dir.

    mkstemp creates with O_EXCL|0600 so it never follows a pre-planted symlink;
    os.replace then swaps it in, discarding any symlink sitting at the target.
    """
    try:
        fd, tmp_name = tempfile.mkstemp(dir=str(cache.parent), prefix=cache.name + ".")
    except OSError:
        return
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(info))
        os.replace(tmp_name, cache)
    except OSError:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass


def git_info(payload: dict[str, object]) -> dict[str, object]:
    """Cached git lookup keyed by session_id (cache TTL: GIT_CACHE_TTL_SEC)."""
    cwd = as_str(dig(payload, "workspace", "current_dir")) or as_str(payload.get("cwd"))
    session_id = as_str(payload.get("session_id"))
    if not session_id:
        return compute_git(cwd)

    safe = re.sub(r"[^A-Za-z0-9_-]", "", session_id)[:64]
    if not safe:
        return compute_git(cwd)  # avoid a shared, predictable cache filename
    cache = Path(tempfile.gettempdir()) / f"statusline-git-{safe}"
    cached = _read_git_cache(cache)
    if cached is not None:
        return cached

    info = compute_git(cwd)
    _write_git_cache(cache, info)
    return info


# --- assembly --------------------------------------------------------------- #
def build_line1(payload: dict[str, object]) -> str:
    # Cap length before the regex: bounds _MODEL_CTX_RE backtracking on a
    # pathologically long display_name (ReDoS guard) — real names are short.
    model = sanitize(as_str(dig(payload, "model", "display_name")))[:MODEL_NAME_MAX]
    model = _MODEL_CTX_RE.sub("", model) or "?"
    head = f"🤖 {model}"
    agent = sanitize(as_str(dig(payload, "agent", "name")))
    if agent:
        head += f" {agent}"
    head += effort_segment(sanitize(as_str(dig(payload, "effort", "level"))))
    head += output_style_segment(sanitize(as_str(dig(payload, "output_style", "name"))))
    # Metrics ($cost ⟲ cache ⇌ api ◷ wall) ride with the context bar separated
    # by a space; only the model↔metrics divider keeps the │.
    body = f"{context_segment(payload)} {metrics_segment(payload)}"
    return SEP.join([head, body])


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

    # as_num() yields a finite float (0.0 for non-finite / overflowing input),
    # so int() below is always safe and an absurd PR number simply drops.
    pr_num = as_num(dig(payload, "pr", "number"))
    if pr_num >= 1:
        pr_url = safe_osc8_uri(as_str(dig(payload, "pr", "url")))
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
    """Shorten an over-wide line2 by trimming the branch name with an ellipsis.

    `over` is a display-cell budget, so drop trailing code points by their
    rendered width (wide/CJK = 2 cells) rather than by count; otherwise a CJK
    branch trims roughly twice as hard as the column budget requires.
    """
    if columns <= 0 or visible_len(line) <= columns:
        return line
    over = visible_len(line) - columns + 1
    match = re.match(r"(🌳 )(\S+)(.*)", line, re.DOTALL)
    if not match:
        return line
    prefix, branch, rest = match.groups()
    removed = 0
    keep = len(branch)
    while keep > 1 and removed < over:
        keep -= 1
        removed += 2 if unicodedata.east_asian_width(branch[keep]) in ("W", "F") else 1
    return f"{prefix}{branch[:keep]}…{rest}"


def main() -> int:
    # Force UTF-8 so the glyphs render on a Windows pipe (whose default codec is
    # the ANSI codepage, which cannot encode 🤖/🌳); errors="replace" then makes
    # a write physically unable to raise. getattr keeps it safe if stdout is not
    # a reconfigurable TextIOWrapper.
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure):
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            pass
    try:
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
    except Exception:
        # A status line must never spew a traceback into the prompt; degrade to
        # an ASCII-only marker (safe even if the reconfigure above failed).
        sys.stdout.write("?\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
