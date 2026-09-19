#!/usr/bin/env python3
"""Remove one clean, expected Git worktree without deleting its branch."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


class CleanupError(RuntimeError):
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


def _has_hidden_tracked_state(root: Path) -> bool:
    entries = _git(root, "ls-files", "-v", "-z").stdout.split(b"\0")
    for entry in entries:
        if not entry:
            continue
        if len(entry) < 3 or entry[1:2] != b" ":
            raise CleanupError("tracked fileのindex状態を確認できません")
        tag = entry[0]
        # `S` is skip-worktree; lowercase tags mean assume-unchanged.
        if tag == ord("S") or ord("a") <= tag <= ord("z"):
            return True
    return False


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

    if _has_hidden_tracked_state(destination):
        raise CleanupError(
            "destinationに変更を隠すindex flagが設定されたtracked fileがあります"
        )

    status = _git(
        destination,
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
        "--ignored=matching",
    )
    if status.stdout:
        raise CleanupError("destinationに未コミットまたは未追跡の作業があります")

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
