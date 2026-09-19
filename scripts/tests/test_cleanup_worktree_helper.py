from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[2]
HELPER = REPO_ROOT / "templates/skills/km-github-workflow/scripts/cleanup-worktree.py"
SPEC = importlib.util.spec_from_file_location("cleanup_worktree_helper", HELPER)
assert SPEC is not None and SPEC.loader is not None
cleanup_worktree_helper = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(cleanup_worktree_helper)
PREPARE_HELPER = REPO_ROOT / "templates/skills/km-github-workflow/scripts/prepare-worktree.py"
PREPARE_SPEC = importlib.util.spec_from_file_location(
    "prepare_worktree_helper_for_cleanup", PREPARE_HELPER
)
assert PREPARE_SPEC is not None and PREPARE_SPEC.loader is not None
prepare_worktree_helper = importlib.util.module_from_spec(PREPARE_SPEC)
PREPARE_SPEC.loader.exec_module(prepare_worktree_helper)


class CleanupWorktreeHelperTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="cleanup-worktree-test-"))
        self.repo = self.root / "repo"
        self.destination = self.root / "destination"
        self.repo.mkdir()
        self._git(self.repo, "init", "-q")
        self._git(self.repo, "config", "user.name", "Test User")
        self._git(self.repo, "config", "user.email", "test@example.invalid")
        (self.repo / "tracked.txt").write_text("tracked", encoding="utf-8")
        self._git(self.repo, "add", "tracked.txt")
        self._git(self.repo, "commit", "-qm", "fixture")
        self._git(
            self.repo,
            "worktree",
            "add",
            "-q",
            "-b",
            "work",
            os.fspath(self.destination),
        )

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

    def _run(
        self,
        source: Path | None = None,
        destination: Path | None = None,
        branch: str = "work",
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [
                sys.executable,
                os.fspath(HELPER),
                os.fspath(source or self.repo),
                os.fspath(destination or self.destination),
                "--branch",
                branch,
            ],
            cwd=self.root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def assert_destination_preserved(self) -> None:
        self.assertTrue(self.destination.is_dir())
        self.assertTrue((self.destination / "tracked.txt").is_file())

    def test_clean_expected_worktree_is_removed_without_deleting_branch(self) -> None:
        source_head = self._git(self.repo, "rev-parse", "HEAD").stdout.strip()

        result = self._run()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.destination.exists())
        self.assertEqual(
            self._git(self.repo, "rev-parse", "refs/heads/work").stdout.strip(),
            source_head,
        )
        self.assertEqual(self._git(self.repo, "status", "--short").stdout, "")

    def test_tracked_dirty_worktree_is_rejected(self) -> None:
        (self.destination / "tracked.txt").write_text("changed", encoding="utf-8")

        result = self._run()

        self.assertNotEqual(result.returncode, 0)
        self.assert_destination_preserved()
        self.assertEqual((self.destination / "tracked.txt").read_text(), "changed")

    def test_assume_unchanged_file_is_rejected(self) -> None:
        self._git(
            self.destination,
            "update-index",
            "--assume-unchanged",
            "tracked.txt",
        )
        (self.destination / "tracked.txt").write_text("hidden change", encoding="utf-8")

        result = self._run()

        self.assertNotEqual(result.returncode, 0)
        self.assert_destination_preserved()
        self.assertEqual(
            (self.destination / "tracked.txt").read_text(), "hidden change"
        )

    def test_clean_assume_unchanged_file_is_allowed(self) -> None:
        self._git(
            self.destination,
            "update-index",
            "--assume-unchanged",
            "tracked.txt",
        )

        result = self._run()

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.destination.exists())

    def test_skip_worktree_file_is_rejected(self) -> None:
        self._git(
            self.destination,
            "update-index",
            "--skip-worktree",
            "tracked.txt",
        )
        (self.destination / "tracked.txt").write_text("hidden change", encoding="utf-8")

        result = self._run()

        self.assertNotEqual(result.returncode, 0)
        self.assert_destination_preserved()
        self.assertEqual(
            (self.destination / "tracked.txt").read_text(), "hidden change"
        )

    def test_missing_skip_worktree_file_outside_sparse_checkout_is_rejected(self) -> None:
        self._git(
            self.destination,
            "update-index",
            "--skip-worktree",
            "tracked.txt",
        )
        (self.destination / "tracked.txt").unlink()

        result = self._run()

        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(self.destination.is_dir())
        self.assertFalse((self.destination / "tracked.txt").exists())

    def test_clean_sparse_checkout_is_allowed(self) -> None:
        (self.destination / "included").mkdir()
        (self.destination / "included/file.txt").write_text("included", encoding="utf-8")
        excluded_paths = {
            f"excluded/file-{number}.txt" for number in range(3)
        }
        (self.destination / "excluded").mkdir()
        for relative in excluded_paths:
            (self.destination / relative).write_text("excluded", encoding="utf-8")
        self._git(self.destination, "add", "included", "excluded")
        self._git(self.destination, "commit", "-qm", "sparse fixture")
        self._git(self.destination, "sparse-checkout", "init", "--cone")
        self._git(self.destination, "sparse-checkout", "set", "included")
        for relative in excluded_paths:
            self.assertFalse((self.destination / relative).exists())

        check_rules_inputs: list[bytes] = []
        original_git = cleanup_worktree_helper._git

        def record_git(
            root: Path,
            *args: str,
            check: bool = True,
            env: dict[str, str] | None = None,
            input_data: bytes | None = None,
        ) -> subprocess.CompletedProcess[bytes]:
            if args[:2] == ("sparse-checkout", "check-rules"):
                assert input_data is not None
                check_rules_inputs.append(input_data)
            return original_git(
                root, *args, check=check, env=env, input_data=input_data
            )

        with patch.object(cleanup_worktree_helper, "_git", side_effect=record_git):
            cleanup_worktree_helper.cleanup(self.repo, self.destination, "work")

        self.assertEqual(len(check_rules_inputs), 1)
        checked = {
            item.decode("utf-8")
            for item in check_rules_inputs[0].split(b"\0")
            if item
        }
        self.assertEqual(checked, excluded_paths)
        self.assertFalse(self.destination.exists())

    def test_untracked_file_is_rejected(self) -> None:
        marker = self.destination / "new.txt"
        marker.write_text("keep", encoding="utf-8")

        result = self._run()

        self.assertNotEqual(result.returncode, 0)
        self.assert_destination_preserved()
        self.assertEqual(marker.read_text(), "keep")

    def test_ignored_file_is_rejected(self) -> None:
        (self.destination / ".gitignore").write_text("local.env\n", encoding="utf-8")
        self._git(self.destination, "add", ".gitignore")
        self._git(self.destination, "commit", "-qm", "ignore local file")
        marker = self.destination / "local.env"
        marker.write_text("keep", encoding="utf-8")

        result = self._run()

        self.assertNotEqual(result.returncode, 0)
        self.assert_destination_preserved()
        self.assertEqual(marker.read_text(), "keep")

    def test_prepare_copy_is_disposable_but_changed_copy_is_rejected(self) -> None:
        self._git(self.repo, "worktree", "remove", os.fspath(self.destination))
        self._git(self.repo, "branch", "-D", "work")
        (self.repo / ".gitignore").write_text(".env\n", encoding="utf-8")
        (self.repo / ".worktreeinclude").write_text(".env\n", encoding="utf-8")
        self._git(self.repo, "add", ".gitignore", ".worktreeinclude")
        self._git(self.repo, "commit", "-qm", "prepare policy")
        (self.repo / ".env").write_text("source value", encoding="utf-8")

        copied, skipped = prepare_worktree_helper.setup(
            self.repo, self.destination, "work"
        )
        self.assertEqual((copied, skipped), (1, 0))
        self.assertEqual((self.destination / ".env").read_text(), "source value")
        removed = cleanup_worktree_helper.cleanup(
            self.repo, self.destination, "work"
        )
        self.assertEqual(removed, self.destination)
        self.assertFalse(self.destination.exists())

        changed = self.root / "changed"
        copied, skipped = prepare_worktree_helper.setup(
            self.repo, changed, "work-changed"
        )
        self.assertEqual((copied, skipped), (1, 0))
        (changed / ".env").write_text("changed value", encoding="utf-8")
        with self.assertRaises(cleanup_worktree_helper.CleanupError):
            cleanup_worktree_helper.cleanup(
                self.repo, changed, "work-changed"
            )
        self.assertEqual((changed / ".env").read_text(), "changed value")

    def test_different_branch_is_rejected(self) -> None:
        result = self._run(branch="other")

        self.assertNotEqual(result.returncode, 0)
        self.assert_destination_preserved()

    def test_different_repository_is_rejected(self) -> None:
        other = self.root / "other"
        other.mkdir()
        self._git(other, "init", "-q")
        self._git(other, "config", "user.name", "Test User")
        self._git(other, "config", "user.email", "test@example.invalid")
        (other / "tracked.txt").write_text("other", encoding="utf-8")
        self._git(other, "add", "tracked.txt")
        self._git(other, "commit", "-qm", "other")

        result = self._run(source=other)

        self.assertNotEqual(result.returncode, 0)
        self.assert_destination_preserved()

    def test_general_directory_is_rejected(self) -> None:
        general = self.repo / "general"
        general.mkdir()

        result = self._run(source=general)

        self.assertNotEqual(result.returncode, 0)
        self.assert_destination_preserved()

    @unittest.skipUnless(hasattr(os, "symlink"), "symlink support required")
    def test_symlink_destination_is_rejected(self) -> None:
        alias = self.root / "alias"
        alias.symlink_to(self.destination, target_is_directory=True)

        result = self._run(destination=alias)

        self.assertNotEqual(result.returncode, 0)
        self.assert_destination_preserved()

    def test_source_itself_is_rejected(self) -> None:
        result = self._run(destination=self.repo, branch="master")

        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(self.repo.is_dir())
        self.assert_destination_preserved()

    def test_remove_failure_preserves_destination_and_branch(self) -> None:
        def fail_remove(
            root: Path,
            *args: str,
            check: bool = True,
            env: dict[str, str] | None = None,
            input_data: bytes | None = None,
        ) -> subprocess.CompletedProcess[bytes]:
            if args[:2] == ("worktree", "remove"):
                raise cleanup_worktree_helper.CleanupError("injected failure")
            return original_git(
                root, *args, check=check, env=env, input_data=input_data
            )

        original_git = cleanup_worktree_helper._git
        with patch.object(cleanup_worktree_helper, "_git", side_effect=fail_remove):
            with self.assertRaises(cleanup_worktree_helper.CleanupError):
                cleanup_worktree_helper.cleanup(self.repo, self.destination, "work")

        self.assert_destination_preserved()
        self.assertNotEqual(
            self._git(self.repo, "show-ref", "--verify", "refs/heads/work").stdout,
            "",
        )

    def test_remove_command_never_uses_force(self) -> None:
        calls: list[tuple[str, ...]] = []
        original_git = cleanup_worktree_helper._git

        def record_git(
            root: Path,
            *args: str,
            check: bool = True,
            env: dict[str, str] | None = None,
            input_data: bytes | None = None,
        ) -> subprocess.CompletedProcess[bytes]:
            calls.append(args)
            return original_git(
                root, *args, check=check, env=env, input_data=input_data
            )

        with patch.object(cleanup_worktree_helper, "_git", side_effect=record_git):
            cleanup_worktree_helper.cleanup(self.repo, self.destination, "work")

        remove = next(args for args in calls if args[:2] == ("worktree", "remove"))
        self.assertNotIn("--force", remove)
        self.assertNotIn("-f", remove)


if __name__ == "__main__":
    unittest.main()
