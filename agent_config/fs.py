"""Cross-platform file operations with security defaults.

All writes are atomic (mkstemp + os.replace). Permission modes are applied
explicitly via fchmod where the platform supports it; on Windows the modes
are silently ignored because NTFS does not honour POSIX mode bits — file
isolation there relies on the inherited user-profile ACL.
"""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

POSIX = os.name == "posix"
DIR_MODE = 0o700
FILE_MODE = 0o600
EXEC_MODE = 0o700


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
        raise PermissionError(
            f"refusing to operate outside {parent}: {child}"
        )


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
