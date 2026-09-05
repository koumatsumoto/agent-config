#!/usr/bin/env python3
"""Copy selected ignored files into a newly-created Git worktree."""

from __future__ import annotations

import argparse
import os
import shutil
import stat
import subprocess
import sys
from contextlib import ExitStack
from pathlib import Path


class PreparationError(RuntimeError):
    pass


def _git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    try:
        return subprocess.run(
            ["git", "-C", os.fspath(root), *args],
            check=check,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except FileNotFoundError as exc:
        raise PreparationError("git commandが見つかりません") from exc
    except subprocess.CalledProcessError as exc:
        message = exc.stderr.decode("utf-8", errors="replace").strip()
        raise PreparationError(message or f"git {' '.join(args)} に失敗しました") from exc


def _worktree_root(path: Path) -> Path:
    resolved = path.resolve(strict=True)
    if not resolved.is_dir():
        raise PreparationError(f"Git worktree rootではありません: {path}")
    reported = Path(
        _git(resolved, "rev-parse", "--show-toplevel").stdout.decode().strip()
    ).resolve(strict=True)
    if reported != resolved:
        raise PreparationError(f"Git worktree rootを指定してください: {path}")
    return resolved


def _common_dir(root: Path) -> Path:
    value = _git(
        root, "rev-parse", "--path-format=absolute", "--git-common-dir"
    ).stdout.decode().strip()
    return Path(value).resolve(strict=True)


def _within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _exists_without_following(path: Path) -> bool:
    try:
        path.lstat()
    except FileNotFoundError:
        return False
    return True


def _git_predicate(root: Path, *args: str) -> bool:
    result = _git(root, *args, check=False)
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    message = result.stderr.decode("utf-8", errors="replace").strip()
    raise PreparationError(message or f"git {' '.join(args)} に失敗しました")


def _is_tracked(root: Path, relative: str) -> bool:
    return _git_predicate(root, "ls-files", "--error-unmatch", "--", relative)


def _is_ignored(root: Path, relative: str) -> bool:
    return _git_predicate(root, "check-ignore", "-q", "--", relative)


def _matching_untracked(source: Path, patterns: Path) -> list[str]:
    result = _git(
        source,
        "ls-files",
        "--others",
        "--ignored",
        "-z",
        f"--exclude-from={patterns}",
    )
    return [item.decode("utf-8", errors="surrogateescape") for item in result.stdout.split(b"\0") if item]


def _ensure_private_parents(destination: Path, parent: Path) -> None:
    try:
        relative = parent.relative_to(destination)
    except ValueError as exc:
        raise PreparationError("destination worktree外への書き込みを拒否しました") from exc

    current = destination
    for part in relative.parts:
        current /= part
        if _exists_without_following(current):
            if not current.is_dir() or not _within(current.resolve(strict=True), destination):
                raise PreparationError("destination worktree外への書き込みを拒否しました")
            continue
        current.mkdir(mode=0o700)
        if not _within(current.resolve(strict=True), destination):
            raise PreparationError("destination worktree外への書き込みを拒否しました")


def _remove_created_partial(destination: Path, identity: tuple[int, int]) -> None:
    try:
        current = destination.lstat()
    except FileNotFoundError:
        return
    if not stat.S_ISREG(current.st_mode) or (current.st_dev, current.st_ino) != identity:
        raise PreparationError("作成したpartial destinationを安全に削除できません")
    destination.unlink()


def _copy_regular_file(source: Path, destination: Path) -> None:
    created_identity: tuple[int, int] | None = None
    try:
        with ExitStack() as stack:
            source_flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
            source_fd = os.open(source, source_flags)
            source_file = stack.enter_context(os.fdopen(source_fd, "rb"))
            source_stat = os.fstat(source_file.fileno())
            if not stat.S_ISREG(source_stat.st_mode):
                raise PreparationError("sourceの通常file以外はcopyできません")

            destination_flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
            destination_fd = os.open(
                destination,
                destination_flags,
                stat.S_IMODE(source_stat.st_mode),
            )
            destination_stat = os.fstat(destination_fd)
            created_identity = (destination_stat.st_dev, destination_stat.st_ino)
            destination_file = stack.enter_context(os.fdopen(destination_fd, "wb"))
            shutil.copyfileobj(source_file, destination_file)
    except OSError as exc:
        if created_identity is not None:
            try:
                _remove_created_partial(destination, created_identity)
            except (OSError, PreparationError) as cleanup_exc:
                raise PreparationError(
                    "ignored fileのcopyに失敗し、partial destinationも削除できません"
                ) from cleanup_exc
        raise PreparationError("ignored fileのcopyに失敗しました") from exc


def prepare(source_arg: Path, destination_arg: Path) -> tuple[int, int]:
    source = _worktree_root(source_arg)
    destination = _worktree_root(destination_arg)
    if source == destination:
        raise PreparationError("sourceとdestinationには別のworktreeを指定してください")
    if _common_dir(source) != _common_dir(destination):
        raise PreparationError("sourceとdestinationは同じGit repositoryに属していません")

    include = destination / ".worktreeinclude"
    if not _is_tracked(destination, ".worktreeinclude"):
        return 0, 0
    try:
        include_stat = include.lstat()
    except FileNotFoundError as exc:
        raise PreparationError("tracked .worktreeincludeが見つかりません") from exc
    if not stat.S_ISREG(include_stat.st_mode) or not _within(
        include.resolve(strict=True), destination
    ):
        raise PreparationError(".worktreeincludeはworktree内の通常fileである必要があります")

    planned: list[tuple[Path, Path]] = []
    skipped = 0
    for relative in _matching_untracked(source, include):
        if Path(relative).is_absolute() or ".." in Path(relative).parts:
            raise PreparationError("repository外を指す候補を拒否しました")
        if (
            _is_tracked(source, relative)
            or not _is_ignored(source, relative)
        ):
            continue

        source_path = source / relative
        try:
            source_stat = source_path.lstat()
        except FileNotFoundError:
            continue
        if not stat.S_ISREG(source_stat.st_mode):
            continue
        if not _within(source_path.resolve(strict=True), source):
            raise PreparationError("source worktree外へ解決される候補を拒否しました")

        destination_path = destination / relative
        if _exists_without_following(destination_path):
            skipped += 1
            continue
        if not _within(destination_path.parent.resolve(strict=False), destination):
            raise PreparationError("destination worktree外へ解決される候補を拒否しました")
        if not _is_ignored(destination, relative):
            continue
        planned.append((source_path, destination_path))

    copied = 0
    for source_path, destination_path in planned:
        _ensure_private_parents(destination, destination_path.parent)
        if not _within(destination_path.parent.resolve(strict=True), destination):
            raise PreparationError("destination worktree外への書き込みを拒否しました")
        _copy_regular_file(source_path, destination_path)
        copied += 1
    return copied, skipped


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Copy .worktreeinclude-selected ignored files between Git worktrees."
    )
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args(argv)
    try:
        copied, skipped = prepare(args.source, args.destination)
    except (OSError, PreparationError) as exc:
        print(f"prepare-worktree: {exc}", file=sys.stderr)
        return 1
    print(f"prepare-worktree: copied={copied} skipped={skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
