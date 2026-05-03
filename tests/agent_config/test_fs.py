"""Tests for agent_config.fs."""

from __future__ import annotations

import os
import shutil
import stat
import tempfile
import unittest
from pathlib import Path

from agent_config import fs


class AtomicWriteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = Path(tempfile.mkdtemp(prefix="fs-test-"))

    def tearDown(self) -> None:
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_atomic_write_creates_file(self) -> None:
        target = self.dir / "out.txt"
        fs.atomic_write_text(target, "hello")
        self.assertEqual(target.read_text(encoding="utf-8"), "hello")

    def test_atomic_write_applies_0600_on_posix(self) -> None:
        if not fs.is_posix():
            self.skipTest("POSIX-only")
        target = self.dir / "secret.txt"
        fs.atomic_write_text(target, "secret")
        mode = target.stat().st_mode & 0o777
        self.assertEqual(mode, 0o600)

    def test_atomic_write_replaces_existing(self) -> None:
        target = self.dir / "out.txt"
        target.write_text("old", encoding="utf-8")
        fs.atomic_write_text(target, "new")
        self.assertEqual(target.read_text(encoding="utf-8"), "new")

    def test_atomic_write_replaces_symlink_at_dest(self) -> None:
        if not fs.is_posix():
            self.skipTest("POSIX-only")
        outside = self.dir / "outside.txt"
        outside.write_text("outside-original", encoding="utf-8")
        target = self.dir / "linked.txt"
        os.symlink(outside, target)
        fs.atomic_write_text(target, "new-content")
        # The symlink at `target` is replaced by a regular file; outside is unchanged.
        self.assertFalse(target.is_symlink())
        self.assertEqual(target.read_text(encoding="utf-8"), "new-content")
        self.assertEqual(outside.read_text(encoding="utf-8"), "outside-original")

    def test_atomic_write_no_predictable_tmp_left_behind(self) -> None:
        target = self.dir / "out.txt"
        fs.atomic_write_text(target, "x")
        leftovers = [p for p in self.dir.iterdir() if p.name.startswith("out.txt.")]
        self.assertEqual(leftovers, [])


class IsWithinTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = Path(tempfile.mkdtemp(prefix="fs-test-"))

    def tearDown(self) -> None:
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_inside_directory(self) -> None:
        self.assertTrue(fs.is_within(self.dir / "a" / "b", self.dir))

    def test_outside_directory(self) -> None:
        outside = Path(tempfile.gettempdir()) / "definitely-not-here-12345"
        self.assertFalse(fs.is_within(outside, self.dir))

    def test_assert_within_raises(self) -> None:
        outside = Path(tempfile.gettempdir()) / "definitely-not-here-12345"
        with self.assertRaises(PermissionError):
            fs.assert_within(outside, self.dir)


class InstallFileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = Path(tempfile.mkdtemp(prefix="fs-test-"))
        self.src = self.dir / "src.txt"
        self.dest = self.dir / "out" / "dest.txt"
        self.src.write_text("hello", encoding="utf-8")

    def tearDown(self) -> None:
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_copies_when_missing(self) -> None:
        status = fs.install_file(self.src, self.dest)
        self.assertEqual(status, "copied")
        self.assertEqual(self.dest.read_text(encoding="utf-8"), "hello")

    def test_ok_when_identical(self) -> None:
        fs.install_file(self.src, self.dest)
        status = fs.install_file(self.src, self.dest)
        self.assertEqual(status, "ok")

    def test_replaces_when_different_with_backup(self) -> None:
        self.dest.parent.mkdir(parents=True, exist_ok=True)
        self.dest.write_text("old", encoding="utf-8")
        status = fs.install_file(self.src, self.dest)
        self.assertEqual(status, "replaced")
        self.assertEqual(self.dest.read_text(encoding="utf-8"), "hello")
        bak = self.dest.with_name(self.dest.name + ".bak")
        self.assertEqual(bak.read_text(encoding="utf-8"), "old")

    def test_refuses_symlink_source(self) -> None:
        if not fs.is_posix():
            self.skipTest("POSIX-only")
        link = self.dir / "link.txt"
        os.symlink(self.src, link)
        with self.assertRaises(FileNotFoundError):
            fs.install_file(link, self.dest)


class InstallTreeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = Path(tempfile.mkdtemp(prefix="fs-test-"))
        self.src_root = self.dir / "src"
        self.dest_root = self.dir / "dest"
        (self.src_root / "sub").mkdir(parents=True)
        (self.src_root / "a.txt").write_text("a", encoding="utf-8")
        (self.src_root / "sub" / "b.txt").write_text("b", encoding="utf-8")

    def tearDown(self) -> None:
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_copies_tree(self) -> None:
        results = fs.install_tree(self.src_root, self.dest_root)
        statuses = sorted(s for s, _ in results)
        self.assertEqual(statuses, ["copied", "copied"])
        self.assertEqual((self.dest_root / "a.txt").read_text(encoding="utf-8"), "a")
        self.assertEqual((self.dest_root / "sub" / "b.txt").read_text(encoding="utf-8"), "b")

    def test_boundary_enforcement(self) -> None:
        with self.assertRaises(PermissionError):
            fs.install_tree(self.src_root, self.dest_root, boundary=self.dir / "other")

    def test_idempotent_rerun(self) -> None:
        fs.install_tree(self.src_root, self.dest_root)
        results = fs.install_tree(self.src_root, self.dest_root)
        statuses = sorted(s for s, _ in results)
        self.assertEqual(statuses, ["ok", "ok"])

    def test_refuses_symlink_in_template(self) -> None:
        if not fs.is_posix():
            self.skipTest("POSIX-only")
        target = self.src_root / "a.txt"
        link = self.src_root / "link.txt"
        os.symlink(target, link)
        with self.assertRaises(PermissionError):
            fs.install_tree(self.src_root, self.dest_root)

    def test_refuses_symlink_loop_in_template(self) -> None:
        # A symlink loop inside src_root would hang Python 3.13's rglob
        # if it followed symlinks; install_tree must use a non-following walk.
        if not fs.is_posix():
            self.skipTest("POSIX-only")
        loop = self.src_root / "loop"
        os.symlink(self.src_root.resolve(), loop)
        with self.assertRaises(PermissionError):
            fs.install_tree(self.src_root, self.dest_root)

    def test_boundary_checked_before_dest_root_mkdir(self) -> None:
        # Defense-in-depth: install_tree must refuse a dest_root outside the
        # boundary BEFORE creating or chmod'ing it.
        unwritten = self.dir / "outside"
        with self.assertRaises(PermissionError):
            fs.install_tree(self.src_root, unwritten, boundary=self.dir / "other")
        self.assertFalse(unwritten.exists())


class BackupTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = Path(tempfile.mkdtemp(prefix="fs-test-"))

    def tearDown(self) -> None:
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_backup_returns_none_when_missing(self) -> None:
        result = fs.backup(self.dir / "nope")
        self.assertIsNone(result)

    def test_backup_moves_file(self) -> None:
        target = self.dir / "f.txt"
        target.write_text("v1", encoding="utf-8")
        result = fs.backup(target)
        self.assertEqual(result, target.with_name("f.txt.bak"))
        self.assertFalse(target.exists())
        self.assertEqual(result.read_text(encoding="utf-8"), "v1")

    def test_backup_replaces_existing_bak(self) -> None:
        target = self.dir / "f.txt"
        bak = target.with_name("f.txt.bak")
        target.write_text("v2", encoding="utf-8")
        bak.write_text("old-bak", encoding="utf-8")
        fs.backup(target)
        self.assertEqual(bak.read_text(encoding="utf-8"), "v2")

    def test_remove_with_backup_skipped_when_missing(self) -> None:
        self.assertEqual(fs.remove_with_backup(self.dir / "nope"), "skipped")

    def test_remove_with_backup_moves_to_bak(self) -> None:
        target = self.dir / "f.txt"
        target.write_text("data", encoding="utf-8")
        result = fs.remove_with_backup(target)
        self.assertEqual(result, "backed_up")
        self.assertFalse(target.exists())
        self.assertEqual(target.with_name("f.txt.bak").read_text(encoding="utf-8"), "data")


if __name__ == "__main__":
    unittest.main()
