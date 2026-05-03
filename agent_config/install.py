"""Install Claude Code + Codex CLI templates into the user's home dir.

Replaces the legacy install.sh. Cross-platform (POSIX + Windows). On POSIX
applies 0o700/0o600/0o700 modes for directories / regular files / executables.
On Windows the modes are skipped because NTFS does not honour POSIX bits;
isolation there relies on the inherited user-profile ACL.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from agent_config import fs, merge_settings, paths


def refuse_root() -> None:
    """Refuse to run as root on POSIX. (No EUID concept on Windows.)"""
    if fs.is_posix() and hasattr(os, "geteuid") and os.geteuid() == 0:
        print(
            "ERROR: Do not run this installer as root or with sudo. Run as your user.",
            file=sys.stderr,
        )
        sys.exit(1)


def install(home: Path, repo_root: Path = paths.REPO_ROOT) -> int:
    """Install all templates into `home`. Returns process exit code."""
    # Pre-create home subdirs that we own, with restrictive perms.
    boundary_dirs: list[Path] = []
    for sub in paths.INSTALL_HOME_DIRS:
        d = home / sub
        fs.ensure_secure_dir(d, fs.DIR_MODE)
        boundary_dirs.append(d)

    print("Install Claude + Codex configuration")

    for spec in paths.TEMPLATE_FILES:
        src = repo_root / spec.src_rel
        dest = home / spec.dest_rel
        # Guard: destination must live inside one of the install dirs.
        if not any(fs.is_within(dest, b) for b in boundary_dirs):
            raise PermissionError(f"refusing to write outside install dirs: {dest}")
        status = fs.install_file(src, dest, mode=spec.mode)
        print(f"{status}: {dest}")

    for tspec in paths.TEMPLATE_TREES:
        src_root = repo_root / tspec.src_rel
        dest_root = home / tspec.dest_rel
        # Tree boundary is whichever managed dir contains dest_root.
        boundary = next(
            (b for b in boundary_dirs if fs.is_within(dest_root, b)), None
        )
        if boundary is None:
            raise PermissionError(
                f"refusing to write tree outside install dirs: {dest_root}"
            )
        results = fs.install_tree(
            src_root,
            dest_root,
            dir_mode=tspec.dir_mode,
            file_mode=tspec.file_mode,
            boundary=boundary,
        )
        for status, dest in results:
            print(f"{status}: {dest}")

    settings_status = merge_settings.merge_into(
        repo_root / paths.SETTINGS_TEMPLATE_REL,
        home / paths.SETTINGS_DEST_REL,
    )
    if settings_status == "ok":
        print(f"ok: {home / paths.SETTINGS_DEST_REL}")
    elif settings_status == "created":
        print(f"created: {home / paths.SETTINGS_DEST_REL}")
    else:
        print(f"backup: {home / paths.SETTINGS_DEST_REL}.bak")
        print(f"merged: {home / paths.SETTINGS_DEST_REL}")

    # Re-apply directory perms (in case rsync-style operations widened them).
    for sub in paths.INSTALL_HOME_DIRS:
        fs.chmod_if_posix(home / sub, fs.DIR_MODE)

    return 0


def main(argv: list[str]) -> int:
    refuse_root()
    home = Path.home()
    return install(home)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
