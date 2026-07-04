#!/usr/bin/env python3
"""agent-config management CLI.

Installs / cleans / verifies the Claude Code + Codex CLI templates under the
user's home directory, plus a standalone settings.json shallow-merge command.
Cross-platform (POSIX + Windows), stdlib-only, security-hardened.

Usage:
    python scripts/cli.py install
    python scripts/cli.py clean
    python scripts/cli.py verify
    python scripts/cli.py merge <template.json> <destination.json>

On POSIX, directories / regular files / executables get 0o700 / 0o600 / 0o700
modes. On Windows the modes are skipped because NTFS does not honour POSIX
bits; isolation there relies on the inherited user-profile ACL.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

POSIX = os.name == "posix"
DIR_MODE = 0o700
FILE_MODE = 0o600
EXEC_MODE = 0o700

# scripts/cli.py -> scripts -> repo root.
REPO_ROOT = Path(__file__).resolve().parent.parent


# --------------------------------------------------------------------------- #
# Install manifest: the single source of truth for what is deployed where.
# --------------------------------------------------------------------------- #
@dataclass(frozen=True, slots=True)
class FileSpec:
    src_rel: str           # relative to REPO_ROOT
    dest_rel: str          # relative to home
    mode: int
    is_executable: bool = False


@dataclass(frozen=True, slots=True)
class TreeSpec:
    src_rel: str           # relative to REPO_ROOT
    dest_rel: str          # relative to home
    dir_mode: int = 0o700
    file_mode: int = 0o600
    # When True, install prunes deployed files/dirs absent from the template, so
    # managed directories mirror the source. Top-level entries directly under the
    # tree root (no source counterpart) are preserved as possibly user-added.
    prune: bool = True


# Files that are full-template overwrites (with .bak backup). CLAUDE.md /
# AGENTS.md are the shared agent guidelines and are owned by the template: each
# install refreshes them so edits to the repo propagate. Machine-local overrides
# belong in a sibling *.local.md, which the installer never writes.
TEMPLATE_FILES: tuple[FileSpec, ...] = (
    FileSpec("templates/CLAUDE.md", ".claude/CLAUDE.md", 0o600),
    FileSpec("templates/statusline.py", ".claude/statusline.py", 0o700, is_executable=True),
    FileSpec("templates/subagent-statusline.py", ".claude/subagent-statusline.py", 0o700, is_executable=True),
    FileSpec("templates/AGENTS.md", ".codex/AGENTS.md", 0o600),
    FileSpec("templates/config.toml", ".codex/config.toml", 0o600),
)

# Directory trees synced recursively (with per-file .bak backup).
TEMPLATE_TREES: tuple[TreeSpec, ...] = (
    TreeSpec("templates/rules", ".claude/rules"),
    TreeSpec("templates/skills", ".claude/skills"),
    TreeSpec("templates/skills", ".agents/skills"),
)

# settings.json — special handling: shallow merge instead of overwrite.
SETTINGS_TEMPLATE_REL = "templates/settings.json"
SETTINGS_DEST_REL = ".claude/settings.json"

# settings.json keys whose `command` launches a deployed status-line script,
# mapped to that script's path relative to home. The installer rewrites these
# per-platform so the command is actually runnable on the target OS.
STATUSLINE_COMMANDS: tuple[tuple[str, str], ...] = (
    ("statusLine", ".claude/statusline.py"),
    ("subagentStatusLine", ".claude/subagent-statusline.py"),
)

# Top-level home subdirectories that the installer may write into.
INSTALL_HOME_DIRS: tuple[str, ...] = (".claude", ".codex", ".agents")

# Skill directories shipped previously but no longer maintained. prune_tree keeps
# top-level skill dirs with no source counterpart (they may be user-added), so a
# decommissioned skill would otherwise linger after install. The installer removes
# each by explicit name (with .bak backup) from every skills tree during the
# migration window.
DECOMMISSIONED_SKILLS: tuple[str, ...] = (
    "code-review",
    "doc-review",
    "intent-review",
    "open-html",
    "quality-review",
    "review-loop",
)


def clean_targets(home: Path) -> list[Path]:
    """Paths that clean() removes (with .bak backup).

    settings.json is intentionally excluded because it is a shallow merge of
    template and user-managed keys, not a pure template copy.
    """
    out: list[Path] = []
    for spec in TEMPLATE_FILES:
        out.append(home / spec.dest_rel)
    for spec in TEMPLATE_TREES:
        out.append(home / spec.dest_rel)
    return out


# --------------------------------------------------------------------------- #
# File operations with security defaults.
# --------------------------------------------------------------------------- #
def is_posix() -> bool:
    return POSIX


def chmod_if_posix(path: Path, mode: int) -> None:
    """chmod on POSIX, no-op on Windows."""
    if POSIX:
        os.chmod(path, mode)


def ensure_secure_dir(path: Path, mode: int = DIR_MODE) -> None:
    """Create a directory if missing and apply restrictive permissions on POSIX."""
    path.mkdir(parents=True, exist_ok=True)
    chmod_if_posix(path, mode)


def is_within(child: Path, parent: Path) -> bool:
    """Return True if `child` resolves inside `parent` (after symlink resolution)."""
    try:
        child.resolve(strict=False).relative_to(parent.resolve(strict=False))
        return True
    except ValueError:
        return False


def assert_within(child: Path, parent: Path) -> None:
    if not is_within(child, parent):
        raise PermissionError(f"refusing to operate outside {parent}: {child}")


def atomic_write_bytes(path: Path, data: bytes, mode: int = FILE_MODE) -> None:
    """Atomically write `data` to `path` with the given POSIX mode.

    Uses tempfile.mkstemp in the destination directory so os.replace is atomic
    on the same filesystem. The temp file gets a unique name (no predictable
    `.tmp` suffix) which closes a TOCTOU/symlink window on the temp path.
    """
    parent = path.parent
    parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_str = tempfile.mkstemp(prefix=path.name + ".", dir=str(parent))
    tmp = Path(tmp_str)
    moved = False
    try:
        if POSIX:
            os.fchmod(fd, mode)
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        os.replace(tmp, path)
        chmod_if_posix(path, mode)
        moved = True
    finally:
        if not moved:
            try:
                tmp.unlink()
            except FileNotFoundError:
                pass


def atomic_write_text(path: Path, text: str, mode: int = FILE_MODE) -> None:
    atomic_write_bytes(path, text.encode("utf-8"), mode=mode)


def same_content(src: Path, dest: Path) -> bool:
    """Compare regular-file contents byte-for-byte. Symlinks/dirs return False."""
    if src.is_symlink() or dest.is_symlink():
        return False
    if not src.is_file() or not dest.is_file():
        return False
    return src.read_bytes() == dest.read_bytes()


def backup(path: Path) -> Path | None:
    """Move existing path to path.bak (single generation). Return the .bak Path or None."""
    if not (path.exists() or path.is_symlink()):
        return None
    bak = path.with_name(path.name + ".bak")
    if bak.exists() or bak.is_symlink():
        if bak.is_dir() and not bak.is_symlink():
            shutil.rmtree(bak)
        else:
            bak.unlink()
    os.rename(path, bak)
    return bak


def install_file(src: Path, dest: Path, mode: int = FILE_MODE) -> str:
    """Install a single file with backup. Return one of: ok | copied | replaced.

    - "ok": dest already matches src; nothing changed.
    - "copied": dest did not exist; created from src.
    - "replaced": dest existed and was backed up to dest.bak.
    """
    if not src.is_file() or src.is_symlink():
        raise FileNotFoundError(f"source not found or not a regular file: {src}")

    if dest.exists() and not dest.is_symlink() and same_content(src, dest):
        return "ok"

    bak = backup(dest)
    atomic_write_bytes(dest, src.read_bytes(), mode=mode)
    return "replaced" if bak is not None else "copied"


def install_tree(
    src_root: Path,
    dest_root: Path,
    *,
    dir_mode: int = DIR_MODE,
    file_mode: int = FILE_MODE,
    boundary: Path | None = None,
) -> list[tuple[str, Path]]:
    """Recursively install a directory tree.

    Uses `os.walk(followlinks=False)` so a symlink loop in the template tree
    cannot cause infinite recursion (Python 3.13's `Path.rglob` follows
    symlinks by default, which would otherwise hang during materialisation).
    Any symlink encountered in src is rejected outright.

    `boundary`, when given, restricts every dest path to live under it after
    symlink resolution. The check is applied before any filesystem mutation.
    Returns a list of (status, dest_path) entries for files only.
    """
    if not src_root.is_dir():
        raise FileNotFoundError(f"source tree not found: {src_root}")

    if boundary is not None:
        assert_within(dest_root, boundary)
    ensure_secure_dir(dest_root, dir_mode)

    results: list[tuple[str, Path]] = []
    for dirpath, dirnames, filenames in os.walk(src_root, followlinks=False):
        dirnames.sort()
        filenames.sort()
        for name in dirnames:
            src = Path(dirpath) / name
            if src.is_symlink():
                raise PermissionError(f"refusing to follow symlink in template: {src}")
            dest = dest_root / src.relative_to(src_root)
            if boundary is not None:
                assert_within(dest, boundary)
            ensure_secure_dir(dest, dir_mode)
        for name in filenames:
            src = Path(dirpath) / name
            if src.is_symlink():
                raise PermissionError(f"refusing to follow symlink in template: {src}")
            dest = dest_root / src.relative_to(src_root)
            if boundary is not None:
                assert_within(dest, boundary)
            status = install_file(src, dest, mode=file_mode)
            results.append((status, dest))
    return results


def prune_tree(src_root: Path, dest_root: Path, *, boundary: Path) -> list[Path]:
    """Remove deployed files/dirs absent from the template, with .bak backup.

    Makes managed directories mirror the source: an entry is pruned when it lives
    inside a repo-managed directory (one that exists under src_root) but is not
    present under src_root. Entries directly under dest_root with no src
    counterpart — a file or directory the user added — are preserved (never
    removed; such directories are not descended into).

    Returns the pruned dest paths (each backed up to <path>.bak); `.bak` entries
    are left alone.
    """
    if not dest_root.is_dir():
        return []
    pruned: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(dest_root, topdown=True, followlinks=False):
        dest_dir = Path(dirpath)
        src_dir = src_root / dest_dir.relative_to(dest_root)
        keep_dirs: list[str] = []
        for name in sorted(dirnames):
            if name.endswith(".bak"):
                continue  # leave single-generation backups
            if (src_dir / name).is_dir():
                keep_dirs.append(name)  # managed → descend and keep in sync
            elif dest_dir == dest_root:
                continue  # top-level unit with no source → user-added; never touch
            else:
                dest_sub = dest_dir / name  # orphan subdir inside a managed dir
                assert_within(dest_sub, boundary)
                backup(dest_sub)
                pruned.append(dest_sub)
        dirnames[:] = keep_dirs  # descend only into managed subdirs
        for name in sorted(filenames):
            if name.endswith(".bak") or (src_dir / name).exists():
                continue
            if dest_dir == dest_root:
                continue  # top-level file with no source → user-added; never touch
            dest_file = dest_dir / name
            assert_within(dest_file, boundary)
            backup(dest_file)
            pruned.append(dest_file)
    return pruned


def remove_decommissioned_skills(home: Path) -> list[Path]:
    """Remove deployed skill dirs that are no longer shipped (with .bak backup).

    prune_tree preserves top-level entries with no source counterpart (possibly
    user-added), so decommissioned skills are removed by explicit name here.
    """
    removed: list[Path] = []
    skill_roots = [
        home / t.dest_rel for t in TEMPLATE_TREES if t.src_rel == "templates/skills"
    ]
    for root in skill_roots:
        for name in DECOMMISSIONED_SKILLS:
            target = root / name
            if target.is_dir() or target.is_symlink():
                remove_with_backup(target)
                removed.append(target)
    return removed


def remove_with_backup(path: Path) -> str:
    """Move path to path.bak (single generation) and delete the original location.

    Returns one of: skipped | backed_up.
    """
    if not (path.exists() or path.is_symlink()):
        return "skipped"
    bak = path.with_name(path.name + ".bak")
    if bak.exists() or bak.is_symlink():
        if bak.is_dir() and not bak.is_symlink():
            shutil.rmtree(bak)
        else:
            bak.unlink()
    os.rename(path, bak)
    return "backed_up"


# --------------------------------------------------------------------------- #
# settings.json: per-platform status-line command.
# --------------------------------------------------------------------------- #
def statusline_command(home: Path, script_rel: str, *, posix: bool, python: str) -> str:
    """Build a runnable status-line `command` string for the target platform.

    POSIX: a `~`-relative path. The shebang + executable bit launch the script
    OS-independently and re-resolve the interpreter via PATH on every run, which
    survives the interpreter moving as long as it stays on PATH.

    Windows: `cmd.exe` neither expands `~` nor executes a bare `.py`, so the
    interpreter must be invoked explicitly with the absolute script path. Both
    tokens are quoted to tolerate spaces (e.g. `C:/Program Files/...`).
    """
    if posix:
        return f"~/{script_rel}"
    script = (home / script_rel).as_posix()
    return f'"{python}" "{script}"'


def apply_statusline_commands(
    template: dict[str, object], home: Path, *, posix: bool, python: str
) -> dict[str, object]:
    """Return a copy of `template` with status-line commands rewritten for the OS.

    Only sections that already declare a `command` are touched, so the template
    stays the single source of truth for which status lines exist. On POSIX the
    rewritten value equals the template's `~/...` literal, making this a no-op
    there (and keeping re-runs idempotent).
    """
    out = dict(template)
    for key, script_rel in STATUSLINE_COMMANDS:
        section = out.get(key)
        if isinstance(section, dict) and "command" in section:
            updated = dict(section)
            updated["command"] = statusline_command(
                home, script_rel, posix=posix, python=python
            )
            out[key] = updated
    return out


# --------------------------------------------------------------------------- #
# settings.json shallow merge.
# --------------------------------------------------------------------------- #
def read_existing(path: Path) -> tuple[str | None, dict[str, object]]:
    """Return (raw_text_or_None, parsed_dict). Invalid/non-object → empty dict."""
    try:
        text = path.read_text(encoding="utf-8")
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


def merge(template: dict[str, object], existing: dict[str, object]) -> dict[str, object]:
    """Shallow merge: template values win for the keys the template declares.

    The template is the source of truth for every top-level key it sets, so
    edits to those keys propagate to existing installs on re-run. Keys the
    template does not declare (e.g. runtime/UI-managed `theme`, `model`,
    `enabledPlugins`) are preserved from the existing file.
    """
    return {**existing, **template}


def render(merged: dict[str, object]) -> str:
    return json.dumps(merged, indent=2, ensure_ascii=False) + "\n"


def merge_into(
    template_path: Path,
    dest: Path,
    *,
    transform: Callable[[dict[str, object]], dict[str, object]] | None = None,
) -> str:
    """Apply a shallow merge from template_path into dest.

    `transform`, when given, is applied to the parsed template object before the
    merge. The installer uses it to rewrite status-line commands per-platform;
    the standalone `merge` subcommand passes none (generic merge).

    Returns one of: ok | created | merged.
    """
    template_data = json.loads(template_path.read_text(encoding="utf-8"))
    if not isinstance(template_data, dict):
        raise ValueError(f"template must be a JSON object: {template_path}")
    if transform is not None:
        template_data = transform(template_data)

    existing_text, existing = read_existing(dest)
    new_text = render(merge(template_data, existing))

    if existing_text == new_text:
        return "ok"

    if existing_text is not None:
        bak = dest.with_name(dest.name + ".bak")
        atomic_write_text(bak, existing_text, mode=FILE_MODE)

    atomic_write_text(dest, new_text, mode=FILE_MODE)
    return "created" if existing_text is None else "merged"


# --------------------------------------------------------------------------- #
# verify: installed templates match the repo source-of-truth.
# --------------------------------------------------------------------------- #
class VerifyReport:
    def __init__(self) -> None:
        self.failures: list[str] = []
        self.checks = 0

    def record(self, ok: bool, message: str) -> None:
        self.checks += 1
        if not ok:
            self.failures.append(message)

    def fail_count(self) -> int:
        return len(self.failures)


def _check_file(report: VerifyReport, src: Path, dest: Path) -> None:
    report.record(dest.exists(), f"missing: {dest}")
    if dest.exists():
        report.record(same_content(src, dest), f"drift: {dest}")


def _check_mode(report: VerifyReport, path: Path, expected: int) -> None:
    if not is_posix():
        return  # NTFS does not honour POSIX modes
    if not path.exists():
        report.record(False, f"missing: {path}")
        return
    actual = path.stat().st_mode & 0o777
    report.record(
        actual == expected,
        f"mode drift: {path} (expected {oct(expected)}, got {oct(actual)})",
    )


def _check_tree(report: VerifyReport, src_root: Path, dest_root: Path,
                dir_mode: int, file_mode: int) -> None:
    if not dest_root.exists():
        report.record(False, f"missing: {dest_root}")
        return
    _check_mode(report, dest_root, dir_mode)
    for src in sorted(src_root.rglob("*")):
        rel = src.relative_to(src_root)
        dest = dest_root / rel
        if src.is_dir():
            _check_mode(report, dest, dir_mode)
        elif src.is_file():
            _check_file(report, src, dest)
            _check_mode(report, dest, file_mode)


def _read_json_object(report: VerifyReport, path: Path, label: str) -> dict[str, object] | None:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        report.record(False, f"missing: {path}")
        return None
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        report.record(False, f"invalid json: {path} ({exc})")
        return None
    is_object = isinstance(data, dict)
    report.record(is_object, f"{label} must be a JSON object: {path}")
    if not is_object:
        return None
    return data


def _check_settings_contract(report: VerifyReport, template: Path, dest: Path) -> None:
    template_data = _read_json_object(report, template, "settings template")
    dest_data = _read_json_object(report, dest, "settings.json")
    if template_data is None or dest_data is None:
        return
    for key in sorted(template_data):
        report.record(key in dest_data, f"settings missing template key: {dest} ({key})")


def verify(home: Path, repo_root: Path = REPO_ROOT) -> VerifyReport:
    report = VerifyReport()
    print("Verify Claude + Codex configuration")

    for spec in TEMPLATE_FILES:
        src = repo_root / spec.src_rel
        dest = home / spec.dest_rel
        _check_file(report, src, dest)
        _check_mode(report, dest, spec.mode)

    for sub in INSTALL_HOME_DIRS:
        _check_mode(report, home / sub, DIR_MODE)

    for tspec in TEMPLATE_TREES:
        src_root = repo_root / tspec.src_rel
        dest_root = home / tspec.dest_rel
        _check_tree(report, src_root, dest_root, tspec.dir_mode, tspec.file_mode)

    settings_dest = home / SETTINGS_DEST_REL
    report.record(settings_dest.exists(), f"missing: {settings_dest}")
    _check_mode(report, settings_dest, FILE_MODE)
    _check_settings_contract(report, repo_root / SETTINGS_TEMPLATE_REL, settings_dest)

    return report


# --------------------------------------------------------------------------- #
# install / clean.
# --------------------------------------------------------------------------- #
def refuse_root() -> None:
    """Refuse to run as root on POSIX. (No EUID concept on Windows.)"""
    if is_posix() and hasattr(os, "geteuid") and os.geteuid() == 0:
        print(
            "ERROR: Do not run this installer as root or with sudo. Run as your user.",
            file=sys.stderr,
        )
        sys.exit(1)


def install(home: Path, repo_root: Path = REPO_ROOT) -> int:
    """Install all templates into `home`. Returns process exit code."""
    # Pre-create home subdirs that we own, with restrictive perms.
    boundary_dirs: list[Path] = []
    for sub in INSTALL_HOME_DIRS:
        d = home / sub
        ensure_secure_dir(d, DIR_MODE)
        boundary_dirs.append(d)

    print("Install Claude + Codex configuration")

    for spec in TEMPLATE_FILES:
        src = repo_root / spec.src_rel
        dest = home / spec.dest_rel
        # Guard: destination must live inside one of the install dirs.
        if not any(is_within(dest, b) for b in boundary_dirs):
            raise PermissionError(f"refusing to write outside install dirs: {dest}")
        status = install_file(src, dest, mode=spec.mode)
        print(f"{status}: {dest}")

    for tspec in TEMPLATE_TREES:
        src_root = repo_root / tspec.src_rel
        dest_root = home / tspec.dest_rel
        # Tree boundary is whichever managed dir contains dest_root.
        boundary = next((b for b in boundary_dirs if is_within(dest_root, b)), None)
        if boundary is None:
            raise PermissionError(f"refusing to write tree outside install dirs: {dest_root}")
        results = install_tree(
            src_root,
            dest_root,
            dir_mode=tspec.dir_mode,
            file_mode=tspec.file_mode,
            boundary=boundary,
        )
        for status, dest in results:
            print(f"{status}: {dest}")
        if tspec.prune:
            for dest in prune_tree(src_root, dest_root, boundary=boundary):
                print(f"pruned: {dest}")

    for dest in remove_decommissioned_skills(home):
        print(f"removed (decommissioned): {dest}")

    # `sys.executable` is the interpreter running this installer: guaranteed to
    # exist and be >= 3.12, and on Windows it is exactly the python that must be
    # named explicitly in the status-line command.
    python = Path(sys.executable).as_posix()
    settings_status = merge_into(
        repo_root / SETTINGS_TEMPLATE_REL,
        home / SETTINGS_DEST_REL,
        transform=lambda tpl: apply_statusline_commands(
            tpl, home, posix=POSIX, python=python
        ),
    )
    if settings_status == "ok":
        print(f"ok: {home / SETTINGS_DEST_REL}")
    elif settings_status == "created":
        print(f"created: {home / SETTINGS_DEST_REL}")
    else:
        print(f"backup: {home / SETTINGS_DEST_REL}.bak")
        print(f"merged: {home / SETTINGS_DEST_REL}")

    # Re-apply directory perms (in case rsync-style operations widened them).
    for sub in INSTALL_HOME_DIRS:
        chmod_if_posix(home / sub, DIR_MODE)

    return 0


def clean(home: Path) -> int:
    print("Clean Claude + Codex configuration")
    for target in clean_targets(home):
        result = remove_with_backup(target)
        if result == "skipped":
            print(f"skip: {target}")
        else:
            print(f"backup: {target}.bak")
            print(f"removed: {target}")
    print("done")
    return 0


# --------------------------------------------------------------------------- #
# CLI dispatch.
# --------------------------------------------------------------------------- #
USAGE = "usage: cli.py <install|clean|verify|merge> [args]"


def _verify_cli(home: Path) -> int:
    report = verify(home)
    if report.failures:
        for msg in report.failures:
            print(msg)
        print(f"verify failed: {report.fail_count()} issue(s) across {report.checks} check(s)")
        return 1
    print(f"verify ok: {report.checks} check(s)")
    return 0


def _merge_cli(prog: str, rest: list[str]) -> int:
    if len(rest) != 2:
        print(f"usage: {prog} merge <template> <destination>", file=sys.stderr)
        return 2
    template_path = Path(rest[0])
    dest = Path(rest[1])
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


def main(argv: list[str]) -> int:
    prog = argv[0] if argv else "cli.py"
    args = argv[1:]
    if not args:
        print(USAGE, file=sys.stderr)
        return 2

    command, rest = args[0], args[1:]
    match command:
        case "install":
            refuse_root()
            return install(Path.home())
        case "clean":
            return clean(Path.home())
        case "verify":
            return _verify_cli(Path.home())
        case "merge":
            return _merge_cli(prog, rest)
        case _:
            print(f"unknown command: {command}", file=sys.stderr)
            print(USAGE, file=sys.stderr)
            return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
