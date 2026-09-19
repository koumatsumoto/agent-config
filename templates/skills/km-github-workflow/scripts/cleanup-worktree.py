#!/usr/bin/env python3
"""Remove one clean, expected Git worktree without deleting its branch."""

from __future__ import annotations

import argparse
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path


class CleanupError(RuntimeError):
    pass


def _git(
    root: Path,
    *args: str,
    check: bool = True,
    env: dict[str, str] | None = None,
    input_data: bytes | None = None,
) -> subprocess.CompletedProcess[bytes]:
    try:
        return subprocess.run(
            ["git", "-C", os.fspath(root), *args],
            check=check,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            input=input_data,
        )
    except FileNotFoundError as exc:
        raise CleanupError("git commandが見つかりません") from exc
    except subprocess.CalledProcessError as exc:
        message = exc.stderr.decode("utf-8", errors="replace").strip()
        raise CleanupError(message or f"git {' '.join(args)} に失敗しました") from exc


def _worktree_root(path: Path, role: str) -> Path:
    if path.is_symlink():
        raise CleanupError(f"{role}のsymlinkは使用できません")
    try:
        resolved = path.resolve(strict=True)
    except FileNotFoundError as exc:
        raise CleanupError(f"{role}が見つかりません: {path}") from exc
    if not resolved.is_dir():
        raise CleanupError(f"{role}はGit worktree rootではありません: {path}")
    reported = Path(
        _git(resolved, "rev-parse", "--show-toplevel").stdout.decode().strip()
    ).resolve(strict=True)
    if reported != resolved:
        raise CleanupError(f"{role}にはGit worktree rootを指定してください: {path}")
    return resolved


def _common_dir(root: Path) -> Path:
    value = _git(
        root, "rev-parse", "--path-format=absolute", "--git-common-dir"
    ).stdout.decode().strip()
    return Path(value).resolve(strict=True)


def _checked_branch(source: Path, branch: str) -> str:
    checked = _git(source, "check-ref-format", "--branch", branch).stdout.decode().strip()
    if checked != branch:
        raise CleanupError("branchには省略記法ではなく名前を指定してください")
    return f"refs/heads/{branch}"


def _git_predicate(root: Path, *args: str) -> bool:
    result = _git(root, *args, check=False)
    if result.returncode == 0:
        return True
    if result.returncode == 1:
        return False
    message = result.stderr.decode("utf-8", errors="replace").strip()
    raise CleanupError(message or f"git {' '.join(args)} に失敗しました")


def _exists_without_following(path: Path) -> bool:
    try:
        path.lstat()
    except FileNotFoundError:
        return False
    return True


def _sparse_checkout_excluded(root: Path, relatives: list[str]) -> set[str]:
    if not relatives:
        return set()
    enabled = _git(root, "config", "--bool", "core.sparseCheckout", check=False)
    if enabled.returncode == 1:
        return set()
    if enabled.returncode != 0:
        message = enabled.stderr.decode("utf-8", errors="replace").strip()
        raise CleanupError(message or "sparse-checkout設定の確認に失敗しました")
    if enabled.stdout.strip() != b"true":
        return set()

    encoded = {
        relative.encode("utf-8", errors="surrogateescape"): relative
        for relative in relatives
    }
    input_data = b"\0".join(encoded) + b"\0"
    result = _git(
        root,
        "sparse-checkout",
        "check-rules",
        "-z",
        check=False,
        input_data=input_data,
    )
    if result.returncode != 0:
        message = result.stderr.decode("utf-8", errors="replace").strip()
        raise CleanupError(message or "sparse-checkout ruleの確認に失敗しました")
    included_bytes = {item for item in result.stdout.split(b"\0") if item}
    if not included_bytes.issubset(encoded):
        raise CleanupError("sparse-checkout ruleの確認結果を解釈できません")
    included = {encoded[item] for item in included_bytes}
    return set(relatives) - included


def _hidden_tracked_changes(root: Path) -> bool:
    entries = _git(root, "ls-files", "-v", "-z").stdout.split(b"\0")
    checks: list[tuple[str, bool, bool]] = []
    missing_skip_worktree: list[tuple[str, bool, bool]] = []
    for entry in entries:
        if not entry:
            continue
        if len(entry) < 3 or entry[1:2] != b" ":
            raise CleanupError("tracked fileのindex状態を確認できません")
        tag = entry[0]
        skip_worktree = tag in (ord("S"), ord("s"))
        assume_unchanged = ord("a") <= tag <= ord("z")
        if not skip_worktree and not assume_unchanged:
            continue
        relative = entry[2:].decode("utf-8", errors="surrogateescape")
        if skip_worktree and not _exists_without_following(root / relative):
            missing_skip_worktree.append(
                (relative, skip_worktree, assume_unchanged)
            )
            continue
        checks.append((relative, skip_worktree, assume_unchanged))

    excluded = _sparse_checkout_excluded(
        root, [relative for relative, _, _ in missing_skip_worktree]
    )
    checks.extend(
        entry for entry in missing_skip_worktree if entry[0] not in excluded
    )

    if not checks:
        return False

    index_value = _git(
        root, "rev-parse", "--path-format=absolute", "--git-path", "index"
    ).stdout.decode().strip()
    index = Path(index_value).resolve(strict=True)
    temporary_fd, temporary_name = tempfile.mkstemp(prefix="cleanup-worktree-index-")
    os.close(temporary_fd)
    temporary_index = Path(temporary_name)
    try:
        shutil.copyfile(index, temporary_index)
        temporary_env = os.environ.copy()
        temporary_env["GIT_INDEX_FILE"] = os.fspath(temporary_index)
        for relative, skip_worktree, assume_unchanged in checks:
            if skip_worktree:
                _git(
                    root,
                    "update-index",
                    "--no-skip-worktree",
                    "--",
                    relative,
                    env=temporary_env,
                )
            if assume_unchanged:
                _git(
                    root,
                    "update-index",
                    "--no-assume-unchanged",
                    "--",
                    relative,
                    env=temporary_env,
                )
        result = _git(
            root,
            "diff-files",
            "--quiet",
            "--ignore-submodules=none",
            "--",
            check=False,
            env=temporary_env,
        )
        if result.returncode == 0:
            return False
        if result.returncode == 1:
            return True
        message = result.stderr.decode("utf-8", errors="replace").strip()
        raise CleanupError(message or "index flagで隠れた変更の確認に失敗しました")
    finally:
        temporary_index.unlink(missing_ok=True)


