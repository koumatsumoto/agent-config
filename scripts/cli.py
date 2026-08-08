#!/usr/bin/env python3
"""agent-config management CLI.

Installs / cleans / verifies the Claude Code + Codex CLI templates under the
user's home directory, plus a standalone settings.json shallow-merge command.
Supports Linux, macOS, and Windows; stdlib-only and security-hardened.

Platform behavior is capability-based: Linux and macOS share POSIX filesystem
and process semantics, while native Windows gets the small set of adaptations
required by NTFS and cmd.exe.

Usage:
    python scripts/cli.py install [--claude-dir <dir>] [--qwen]
    python scripts/cli.py clean [--claude-dir <dir>] [--qwen]
    python scripts/cli.py verify [--claude-dir <dir>] [--qwen]
    python scripts/cli.py merge <template.json> <destination.json>

`--claude-dir` installs the Claude Code slice of the templates into another
configuration directory (the one CLAUDE_CONFIG_DIR names), so a second profile
tracks the same templates as `~/.claude`.

`--qwen` is additive: it adds the Qwen Code component (`~/.qwen`) to the usual
destinations, with the same meaning in install / clean / verify. Without it
nothing under `~/.qwen` is read or written. It cannot be combined with
`--claude-dir`, which re-roots a single Claude configuration slice: one command
must not mutate two unrelated roots.

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
from dataclasses import dataclass, replace
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
@dataclass(frozen=True)
class FileSpec:
    src_rel: str           # relative to REPO_ROOT
    dest_rel: str          # relative to home
    mode: int
    is_executable: bool = False


@dataclass(frozen=True)
class TreeSpec:
    src_rel: str           # relative to REPO_ROOT
    dest_rel: str          # relative to home
    dir_mode: int = 0o700
    file_mode: int = 0o600
    # When True, install prunes deployed files/dirs absent from the template, so
    # managed directories mirror the source. Top-level entries directly under the
    # tree root (no source counterpart) are preserved as possibly user-added.
    prune: bool = True


# The one canonical agent guideline. Every tool reads it under the file name it
# expects, so the same source is deployed to each of those names and the
# deployed copies stay byte-for-byte identical.
GUIDELINE_TEMPLATE_REL = "templates/CLAUDE.md"

# Files that are full-template overwrites (with .bak backup). The agent
# guideline is owned by the template: each install refreshes it so edits to the
# repo propagate. Machine-local overrides belong in a sibling *.local.md, which
# the installer never writes.
TEMPLATE_FILES: tuple[FileSpec, ...] = (
    FileSpec(GUIDELINE_TEMPLATE_REL, ".claude/CLAUDE.md", 0o600),
    FileSpec("templates/statusline.py", ".claude/statusline.py", 0o700, is_executable=True),
    FileSpec("templates/subagent-statusline.py", ".claude/subagent-statusline.py", 0o700, is_executable=True),
    FileSpec(GUIDELINE_TEMPLATE_REL, ".codex/AGENTS.md", 0o600),
    FileSpec("templates/config.toml", ".codex/config.toml", 0o600),
    FileSpec("templates/codex/readonly.config.toml", ".codex/readonly.config.toml", 0o600),
)

# Directory trees synced recursively (with per-file .bak backup).
TEMPLATE_TREES: tuple[TreeSpec, ...] = (
    TreeSpec("templates/rules", ".claude/rules"),
    TreeSpec("templates/skills", ".claude/skills"),
    TreeSpec("templates/output-styles", ".claude/output-styles"),
    TreeSpec("templates/skills", ".agents/skills"),
    TreeSpec("templates/codex-rules", ".codex/rules"),
)

# settings.json — special handling: shallow merge instead of overwrite.
SETTINGS_TEMPLATE_REL = "templates/settings.json"
SETTINGS_DEST_REL = ".claude/settings.json"

# Qwen Code settings.json — shallow merge, no statusline transform.
QWEN_SETTINGS_TEMPLATE_REL = "templates/qwen-settings.json"
QWEN_SETTINGS_DEST_REL = ".qwen/settings.json"


@dataclass(frozen=True)
class SettingsSpec:
    src_rel: str           # relative to REPO_ROOT
    dest_rel: str          # relative to the layout root
    # Claude Code launches the status line itself, so its command must name a
    # path that resolves on this machine; the Qwen template has no such key.
    rewrite_statusline: bool = False


TEMPLATE_SETTINGS: tuple[SettingsSpec, ...] = (
    SettingsSpec(SETTINGS_TEMPLATE_REL, SETTINGS_DEST_REL, rewrite_statusline=True),
)

# Qwen Code component: everything agent-config manages under `~/.qwen`. It is
# opt-in, so these specs are kept out of the manifests above and only joined
# into a layout when `--qwen` is given. Keeping the whole component — files,
# trees, settings and the managed directory itself — in one place is what makes
# "a plain command never touches ~/.qwen" a structural property rather than a
# set of per-operation conditionals.
QWEN_TEMPLATE_FILES: tuple[FileSpec, ...] = (
    FileSpec(GUIDELINE_TEMPLATE_REL, ".qwen/QWEN.md", 0o600),
)

QWEN_TEMPLATE_TREES: tuple[TreeSpec, ...] = (
    TreeSpec("templates/skills", ".qwen/skills"),
)

QWEN_TEMPLATE_SETTINGS: tuple[SettingsSpec, ...] = (
    SettingsSpec(QWEN_SETTINGS_TEMPLATE_REL, QWEN_SETTINGS_DEST_REL),
)

# settings.json keys whose `command` launches a deployed status-line script,
# mapped to that script's path relative to home. The installer rewrites these
# per-platform so the command is actually runnable on the target OS.
STATUSLINE_COMMANDS: tuple[tuple[str, str], ...] = (
    ("statusLine", ".claude/statusline.py"),
    ("subagentStatusLine", ".claude/subagent-statusline.py"),
)

# Top-level home subdirectories that the installer may write into.
INSTALL_HOME_DIRS: tuple[str, ...] = (".claude", ".codex", ".agents")

# Home subdirectory of the opt-in Qwen Code component. Excluding it from
# managed_dirs — not just its specs from the manifests — keeps `~/.qwen`
# outside the filesystem-mutation boundary, so a plain install cannot even
# create it empty.
QWEN_HOME_DIRS: tuple[str, ...] = (".qwen",)

# Top-level skill directory names that are no longer maintained. prune_tree keeps
# entries with no source counterpart because they may be user-added, so obsolete
# managed names would otherwise linger after install. The installer deletes each
# explicit managed name and its same-name backup from every skills tree during the
# migration window.
DECOMMISSIONED_SKILLS: tuple[str, ...] = (
    "code-review",
    "commit",
    "doc-review",
    "github-workflow",
    "html-document",
    "intent-review",
    "kaizen",
    "open-file",
    "open-html",
    "plan",
    "quality-review",
    "review",
    "review-loop",
    "skill-improve",
    "third-party-oss-security-review",
)

# Managed file destinations that are no longer maintained. A removed spec
# leaves its deployed file in place otherwise, so the installer retires each
# explicit managed path to its single-generation .bak: the retired config
# stops being loadable while remaining recoverable.
DECOMMISSIONED_FILES: tuple[str, ...] = (
    ".codex/full.config.toml",
)


# --------------------------------------------------------------------------- #
# Layout: one install destination — the root, the dirs owned there, and the
# subset of the manifest that belongs in it.
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Layout:
    root: Path                          # dest_rel values resolve against this
    home: Path                          # base for `~`-relative status-line commands
    managed_dirs: tuple[Path, ...]      # dirs the installer owns; every write stays inside one
    files: tuple[FileSpec, ...]
    trees: tuple[TreeSpec, ...]
    settings: tuple[SettingsSpec, ...]
    statusline_commands: tuple[tuple[str, str], ...]
    description: str                    # subject of the "Install …" / "Clean …" banner


# Prefix of the home-relative destinations that make up a Claude Code
# configuration directory. It is what CLAUDE_CONFIG_DIR replaces, so it is also
# exactly the slice a --claude-dir install re-roots elsewhere.
CLAUDE_HOME_DIR = ".claude"

HOME_DESCRIPTION = "Claude + Codex configuration"
HOME_QWEN_DESCRIPTION = "Claude + Codex + Qwen Code configuration"


def home_layout(home: Path, *, include_qwen: bool = False) -> Layout:
    """Default destination: `~/.claude`, `~/.codex`, `~/.agents` (+ `~/.qwen`).

    `include_qwen` joins the opt-in Qwen Code component into the layout. The
    selection happens here, once, so install / clean / verify all act on the
    same set of destinations and cannot drift apart.
    """
    return Layout(
        root=home,
        home=home,
        managed_dirs=tuple(
            home / sub
            for sub in (INSTALL_HOME_DIRS + (QWEN_HOME_DIRS if include_qwen else ()))
        ),
        files=TEMPLATE_FILES + (QWEN_TEMPLATE_FILES if include_qwen else ()),
        trees=TEMPLATE_TREES + (QWEN_TEMPLATE_TREES if include_qwen else ()),
        settings=TEMPLATE_SETTINGS + (QWEN_TEMPLATE_SETTINGS if include_qwen else ()),
        statusline_commands=STATUSLINE_COMMANDS,
        description=HOME_QWEN_DESCRIPTION if include_qwen else HOME_DESCRIPTION,
    )


def claude_config_rel(dest_rel: str) -> str | None:
    """Destination under a Claude configuration directory, or None.

    None means the entry is not part of one: Codex and the shared `~/.agents`
    skills are addressed by their own tools and are unaffected by
    CLAUDE_CONFIG_DIR.
    """
    prefix = f"{CLAUDE_HOME_DIR}/"
    return dest_rel[len(prefix):] if dest_rel.startswith(prefix) else None


def claude_dir_layout(target: Path, home: Path) -> Layout:
    """Destination for `--claude-dir`: the `~/.claude` slice, re-rooted on `target`.

    Derived from the home manifest rather than listed separately, so a
    CLAUDE_CONFIG_DIR profile always receives exactly what `~/.claude` receives.
    """
    files = tuple(
        replace(spec, dest_rel=rel)
        for spec in TEMPLATE_FILES
        if (rel := claude_config_rel(spec.dest_rel)) is not None
    )
    trees = tuple(
        replace(spec, dest_rel=rel)
        for spec in TEMPLATE_TREES
        if (rel := claude_config_rel(spec.dest_rel)) is not None
    )
    settings = tuple(
        replace(spec, dest_rel=rel)
        for spec in TEMPLATE_SETTINGS
        if (rel := claude_config_rel(spec.dest_rel)) is not None
    )
    statusline = tuple(
        (key, rel)
        for key, script_rel in STATUSLINE_COMMANDS
        if (rel := claude_config_rel(script_rel)) is not None
    )
    return Layout(
        root=target,
        home=home,
        managed_dirs=(target,),
        files=files,
        trees=trees,
        settings=settings,
        statusline_commands=statusline,
        description=f"Claude configuration in {target}",
    )


def clean_targets(layout: Layout) -> list[Path]:
    """Paths that clean() removes (with .bak backup).

    settings.json is intentionally excluded because it is a shallow merge of
    template and user-managed keys, not a pure template copy.
    """
    out: list[Path] = []
    for spec in layout.files:
        out.append(layout.root / spec.dest_rel)
    for tspec in layout.trees:
        out.append(layout.root / tspec.dest_rel)
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


def ensure_file_mode(path: Path, mode: int) -> bool:
    """Re-apply a managed file's mode without rewriting its content.

    install skips writing a destination whose content already matches, and the
    mode is only set as part of a write. The mode is nevertheless part of what
    verify checks, so a tool that rewrites its own config with a wider mode
    would otherwise leave drift that no number of re-runs can repair. Applying
    it here keeps install convergent.

    Reports the change when there is one, and returns whether it acted. The
    status line of a file whose content already matches stays `ok:`; changing
    permission bits is the one thing this does beyond nothing, so the rare run
    that does it says so on its own line instead of hiding inside that `ok:`.

    The mode is applied through a file descriptor opened with O_NOFOLLOW, so
    the check and the change cannot be separated by a symlink swapped in
    between them. A symlinked path is rejected by the same flag: chmod follows
    links and would change the mode of a file the installer does not manage.
    """
    if not POSIX:
        return False  # NTFS does not honour POSIX modes
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    except OSError:
        return False  # missing, a symlink (ELOOP), or unreadable
    try:
        current = os.fstat(fd).st_mode & 0o777
        if current == mode:
            return False
        os.fchmod(fd, mode)
    finally:
        os.close(fd)
    print(f"mode: {path} ({oct(current)} -> {oct(mode)})")
    return True


def install_file(src: Path, dest: Path, mode: int = FILE_MODE) -> str:
    """Install a single file with backup. Return one of: ok | copied | replaced.

    - "ok": dest already matches src; only the mode is re-applied.
    - "copied": dest did not exist; created from src.
    - "replaced": dest existed and was backed up to dest.bak.
    """
    if not src.is_file() or src.is_symlink():
        raise FileNotFoundError(f"source not found or not a regular file: {src}")

    if dest.exists() and not dest.is_symlink() and same_content(src, dest):
        ensure_file_mode(dest, mode)
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


def remove_decommissioned_skills(layout: Layout) -> list[Path]:
    """Delete deployed skill names that must no longer be discoverable.

    prune_tree preserves top-level entries with no source counterpart (possibly
    user-added), so obsolete managed names and their backups are deleted by
    explicit name here.
    """
    removed: list[Path] = []
    skill_roots = [
        layout.root / t.dest_rel
        for t in layout.trees
        if t.src_rel == "templates/skills"
    ]
    for root in skill_roots:
        for name in DECOMMISSIONED_SKILLS:
            for target in (root / name, root / f"{name}.bak"):
                if not (target.exists() or target.is_symlink()):
                    continue
                if target.is_symlink():
                    target.unlink()
                else:
                    assert_within(target, root)
                if target.exists() and target.is_dir():
                    shutil.rmtree(target)
                elif target.exists():
                    target.unlink()
                removed.append(target)
        archive_root = root.parent / "retired-skills"
        if archive_root.exists() or archive_root.is_symlink():
            if archive_root.is_symlink():
                archive_root.unlink()
            else:
                assert_within(archive_root, root.parent)
            if archive_root.exists() and archive_root.is_dir():
                shutil.rmtree(archive_root)
            elif archive_root.exists():
                archive_root.unlink()
            removed.append(archive_root)
    return removed


def remove_decommissioned_files(layout: Layout) -> list[Path]:
    """Retire deployed file destinations the manifest no longer maintains.

    Each retired path is moved to its single-generation .bak (recoverable),
    mirroring how clean() removes managed files. Absent paths are skipped.

    Retirements are global constants rather than per-component specs, so they
    are filtered by the layout's managed dirs like every other write: retiring
    something under a component this layout does not select must not reach into
    that component's directory.
    """
    removed: list[Path] = []
    for rel in DECOMMISSIONED_FILES:
        target = layout.root / rel
        if not any(is_within(target, managed) for managed in layout.managed_dirs):
            continue
        if remove_with_backup(target) == "backed_up":
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
def statusline_command(script: Path, *, posix: bool, python: str, home: Path) -> str:
    """Build a runnable status-line `command` string for the target platform.

    POSIX: a `~`-relative path when the script lives under `home`, else its
    absolute path. The shebang + executable bit launch the script
    OS-independently and re-resolve the interpreter via PATH on every run, which
    survives the interpreter moving as long as it stays on PATH.

    Windows: `cmd.exe` neither expands `~` nor executes a bare `.py`, so the
    interpreter must be invoked explicitly with the absolute script path. Both
    tokens are quoted to tolerate spaces (e.g. `C:/Program Files/...`).
    """
    if not posix:
        return f'"{python}" "{script.as_posix()}"'
    try:
        return f"~/{script.relative_to(home).as_posix()}"
    except ValueError:
        return script.as_posix()


def apply_statusline_commands(
    template: dict[str, object], layout: Layout, *, posix: bool, python: str
) -> dict[str, object]:
    """Return a copy of `template` with status-line commands rewritten for the OS.

    Only sections that already declare a `command` are touched, so the template
    stays the single source of truth for which status lines exist. For a home
    install on POSIX the rewritten value equals the template's `~/...` literal,
    making this a no-op there (and keeping re-runs idempotent).
    """
    out = dict(template)
    for key, script_rel in layout.statusline_commands:
        section = out.get(key)
        if isinstance(section, dict) and "command" in section:
            updated = dict(section)
            updated["command"] = statusline_command(
                layout.root / script_rel, posix=posix, python=python, home=layout.home
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
    materialize: bool = False,
) -> str:
    """Apply a shallow merge from template_path into dest.

    `transform`, when given, is applied to the parsed template object before the
    merge. The installer uses it to rewrite status-line commands per-platform;
    the standalone `merge` subcommand passes none (generic merge).

    `materialize` makes a symlinked destination take the write path even when
    the merged content already matches. A managed destination is a regular
    file — install_file replaces a symlinked one outright, and verify checks
    the mode through the link, which the installer refuses to change — so a
    symlink left in place is a destination that install and verify disagree
    about and never converge on. The merge still reads through the link first,
    so user-managed keys survive the change. The standalone `merge` subcommand
    leaves the caller's own symlink alone.

    Returns one of: ok | created | merged | materialized.
    """
    template_data = json.loads(template_path.read_text(encoding="utf-8"))
    if not isinstance(template_data, dict):
        raise ValueError(f"template must be a JSON object: {template_path}")
    if transform is not None:
        template_data = transform(template_data)

    existing_text, existing = read_existing(dest)
    new_text = render(merge(template_data, existing))

    unchanged = existing_text == new_text
    if unchanged and not (materialize and dest.is_symlink()):
        return "ok"

    # Only content that differs from what is about to be written is worth
    # recovering. Backing up an identical copy would spend the single .bak
    # generation on nothing and discard a genuinely older state.
    if existing_text is not None and not unchanged:
        bak = dest.with_name(dest.name + ".bak")
        atomic_write_text(bak, existing_text, mode=FILE_MODE)

    atomic_write_text(dest, new_text, mode=FILE_MODE)
    if unchanged:
        return "materialized"
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


def verify(layout: Layout, repo_root: Path = REPO_ROOT) -> VerifyReport:
    report = VerifyReport()
    print(f"Verify {layout.description}")

    for spec in layout.files:
        src = repo_root / spec.src_rel
        dest = layout.root / spec.dest_rel
        _check_file(report, src, dest)
        _check_mode(report, dest, spec.mode)

    for managed in layout.managed_dirs:
        _check_mode(report, managed, DIR_MODE)

    for tspec in layout.trees:
        src_root = repo_root / tspec.src_rel
        dest_root = layout.root / tspec.dest_rel
        _check_tree(report, src_root, dest_root, tspec.dir_mode, tspec.file_mode)

    for sspec in layout.settings:
        dest = layout.root / sspec.dest_rel
        report.record(dest.exists(), f"missing: {dest}")
        _check_mode(report, dest, FILE_MODE)
        _check_settings_contract(report, repo_root / sspec.src_rel, dest)

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


def _statusline_transform(
    layout: Layout, *, python: str
) -> Callable[[dict[str, object]], dict[str, object]]:
    def transform(template: dict[str, object]) -> dict[str, object]:
        return apply_statusline_commands(template, layout, posix=POSIX, python=python)

    return transform


def install(layout: Layout, repo_root: Path = REPO_ROOT) -> int:
    """Install the layout's templates into its root. Returns process exit code."""
    # Pre-create the dirs we own, with restrictive perms. They are also the
    # boundary: every destination below must resolve inside one of them.
    boundary_dirs = layout.managed_dirs
    for managed in boundary_dirs:
        ensure_secure_dir(managed, DIR_MODE)

    print(f"Install {layout.description}")

    for spec in layout.files:
        src = repo_root / spec.src_rel
        dest = layout.root / spec.dest_rel
        # Guard: destination must live inside one of the install dirs.
        if not any(is_within(dest, b) for b in boundary_dirs):
            raise PermissionError(f"refusing to write outside install dirs: {dest}")
        status = install_file(src, dest, mode=spec.mode)
        print(f"{status}: {dest}")

    for tspec in layout.trees:
        src_root = repo_root / tspec.src_rel
        dest_root = layout.root / tspec.dest_rel
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

    for dest in remove_decommissioned_skills(layout):
        print(f"removed (obsolete skill data): {dest}")

    for dest in remove_decommissioned_files(layout):
        print(f"backup: {dest}.bak")
        print(f"removed (obsolete config): {dest}")

    # `sys.executable` is the interpreter running this installer: guaranteed to
    # exist and be >= 3.9, and on Windows it is exactly the python that must be
    # named explicitly in the status-line command.
    python = Path(sys.executable).as_posix()
    for sspec in layout.settings:
        dest = layout.root / sspec.dest_rel
        if not any(is_within(dest, b) for b in boundary_dirs):
            raise PermissionError(f"refusing to write outside install dirs: {dest}")
        transform = (
            _statusline_transform(layout, python=python)
            if sspec.rewrite_statusline
            else None
        )
        # Read before the merge: materializing replaces the link, and naming
        # what it pointed at is what lets the user restore the arrangement.
        link_target = os.readlink(dest) if dest.is_symlink() else None
        status = merge_into(
            repo_root / sspec.src_rel, dest, transform=transform, materialize=True
        )
        # merge_into writes only when the merged content differs, so the mode
        # gets the same explicit re-apply that install_file does.
        ensure_file_mode(dest, FILE_MODE)
        if status == "ok":
            print(f"ok: {dest}")
        elif status == "created":
            print(f"created: {dest}")
        elif status == "materialized":
            # Replacing a symlink is a bigger change than the content merge it
            # would otherwise be reported as, so it gets named on its own.
            print(f"materialized: {dest} (was a symlink to {link_target})")
        else:
            print(f"backup: {dest}.bak")
            print(f"merged: {dest}")

    # Re-apply directory perms (in case rsync-style operations widened them).
    for managed in boundary_dirs:
        chmod_if_posix(managed, DIR_MODE)

    return 0


