from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
HELPER = REPO_ROOT / "templates/skills/km-github-workflow/scripts/prepare-worktree.py"


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

    def _commit_fixture(self, *, include: str | None = ".env\n") -> None:
        (self.repo / ".gitignore").write_text(
            ".env\ncache/\nunlisted.txt\nlinked/\ncredential.private\n",
            encoding="utf-8",
        )
        (self.repo / "tracked.txt").write_text("tracked", encoding="utf-8")
        if include is not None:
            (self.repo / ".worktreeinclude").write_text(include, encoding="utf-8")
        self._git(self.repo, "add", ".gitignore", "tracked.txt")
        if include is not None:
            self._git(self.repo, "add", ".worktreeinclude")
        self._git(self.repo, "commit", "-qm", "fixture")
        self._git(self.repo, "worktree", "add", "-q", os.fspath(self.destination), "-b", "work")

    def _run(
        self, source: Path | None = None, destination: Path | None = None
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                os.fspath(HELPER),
                os.fspath(source or self.repo),
                os.fspath(destination or self.destination),
            ],
            cwd=self.root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

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
        self.assertIn("同じGit repository", result.stderr)

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