def _ignored_untracked(root: Path) -> list[str]:
    result = _git(
        root,
        "ls-files",
        "--others",
        "--ignored",
        "-z",
        "--exclude-standard",
    )
    return [
        item.decode("utf-8", errors="surrogateescape")
        for item in result.stdout.split(b"\0")
        if item
    ]


def _matching_source_files(source: Path, include: Path) -> set[str]:
    result = _git(
        source,
        "ls-files",
        "--others",
        "--ignored",
        "-z",
        f"--exclude-from={include}",
    )
    return {
        item.decode("utf-8", errors="surrogateescape")
        for item in result.stdout.split(b"\0")
        if item
    }


def _same_regular_file(left: Path, right: Path, left_root: Path, right_root: Path) -> bool:
    try:
        left_stat = left.lstat()
        right_stat = right.lstat()
    except FileNotFoundError:
        return False
    if not stat.S_ISREG(left_stat.st_mode) or not stat.S_ISREG(right_stat.st_mode):
        return False
    try:
        if not left.resolve(strict=True).is_relative_to(left_root):
            return False
        if not right.resolve(strict=True).is_relative_to(right_root):
            return False
    except (OSError, RuntimeError):
        return False

    with left.open("rb") as left_file, right.open("rb") as right_file:
        while True:
            left_chunk = left_file.read(1024 * 1024)
            right_chunk = right_file.read(1024 * 1024)
            if left_chunk != right_chunk:
                return False
            if not left_chunk:
                return True


def _ignored_files_are_disposable(source: Path, destination: Path) -> bool:
    ignored = _ignored_untracked(destination)
    if not ignored:
        return True

    include = source / ".worktreeinclude"
    if not _git_predicate(source, "ls-files", "--error-unmatch", "--", ".worktreeinclude"):
        return False
    try:
        include_stat = include.lstat()
    except FileNotFoundError:
        return False
    if not stat.S_ISREG(include_stat.st_mode) or not include.resolve(
        strict=True
    ).is_relative_to(source):
        return False

    matching = _matching_source_files(source, include)
    for relative in ignored:
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts or relative not in matching:
            return False
        if _git_predicate(source, "ls-files", "--error-unmatch", "--", relative):
            return False
        if not _git_predicate(source, "check-ignore", "-q", "--", relative):
            return False
        if not _same_regular_file(
            source / relative,
            destination / relative,
            source,
            destination,
        ):
            return False
    return True


def cleanup(source_arg: Path, destination_arg: Path, branch: str) -> Path:
    source = _worktree_root(source_arg, "source")
    destination = _worktree_root(destination_arg, "destination")
    if source == destination:
        raise CleanupError("sourceとdestinationには別のworktreeを指定してください")
    if _common_dir(source) != _common_dir(destination):
        raise CleanupError("sourceとdestinationは同じGit repositoryに属していません")

    expected_ref = _checked_branch(source, branch)
    current = _git(destination, "symbolic-ref", "--quiet", "HEAD", check=False)
    if current.returncode == 1:
        raise CleanupError("destinationは期待されたbranchをcheckoutしていません")
    if current.returncode != 0:
        message = current.stderr.decode("utf-8", errors="replace").strip()
        raise CleanupError(message or "destination branchの確認に失敗しました")
    if current.stdout.decode().strip() != expected_ref:
        raise CleanupError("destinationは別のbranchです")

    status = _git(
        destination,
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
    )
    if status.stdout:
        raise CleanupError("destinationに未コミットまたは未追跡の作業があります")
    if _hidden_tracked_changes(destination):
        raise CleanupError("destinationにindex flagで隠れた変更があります")
    if not _ignored_files_are_disposable(source, destination):
        raise CleanupError("destinationに削除可能と確認できないignored fileがあります")

    _git(source, "worktree", "remove", "--", os.fspath(destination))
    return destination


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Remove one clean worktree after its pull request is merged."
    )
    parser.add_argument("source", type=Path, help="base-side worktree root")
    parser.add_argument("destination", type=Path, help="worktree to remove")
    parser.add_argument("--branch", required=True, help="expected work branch name")
    args = parser.parse_args(argv)
    try:
        removed = cleanup(args.source, args.destination, args.branch)
    except (OSError, CleanupError) as exc:
        print(f"cleanup-worktree: {exc}", file=sys.stderr)
        return 1
    print(f"cleanup-worktree: removed={removed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