def clean(layout: Layout) -> int:
    print(f"Clean {layout.description}")
    for target in clean_targets(layout):
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
USAGE = (
    "usage: cli.py <install|clean|verify> [--claude-dir <dir>] [--qwen]\n"
    "       cli.py merge <template> <destination>\n"
    "\n"
    "--qwen is additive (usual destinations + the Qwen Code component) and\n"
    "cannot be combined with --claude-dir."
)

CLAUDE_DIR_FLAG = "--claude-dir"
QWEN_FLAG = "--qwen"

# Commands that act on a destination layout rather than on explicit paths.
LAYOUT_COMMANDS = ("install", "clean", "verify")


@dataclass(frozen=True)
class LayoutArgs:
    claude_dir: str | None      # raw --claude-dir value, unresolved
    include_qwen: bool


def _directory_value(raw: str) -> str:
    """Reject a directory argument that is really a mistyped option.

    `--claude-dir --qwen` would otherwise consume the next option as the
    directory name and install into a literal `./--qwen`, silently bypassing
    the flag-conflict check below. A directory whose name really starts with
    `-` can still be named as `./-name`.
    """
    if raw.startswith("-"):
        raise ValueError(
            f"{CLAUDE_DIR_FLAG} value looks like an option: {raw} "
            f"(pass ./{raw} if that is really the directory name)"
        )
    return raw


