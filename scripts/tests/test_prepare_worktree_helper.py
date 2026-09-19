from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import BinaryIO
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[2]
HELPER = REPO_ROOT / "templates/skills/km-github-workflow/scripts/prepare-worktree.py"
SPEC = importlib.util.spec_from_file_location("prepare_worktree_helper", HELPER)
assert SPEC is not None and SPEC.loader is not None
prepare_worktree_helper = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(prepare_worktree_helper)


class PrepareWorktreeHelperTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="prepare-worktree-test-"))
        self.repo = self.root / "repo"
        self.destination = self.root / "destination"
        self.repo.mkdir()
        self._git(self.repo, "init", "-q")
        self._git(self.repo, "config", "user.name", "Test User")
        self._git(self.repo, "config", "user.email", "test@example.invalid")

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def _git(self, cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", "-C", os.fspath(cwd), *args],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def _commit_fixture(
        self, *, include: str | None = ".env\n", extra_ignore: str = "", create_worktree: bool = True
    ) -> None:
        (self.repo / ".gitignore").write_text(
            ".env\ncache/\nunlisted.txt\nlinked/\ncredential.private\n"
            + extra_ignore,
            encoding="utf-8",
        )
        (self.repo / "tracked.txt").write_text("tracked", encoding="utf-8")
        if include is not None:
            (self.repo / ".worktreeinclude").write_text(include, encoding="utf-8")
        self._git(self.repo, "add", ".gitignore", "tracked.txt")
        if include is not None:
            self._git(self.repo, "add", ".worktreeinclude")
        self._git(self.repo, "commit", "-qm", "fixture")
        if create_worktree:
            self._git(self.repo, "worktree", "add", "-q", os.fspath(self.destination), "-b", "work")

    def _run(
        self,
        source: Path | None = None,
        destination: Path | None = None,
        *,
        env_extra: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        if env_extra:
            env.update(env_extra)
        return subprocess.run(
            [
                sys.executable,
                os.fspath(HELPER),
                os.fspath(source or self.repo),
                os.fspath(destination or self.destination),
                "--branch", "work",
            ],
            cwd=self.root,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def test_single_command_creates_branch_worktree_and_copies_files(self) -> None:
        self._commit_fixture(create_worktree=False)
        (self.repo / ".env").write_text("selected", encoding="utf-8")
        (self.repo / "tracked.txt").write_text("uncommitted", encoding="utf-8")
        result = self._run()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self._git(self.destination, "branch", "--show-current").stdout.strip(), "work")
        self.assertEqual((self.destination / ".env").read_text(), "selected")
        self.assertEqual((self.destination / "tracked.txt").read_text(), "tracked")
        self.assertEqual((self.repo / "tracked.txt").read_text(), "uncommitted")

    def test_creation_without_include_and_repeat_preserve_work(self) -> None:
        self._commit_fixture(include=None, create_worktree=False)
        result = self._run()
        self.assertEqual(result.returncode, 0, result.stderr)
        (self.destination / "tracked.txt").write_text("in progress", encoding="utf-8")
        again = self._run()
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertEqual((self.destination / "tracked.txt").read_text(), "in progress")

    def test_existing_branch_requires_explicit_mode(self) -> None:
        self._commit_fixture(create_worktree=False)
        self._git(self.repo, "branch", "work")
        result = self._run()
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.destination.exists())
        copied, skipped = prepare_worktree_helper.setup(
            self.repo, self.destination, "work", existing=True
        )
        self.assertEqual((copied, skipped), (0, 0))
        self.assertEqual(self._git(self.destination, "branch", "--show-current").stdout.strip(), "work")

    def test_existing_branch_cli_and_checked_out_branch_protection(self) -> None:
        self._commit_fixture(create_worktree=False)
        self._git(self.repo, "branch", "work")
        command = [sys.executable, os.fspath(HELPER), os.fspath(self.repo),
                   os.fspath(self.destination), "--branch", "work", "--existing"]
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        other = self.root / "other"
        with self.assertRaises(prepare_worktree_helper.PreparationError):
            prepare_worktree_helper.setup(self.repo, other, "work", existing=True)
        self.assertFalse(other.exists())
        self.assertTrue((self.destination / "tracked.txt").is_file())

    def test_existing_remote_tracking_branch_is_materialized(self) -> None:
        self._commit_fixture(create_worktree=False)
        remote = self.root / "remote.git"
        self._git(self.root, "init", "--bare", "-q", os.fspath(remote))
        self._git(self.repo, "remote", "add", "origin", os.fspath(remote))
        self._git(self.repo, "push", "-q", "origin", "HEAD:refs/heads/work")
        self._git(self.repo, "fetch", "-q", "origin")

        copied, skipped = prepare_worktree_helper.setup(
            self.repo, self.destination, "work", existing=True
        )

        self.assertEqual((copied, skipped), (0, 0))
        self.assertEqual(
            self._git(self.destination, "branch", "--show-current").stdout.strip(),
            "work",
        )
        upstream = self._git(
            self.destination, "rev-parse", "--abbrev-ref", "@{upstream}"
        ).stdout.strip()
        self.assertEqual(upstream, "origin/work")

    def test_ambiguous_remote_tracking_branch_is_rejected(self) -> None:
        self._commit_fixture(create_worktree=False)
        for name in ("origin", "upstream"):
            remote = self.root / f"{name}.git"
            self._git(self.root, "init", "--bare", "-q", os.fspath(remote))
            self._git(self.repo, "remote", "add", name, os.fspath(remote))
            self._git(self.repo, "push", "-q", name, "HEAD:refs/heads/work")
            self._git(self.repo, "fetch", "-q", name)

        with self.assertRaisesRegex(
            prepare_worktree_helper.PreparationError, "複数"
        ):
            prepare_worktree_helper.setup(
                self.repo, self.destination, "work", existing=True
            )
        self.assertFalse(self.destination.exists())

    def test_remote_tracking_branch_requires_exact_branch_name(self) -> None:
        self._commit_fixture(create_worktree=False)
        remote = self.root / "remote.git"
        self._git(self.root, "init", "--bare", "-q", os.fspath(remote))
        self._git(self.repo, "remote", "add", "origin", os.fspath(remote))
        self._git(
            self.repo,
            "push",
            "-q",
            "origin",
            "HEAD:refs/heads/archive/feat/123-x",
        )
        self._git(self.repo, "fetch", "-q", "origin")

        with self.assertRaisesRegex(
            prepare_worktree_helper.PreparationError, "見つかりません"
        ):
            prepare_worktree_helper.setup(
                self.repo, self.destination, "feat/123-x", existing=True
            )
        self.assertFalse(self.destination.exists())

    def test_remote_branch_cannot_select_source_local_files(self) -> None:
        self._commit_fixture(
            include=None, extra_ignore="private.env\n", create_worktree=False
        )
        remote = self.root / "remote.git"
        attacker = self.root / "attacker"
        self._git(self.root, "init", "--bare", "-q", os.fspath(remote))
        self._git(self.repo, "remote", "add", "origin", os.fspath(remote))
        self._git(
            self.repo,
            "worktree",
            "add",
            "-q",
            "-b",
            "attacker",
            os.fspath(attacker),
        )
        (attacker / ".worktreeinclude").write_text("private.env\n", encoding="utf-8")
        self._git(attacker, "add", ".worktreeinclude")
        self._git(attacker, "commit", "-qm", "malicious include")
        self._git(attacker, "push", "-q", "origin", "HEAD:refs/heads/work")
        self._git(self.repo, "fetch", "-q", "origin")
        (self.repo / "private.env").write_text("source secret", encoding="utf-8")

        copied, skipped = prepare_worktree_helper.setup(
            self.repo, self.destination, "work", existing=True
        )

        self.assertEqual((copied, skipped), (0, 0))
        self.assertFalse((self.destination / "private.env").exists())

    def test_invalid_base_does_not_create_worktree_or_branch(self) -> None:
        self._commit_fixture(create_worktree=False)
        with self.assertRaises(prepare_worktree_helper.PreparationError):
            prepare_worktree_helper.setup(self.repo, self.destination, "work", base="missing-ref")
        self.assertFalse(self.destination.exists())
        self.assertEqual(self._git(self.repo, "branch", "--list", "work").stdout, "")

    @unittest.skipUnless(hasattr(os, "symlink"), "symlink support required")
    def test_setup_rejects_symlink_destination(self) -> None:
        self._commit_fixture()
        alias = self.root / "alias"
        alias.symlink_to(self.destination, target_is_directory=True)
        with self.assertRaises(prepare_worktree_helper.PreparationError):
            prepare_worktree_helper.setup(self.repo, alias, "work")

    def test_existing_worktree_with_different_branch_is_rejected(self) -> None:
        self._commit_fixture()
        before = self._git(self.destination, "rev-parse", "HEAD").stdout
        with self.assertRaises(prepare_worktree_helper.PreparationError):
            prepare_worktree_helper.setup(self.repo, self.destination, "other")
        self.assertEqual(self._git(self.destination, "rev-parse", "HEAD").stdout, before)
        self.assertEqual(self._git(self.destination, "branch", "--show-current").stdout.strip(), "work")

    def test_existing_directory_is_not_repurposed(self) -> None:
        self._commit_fixture(create_worktree=False)
        self.destination.mkdir()
        marker = self.destination / "keep.txt"
        marker.write_text("keep", encoding="utf-8")
        result = self._run()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(marker.read_text(), "keep")
        branches = self._git(self.repo, "branch", "--list", "work").stdout
        self.assertEqual(branches, "")

    def test_base_ref_controls_new_branch(self) -> None:
        self._commit_fixture(create_worktree=False)
        base = self._git(self.repo, "rev-parse", "HEAD").stdout.strip()
        (self.repo / "later.txt").write_text("later", encoding="utf-8")
        self._git(self.repo, "add", "later.txt")
        self._git(self.repo, "commit", "-qm", "later")
        prepare_worktree_helper.setup(self.repo, self.destination, "work", base=base)
        self.assertEqual(self._git(self.destination, "rev-parse", "HEAD").stdout.strip(), base)
        self.assertFalse((self.destination / "later.txt").exists())

    def test_preparation_failure_keeps_worktree_for_retry(self) -> None:
        self._commit_fixture(create_worktree=False)
        (self.repo / ".env").write_text("selected", encoding="utf-8")
        with patch.object(prepare_worktree_helper, "_copy_regular_file", side_effect=OSError("failed")):
            with self.assertRaises(OSError):
                prepare_worktree_helper.setup(self.repo, self.destination, "work")
        self.assertTrue((self.destination / "tracked.txt").is_file())
        result = self._run()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.destination / ".env").read_text(), "selected")

    def test_nested_destination_is_rejected_before_creation(self) -> None:
        self._commit_fixture(create_worktree=False)
        target = self.repo / "nested"
        result = self._run(destination=target)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(target.exists())

    def test_no_tracked_include_is_a_noop(self) -> None:
        self._commit_fixture(include=None)
        result = self._run()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("copied=0", result.stdout)

    def test_literal_pattern_copies_only_listed_ignored_file(self) -> None:
        self._commit_fixture()
        (self.repo / ".env").write_text("selected", encoding="utf-8")
        (self.repo / "unlisted.txt").write_text("not selected", encoding="utf-8")
        result = self._run()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.destination / ".env").read_text(encoding="utf-8"), "selected")
        self.assertFalse((self.destination / "unlisted.txt").exists())

    def test_gitignore_pattern_selects_multiple_files(self) -> None:
        self._commit_fixture(include="cache/*.json\n")
        cache = self.repo / "cache"
        cache.mkdir()
        (cache / "a.json").write_text("a", encoding="utf-8")
        (cache / "b.json").write_text("b", encoding="utf-8")
        (cache / "skip.txt").write_text("skip", encoding="utf-8")
        result = self._run()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.destination / "cache/a.json").read_text(), "a")
        self.assertEqual((self.destination / "cache/b.json").read_text(), "b")
        self.assertFalse((self.destination / "cache/skip.txt").exists())

    def test_matching_but_not_git_ignored_and_tracked_files_are_not_copied(self) -> None:
        self._commit_fixture(include="public.txt\ntracked.txt\n")
        (self.repo / "public.txt").write_text("public", encoding="utf-8")
        result = self._run()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.destination / "public.txt").exists())
        self.assertEqual((self.destination / "tracked.txt").read_text(), "tracked")

    @unittest.skipUnless(hasattr(os, "symlink"), "symlink support required")
    def test_source_symlink_is_skipped(self) -> None:
        self._commit_fixture(include="linked\n")
        outside = self.root / "outside.txt"
        outside.write_text("outside", encoding="utf-8")
        os.symlink(outside, self.repo / "linked")
        result = self._run()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.destination / "linked").exists())

    def test_existing_destination_is_not_overwritten(self) -> None:
        self._commit_fixture()
        (self.repo / ".env").write_text("source", encoding="utf-8")
        (self.destination / ".env").write_text("destination", encoding="utf-8")
        result = self._run()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.destination / ".env").read_text(), "destination")
        self.assertIn("skipped=1", result.stdout)

    def test_file_not_ignored_in_destination_is_not_copied(self) -> None:
        self._commit_fixture(include="credential.private\n")
        destination_ignore = self.destination / ".gitignore"
        destination_ignore.write_text(
            destination_ignore.read_text(encoding="utf-8").replace(
                "credential.private\n", ""
            ),
            encoding="utf-8",
        )
        self._git(self.destination, "add", ".gitignore")
        self._git(self.destination, "commit", "-qm", "stop ignoring credential")
        (self.repo / "credential.private").write_text("secret", encoding="utf-8")
        result = self._run()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.destination / "credential.private").exists())
        self.assertEqual(self._git(self.destination, "status", "--short").stdout, "")

    @unittest.skipIf(os.name == "nt", "POSIX mode semantics required")
    def test_copy_never_broadens_source_mode(self) -> None:
        self._commit_fixture()
        source = self.repo / ".env"
        source.write_text("secret", encoding="utf-8")
        source.chmod(0o600)
        result = self._run()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.destination / ".env").stat().st_mode & 0o777, 0o600)

    @unittest.skipIf(os.name == "nt", "POSIX mode semantics required")
    def test_new_parent_directories_are_private(self) -> None:
        self._commit_fixture(
            include="private/nested/config.json\n", extra_ignore="private/\n"
        )
        private = self.repo / "private/nested"
        private.mkdir(parents=True, mode=0o700)
        (private / "config.json").write_text("secret", encoding="utf-8")

        previous_umask = os.umask(0o022)
        try:
            result = self._run()
        finally:
            os.umask(previous_umask)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.destination / "private").stat().st_mode & 0o777, 0o700)
        self.assertEqual(
            (self.destination / "private/nested").stat().st_mode & 0o777, 0o700
        )

    @unittest.skipIf(os.name == "nt", "POSIX mode semantics required")
    def test_existing_parent_directory_mode_is_unchanged(self) -> None:
        self._commit_fixture(
            include="private/config.json\n", extra_ignore="private/\n"
        )
        source_parent = self.repo / "private"
        source_parent.mkdir()
        (source_parent / "config.json").write_text("secret", encoding="utf-8")
        destination_parent = self.destination / "private"
        destination_parent.mkdir(mode=0o755)

        result = self._run()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(destination_parent.stat().st_mode & 0o777, 0o755)

    def test_partial_destination_is_removed_after_copy_failure(self) -> None:
        self._commit_fixture()
        source = self.repo / ".env"
        source.write_text("complete content", encoding="utf-8")

        def fail_after_partial_write(
            source_file: BinaryIO, destination_file: BinaryIO
        ) -> None:
            destination_file.write(source_file.read(4))
            destination_file.flush()
            raise OSError("injected copy failure")

        with patch.object(
            prepare_worktree_helper.shutil,
            "copyfileobj",
            side_effect=fail_after_partial_write,
        ):
            with self.assertRaises(prepare_worktree_helper.PreparationError):
                prepare_worktree_helper.prepare(self.repo, self.destination)

        destination = self.destination / ".env"
        self.assertFalse(destination.exists())
        copied, skipped = prepare_worktree_helper.prepare(self.repo, self.destination)
        self.assertEqual((copied, skipped), (1, 0))
        self.assertEqual(destination.read_text(encoding="utf-8"), "complete content")

    def test_git_fatal_in_predicates_fails_closed(self) -> None:
        self._commit_fixture()
        invalid_index = self.root / "invalid-index"
        invalid_index.mkdir()
        with patch.dict(os.environ, {"GIT_INDEX_FILE": os.fspath(invalid_index)}):
            with self.assertRaises(prepare_worktree_helper.PreparationError):
                prepare_worktree_helper._is_tracked(self.repo, ".worktreeinclude")
            with self.assertRaises(prepare_worktree_helper.PreparationError):
                prepare_worktree_helper._is_ignored(self.repo, ".env")
        result = self._run(env_extra={"GIT_INDEX_FILE": os.fspath(invalid_index)})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("prepare-worktree:", result.stderr)

    @unittest.skipUnless(hasattr(os, "symlink"), "symlink support required")
    def test_destination_parent_resolving_outside_is_rejected(self) -> None:
        self._commit_fixture(include="cache/*.json\n")
        cache = self.repo / "cache"
        cache.mkdir()
        (cache / "a.json").write_text("secret", encoding="utf-8")
        outside = self.root / "outside"
        outside.mkdir()
        (self.destination / "cache").symlink_to(outside, target_is_directory=True)
        result = self._run()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("destination worktree外", result.stderr)
        self.assertFalse((outside / "a.json").exists())

    def test_different_repositories_are_rejected(self) -> None:
        self._commit_fixture()
        other = self.root / "other"
        other.mkdir()
        self._git(other, "init", "-q")
        result = self._run(destination=other)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Git repository", result.stderr)

    def test_copy_does_not_change_index_or_print_file_content(self) -> None:
        self._commit_fixture()
        content = "SECRET-CONTENT-MUST-NOT-BE-LOGGED"
        (self.repo / ".env").write_text(content, encoding="utf-8")
        before_source = self._git(self.repo, "diff", "--cached", "--name-only").stdout
        before_destination = self._git(
            self.destination, "diff", "--cached", "--name-only"
        ).stdout
        result = self._run()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn(content, result.stdout + result.stderr)
        self.assertEqual(
            self._git(self.repo, "diff", "--cached", "--name-only").stdout,
            before_source,
        )
        self.assertEqual(
            self._git(self.destination, "diff", "--cached", "--name-only").stdout,
            before_destination,
        )

    def test_source_and_destination_must_be_worktree_roots(self) -> None:
        self._commit_fixture()
        child = self.repo / "child"
        child.mkdir()
        result = self._run(source=child)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("root", result.stderr)


if __name__ == "__main__":
    unittest.main()
