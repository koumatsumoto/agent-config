"""Repo-relative source paths and home-relative install destinations."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


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


# Files that are full-template overwrites (with .bak backup).
TEMPLATE_FILES: tuple[FileSpec, ...] = (
    FileSpec("templates/CLAUDE.md", ".claude/CLAUDE.md", 0o600),
    FileSpec("templates/keybindings.json", ".claude/keybindings.json", 0o600),
    FileSpec("templates/statusline.sh", ".claude/statusline.sh", 0o700, is_executable=True),
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


# Top-level home subdirectories that the installer may write into.
INSTALL_HOME_DIRS: tuple[str, ...] = (".claude", ".codex", ".agents")


def all_install_targets(home: Path) -> list[Path]:
    """Every absolute dest path the installer would touch (files + tree roots)."""
    out: list[Path] = []
    for spec in TEMPLATE_FILES:
        out.append(home / spec.dest_rel)
    for spec in TEMPLATE_TREES:
        out.append(home / spec.dest_rel)
    out.append(home / SETTINGS_DEST_REL)
    return out


def clean_targets(home: Path) -> list[Path]:
    """Paths that clean.py removes (with .bak backup).

    settings.json is intentionally excluded because it carries user-managed
    values merged in, not a pure template copy.
    """
    out: list[Path] = []
    for spec in TEMPLATE_FILES:
        out.append(home / spec.dest_rel)
    for spec in TEMPLATE_TREES:
        out.append(home / spec.dest_rel)
    return out