def parse_layout_args(args: list[str]) -> LayoutArgs:
    """Parse the options a layout command accepts.

    Accepts `--claude-dir DIR`, `--claude-dir=DIR` and `--qwen`. Anything else
    raises, so a mistyped flag cannot be silently ignored and write to `$HOME`
    instead. `--claude-dir` re-roots one Claude configuration slice while
    `--qwen` targets `$HOME/.qwen`: combining them would make a single command
    mutate two unrelated roots, so the combination is rejected here — before
    any filesystem work starts — rather than given a new meaning.
    """
    rest = list(args)
    claude_dir: str | None = None
    include_qwen = False
    while rest:
        arg = rest.pop(0)
        if arg == CLAUDE_DIR_FLAG:
            if not rest:
                raise ValueError(f"{CLAUDE_DIR_FLAG} requires a directory argument")
            claude_dir = _directory_value(rest.pop(0))
        elif arg.startswith(f"{CLAUDE_DIR_FLAG}="):
            claude_dir = _directory_value(arg.split("=", 1)[1])
        elif arg == QWEN_FLAG:
            include_qwen = True
        else:
            raise ValueError(f"unexpected argument: {arg}")
    if claude_dir is not None and include_qwen:
        raise ValueError(
            f"{CLAUDE_DIR_FLAG} and {QWEN_FLAG} cannot be combined: "
            f"{CLAUDE_DIR_FLAG} re-roots the Claude configuration slice, while "
            f"{QWEN_FLAG} targets $HOME/.qwen"
        )
    return LayoutArgs(claude_dir=claude_dir, include_qwen=include_qwen)


def resolve_claude_dir(raw: str, home: Path) -> Path:
    """Resolve a `--claude-dir` value to the absolute directory to install into.

    `~` is expanded here as well as by the shell, so `--claude-dir=~/x` works.
    Rejected targets: an empty value; `$HOME` and filesystem roots, where the
    template would scatter across a directory the installer does not own; and
    an existing non-directory, so a typo cannot clobber a file.
    """
    if not raw.strip():
        raise ValueError(f"{CLAUDE_DIR_FLAG} requires a non-empty path")
    target = Path(raw).expanduser().resolve(strict=False)
    if target == home.expanduser().resolve(strict=False):
        raise ValueError(
            f"{CLAUDE_DIR_FLAG} must name a configuration directory, not the home "
            f"directory itself: {target}"
        )
    if target.parent == target:
        raise ValueError(f"{CLAUDE_DIR_FLAG} must not be a filesystem root: {target}")
    if target.exists() and not target.is_dir():
        raise ValueError(f"{CLAUDE_DIR_FLAG} is not a directory: {target}")
    return target


def layout_for(args: list[str], home: Path) -> Layout:
    """Destination layout for a layout command's arguments.

    CLAUDE_CONFIG_DIR is deliberately not consulted: a plain `install` run from
    a shell that exports it must still target `~/.claude`, so redirecting the
    install stays an explicit act.
    """
    parsed = parse_layout_args(args)
    if parsed.claude_dir is None:
        return home_layout(home, include_qwen=parsed.include_qwen)
    return claude_dir_layout(resolve_claude_dir(parsed.claude_dir, home), home)


def _verify_cli(layout: Layout) -> int:
    report = verify(layout)
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
    if command in LAYOUT_COMMANDS:
        try:
            layout = layout_for(rest, Path.home())
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            print(USAGE, file=sys.stderr)
            return 2
        if command == "install":
            refuse_root()
            return install(layout)
        if command == "clean":
            return clean(layout)
        return _verify_cli(layout)
    if command == "merge":
        return _merge_cli(prog, rest)
    print(f"unknown command: {command}", file=sys.stderr)
    print(USAGE, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
