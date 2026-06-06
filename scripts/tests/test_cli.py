"""Tests for scripts/cli.py (install / clean / verify / merge + fs helpers).

Run with the scripts/ dir as the top-level import root:
    python3 -m unittest discover -s scripts/tests -t scripts
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import cli


# --------------------------------------------------------------------------- #
# fs helpers
# --------------------------------------------------------------------------- #
class AtomicWriteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = Path(tempfile.mkdtemp(prefix="fs-test-"))

    def tearDown(self) -> None:
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_atomic_write_creates_file(self) -> None:
        target = self.dir / "out.txt"
        cli.atomic_write_text(target, "hello")
        self.assertEqual(target.read_text(encoding="utf-8"), "hello")

    def test_atomic_write_applies_0600_on_posix(self) -> None:
        if not cli.is_posix():
            self.skipTest("POSIX-only")
        target = self.dir / "secret.txt"
        cli.atomic_write_text(target, "secret")
        mode = target.stat().st_mode & 0o777
        self.assertEqual(mode, 0o600)

    def test_atomic_write_replaces_existing(self) -> None:
        target = self.dir / "out.txt"
        target.write_text("old", encoding="utf-8")
        cli.atomic_write_text(target, "new")
        self.assertEqual(target.read_text(encoding="utf-8"), "new")

    def test_atomic_write_replaces_symlink_at_dest(self) -> None:
        if not cli.is_posix():
            self.skipTest("POSIX-only")
        outside = self.dir / "outside.txt"
        outside.write_text("outside-original", encoding="utf-8")
        target = self.dir / "linked.txt"
        os.symlink(outside, target)
        cli.atomic_write_text(target, "new-content")
        # The symlink at `target` is replaced by a regular file; outside is unchanged.
        self.assertFalse(target.is_symlink())
        self.assertEqual(target.read_text(encoding="utf-8"), "new-content")
        self.assertEqual(outside.read_text(encoding="utf-8"), "outside-original")

    def test_atomic_write_no_predictable_tmp_left_behind(self) -> None:
        target = self.dir / "out.txt"
        cli.atomic_write_text(target, "x")
        leftovers = [p for p in self.dir.iterdir() if p.name.startswith("out.txt.")]
        self.assertEqual(leftovers, [])


class IsWithinTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = Path(tempfile.mkdtemp(prefix="fs-test-"))

    def tearDown(self) -> None:
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_inside_directory(self) -> None:
        self.assertTrue(cli.is_within(self.dir / "a" / "b", self.dir))

    def test_outside_directory(self) -> None:
        outside = Path(tempfile.gettempdir()) / "definitely-not-here-12345"
        self.assertFalse(cli.is_within(outside, self.dir))

    def test_assert_within_raises(self) -> None:
        outside = Path(tempfile.gettempdir()) / "definitely-not-here-12345"
        with self.assertRaises(PermissionError):
            cli.assert_within(outside, self.dir)


class InstallFileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = Path(tempfile.mkdtemp(prefix="fs-test-"))
        self.src = self.dir / "src.txt"
        self.dest = self.dir / "out" / "dest.txt"
        self.src.write_text("hello", encoding="utf-8")

    def tearDown(self) -> None:
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_copies_when_missing(self) -> None:
        status = cli.install_file(self.src, self.dest)
        self.assertEqual(status, "copied")
        self.assertEqual(self.dest.read_text(encoding="utf-8"), "hello")

    def test_ok_when_identical(self) -> None:
        cli.install_file(self.src, self.dest)
        status = cli.install_file(self.src, self.dest)
        self.assertEqual(status, "ok")

    def test_replaces_when_different_with_backup(self) -> None:
        self.dest.parent.mkdir(parents=True, exist_ok=True)
        self.dest.write_text("old", encoding="utf-8")
        status = cli.install_file(self.src, self.dest)
        self.assertEqual(status, "replaced")
        self.assertEqual(self.dest.read_text(encoding="utf-8"), "hello")
        bak = self.dest.with_name(self.dest.name + ".bak")
        self.assertEqual(bak.read_text(encoding="utf-8"), "old")

    def test_refuses_symlink_source(self) -> None:
        if not cli.is_posix():
            self.skipTest("POSIX-only")
        link = self.dir / "link.txt"
        os.symlink(self.src, link)
        with self.assertRaises(FileNotFoundError):
            cli.install_file(link, self.dest)


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
        results = cli.install_tree(self.src_root, self.dest_root)
        statuses = sorted(s for s, _ in results)
        self.assertEqual(statuses, ["copied", "copied"])
        self.assertEqual((self.dest_root / "a.txt").read_text(encoding="utf-8"), "a")
        self.assertEqual((self.dest_root / "sub" / "b.txt").read_text(encoding="utf-8"), "b")

    def test_boundary_enforcement(self) -> None:
        with self.assertRaises(PermissionError):
            cli.install_tree(self.src_root, self.dest_root, boundary=self.dir / "other")

    def test_idempotent_rerun(self) -> None:
        cli.install_tree(self.src_root, self.dest_root)
        results = cli.install_tree(self.src_root, self.dest_root)
        statuses = sorted(s for s, _ in results)
        self.assertEqual(statuses, ["ok", "ok"])

    def test_refuses_symlink_in_template(self) -> None:
        if not cli.is_posix():
            self.skipTest("POSIX-only")
        target = self.src_root / "a.txt"
        link = self.src_root / "link.txt"
        os.symlink(target, link)
        with self.assertRaises(PermissionError):
            cli.install_tree(self.src_root, self.dest_root)

    def test_refuses_symlink_loop_in_template(self) -> None:
        # A symlink loop inside src_root would hang Python 3.13's rglob
        # if it followed symlinks; install_tree must use a non-following walk.
        if not cli.is_posix():
            self.skipTest("POSIX-only")
        loop = self.src_root / "loop"
        os.symlink(self.src_root.resolve(), loop)
        with self.assertRaises(PermissionError):
            cli.install_tree(self.src_root, self.dest_root)

    def test_boundary_checked_before_dest_root_mkdir(self) -> None:
        # Defense-in-depth: install_tree must refuse a dest_root outside the
        # boundary BEFORE creating or chmod'ing it.
        unwritten = self.dir / "outside"
        with self.assertRaises(PermissionError):
            cli.install_tree(self.src_root, unwritten, boundary=self.dir / "other")
        self.assertFalse(unwritten.exists())


class BackupTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = Path(tempfile.mkdtemp(prefix="fs-test-"))

    def tearDown(self) -> None:
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_backup_returns_none_when_missing(self) -> None:
        result = cli.backup(self.dir / "nope")
        self.assertIsNone(result)

    def test_backup_moves_file(self) -> None:
        target = self.dir / "f.txt"
        target.write_text("v1", encoding="utf-8")
        result = cli.backup(target)
        self.assertEqual(result, target.with_name("f.txt.bak"))
        self.assertFalse(target.exists())
        self.assertEqual(result.read_text(encoding="utf-8"), "v1")

    def test_backup_replaces_existing_bak(self) -> None:
        target = self.dir / "f.txt"
        bak = target.with_name("f.txt.bak")
        target.write_text("v2", encoding="utf-8")
        bak.write_text("old-bak", encoding="utf-8")
        cli.backup(target)
        self.assertEqual(bak.read_text(encoding="utf-8"), "v2")

    def test_remove_with_backup_skipped_when_missing(self) -> None:
        self.assertEqual(cli.remove_with_backup(self.dir / "nope"), "skipped")

    def test_remove_with_backup_moves_to_bak(self) -> None:
        target = self.dir / "f.txt"
        target.write_text("data", encoding="utf-8")
        result = cli.remove_with_backup(target)
        self.assertEqual(result, "backed_up")
        self.assertFalse(target.exists())
        self.assertEqual(target.with_name("f.txt.bak").read_text(encoding="utf-8"), "data")


# --------------------------------------------------------------------------- #
# settings.json merge
# --------------------------------------------------------------------------- #
class MergeFunctionTests(unittest.TestCase):
    def test_template_wins_for_shared_keys(self) -> None:
        merged = cli.merge({"a": 1, "b": "tpl"}, {"a": 99})
        self.assertEqual(merged["a"], 1)
        self.assertEqual(merged["b"], "tpl")

    def test_template_keys_added(self) -> None:
        merged = cli.merge({"a": 1}, {})
        self.assertEqual(merged, {"a": 1})

    def test_user_only_keys_kept(self) -> None:
        merged = cli.merge({"a": 1}, {"theme": "dark"})
        self.assertEqual(merged["theme"], "dark")
        self.assertEqual(merged["a"], 1)


class MergeIntoTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = Path(tempfile.mkdtemp(prefix="merge-test-"))
        self.template = self.dir / "template.json"
        self.dest = self.dir / "dest.json"
        self.bak = Path(f"{self.dest}.bak")
        self.template.write_text(json.dumps({"a": 1, "b": "template"}), encoding="utf-8")

    def tearDown(self) -> None:
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_creates_when_dest_missing(self) -> None:
        result = cli.merge_into(self.template, self.dest)
        self.assertEqual(result, "created")
        self.assertEqual(json.loads(self.dest.read_text(encoding="utf-8")), {"a": 1, "b": "template"})

    def test_ok_when_no_change(self) -> None:
        cli.merge_into(self.template, self.dest)
        result = cli.merge_into(self.template, self.dest)
        self.assertEqual(result, "ok")
        self.assertFalse(self.bak.exists())

    def test_merged_template_wins_user_only_kept(self) -> None:
        self.dest.write_text(json.dumps({"a": 99, "theme": "dark"}), encoding="utf-8")
        result = cli.merge_into(self.template, self.dest)
        self.assertEqual(result, "merged")
        merged = json.loads(self.dest.read_text(encoding="utf-8"))
        # template declares "a" -> template value wins (propagates on re-run)
        self.assertEqual(merged["a"], 1)
        # template does not declare "theme" -> user value is preserved
        self.assertEqual(merged["theme"], "dark")
        self.assertEqual(merged["b"], "template")
        self.assertTrue(self.bak.exists())

    def test_invalid_json_warned_and_replaced(self) -> None:
        self.dest.write_text("{not valid", encoding="utf-8")
        with patch("sys.stderr", new=StringIO()) as err:
            result = cli.merge_into(self.template, self.dest)
        self.assertEqual(result, "merged")
        self.assertIn("warn:", err.getvalue())
        self.assertEqual(self.bak.read_text(encoding="utf-8"), "{not valid")

    def test_non_object_json_warned(self) -> None:
        self.dest.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
        with patch("sys.stderr", new=StringIO()) as err:
            result = cli.merge_into(self.template, self.dest)
        self.assertEqual(result, "merged")
        self.assertIn("warn:", err.getvalue())

    def test_template_must_be_object(self) -> None:
        self.template.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
        with self.assertRaises(ValueError):
            cli.merge_into(self.template, self.dest)

    def test_empty_dest_merges_template(self) -> None:
        # Exercises the `text.strip()` empty branch of read_existing.
        self.dest.write_text("", encoding="utf-8")
        result = cli.merge_into(self.template, self.dest)
        self.assertEqual(result, "merged")
        self.assertEqual(
            json.loads(self.dest.read_text(encoding="utf-8")),
            {"a": 1, "b": "template"},
        )

    def test_applies_0600_on_posix(self) -> None:
        if not cli.is_posix():
            self.skipTest("POSIX-only")
        cli.merge_into(self.template, self.dest)
        mode = self.dest.stat().st_mode & 0o777
        self.assertEqual(mode, 0o600)


class MergeCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = Path(tempfile.mkdtemp(prefix="merge-test-"))
        self.template = self.dir / "template.json"
        self.dest = self.dir / "dest.json"
        self.template.write_text(json.dumps({"a": 1}), encoding="utf-8")

    def tearDown(self) -> None:
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_no_command_returns_usage_error(self) -> None:
        with patch("sys.stderr", new=StringIO()) as err:
            rc = cli.main(["cli.py"])
        self.assertEqual(rc, 2)
        self.assertIn("usage:", err.getvalue())

    def test_merge_missing_args_returns_2(self) -> None:
        with patch("sys.stderr", new=StringIO()) as err:
            rc = cli.main(["cli.py", "merge"])
        self.assertEqual(rc, 2)
        self.assertIn("usage:", err.getvalue())

    def test_unknown_command_returns_2(self) -> None:
        with patch("sys.stderr", new=StringIO()) as err:
            rc = cli.main(["cli.py", "bogus"])
        self.assertEqual(rc, 2)
        self.assertIn("unknown command", err.getvalue())

    def test_merge_creates(self) -> None:
        with patch("sys.stdout", new=StringIO()) as out:
            rc = cli.main(["cli.py", "merge", str(self.template), str(self.dest)])
        self.assertEqual(rc, 0)
        self.assertIn("created:", out.getvalue())

    def test_merge_existing_emits_backup_and_merged(self) -> None:
        self.dest.write_text(json.dumps({"a": 99}), encoding="utf-8")
        with patch("sys.stdout", new=StringIO()) as out:
            rc = cli.main(["cli.py", "merge", str(self.template), str(self.dest)])
        self.assertEqual(rc, 0)
        output = out.getvalue()
        self.assertIn("backup:", output)
        self.assertIn("merged:", output)

    def test_merge_noop_emits_ok(self) -> None:
        with patch("sys.stdout", new=StringIO()):
            cli.main(["cli.py", "merge", str(self.template), str(self.dest)])
        with patch("sys.stdout", new=StringIO()) as out:
            rc = cli.main(["cli.py", "merge", str(self.template), str(self.dest)])
        self.assertEqual(rc, 0)
        self.assertIn("ok:", out.getvalue())


# --------------------------------------------------------------------------- #
# install
# --------------------------------------------------------------------------- #
class InstallTests(unittest.TestCase):
    def setUp(self) -> None:
        self.home = Path(tempfile.mkdtemp(prefix="install-test-"))

    def tearDown(self) -> None:
        shutil.rmtree(self.home, ignore_errors=True)

    def _run_install(self) -> str:
        with patch("sys.stdout", new=StringIO()) as out:
            rc = cli.install(self.home)
        self.assertEqual(rc, 0)
        return out.getvalue()

    def test_creates_all_template_files(self) -> None:
        self._run_install()
        for spec in cli.TEMPLATE_FILES:
            dest = self.home / spec.dest_rel
            self.assertTrue(dest.is_file(), f"missing: {dest}")

    def test_creates_managed_dirs(self) -> None:
        self._run_install()
        for sub in cli.INSTALL_HOME_DIRS:
            self.assertTrue((self.home / sub).is_dir())

    def test_creates_settings_json(self) -> None:
        self._run_install()
        settings = self.home / cli.SETTINGS_DEST_REL
        self.assertTrue(settings.is_file())
        data = json.loads(settings.read_text(encoding="utf-8"))
        # statusLine is a known recommended key in the template
        self.assertIn("statusLine", data)

    def test_idempotent(self) -> None:
        self._run_install()
        out = self._run_install()
        # On second run every line should be ok: ...
        non_ok = [
            line for line in out.splitlines()
            if line and not line.startswith("ok:") and not line.startswith("Install ")
        ]
        self.assertEqual(non_ok, [], f"unexpected non-ok lines: {non_ok}")

    def test_settings_user_value_preserved_on_rerun(self) -> None:
        self._run_install()
        settings = self.home / cli.SETTINGS_DEST_REL
        data = json.loads(settings.read_text(encoding="utf-8"))
        data["theme"] = "user-pick"
        settings.write_text(json.dumps(data), encoding="utf-8")
        self._run_install()
        merged = json.loads(settings.read_text(encoding="utf-8"))
        self.assertEqual(merged["theme"], "user-pick")

    def test_dir_perms_0700_on_posix(self) -> None:
        if not cli.is_posix():
            self.skipTest("POSIX-only")
        self._run_install()
        for sub in cli.INSTALL_HOME_DIRS:
            mode = (self.home / sub).stat().st_mode & 0o777
            self.assertEqual(mode, 0o700)

    def test_file_perms_match_spec_on_posix(self) -> None:
        if not cli.is_posix():
            self.skipTest("POSIX-only")
        self._run_install()
        for spec in cli.TEMPLATE_FILES:
            dest = self.home / spec.dest_rel
            mode = dest.stat().st_mode & 0o777
            self.assertEqual(mode, spec.mode, f"{dest} mode={oct(mode)} expected {oct(spec.mode)}")

    def test_runs_to_completion(self) -> None:
        # Lower-level boundary guarantees are covered by InstallTreeTests.
        self._run_install()


# --------------------------------------------------------------------------- #
# clean
# --------------------------------------------------------------------------- #
class CleanTests(unittest.TestCase):
    def setUp(self) -> None:
        self.home = Path(tempfile.mkdtemp(prefix="clean-test-"))
        with patch("sys.stdout", new=StringIO()):
            cli.install(self.home)

    def tearDown(self) -> None:
        shutil.rmtree(self.home, ignore_errors=True)

    def _run_clean(self) -> str:
        with patch("sys.stdout", new=StringIO()) as out:
            rc = cli.clean(self.home)
        self.assertEqual(rc, 0)
        return out.getvalue()

    def test_removes_managed_files(self) -> None:
        self._run_clean()
        for spec in cli.TEMPLATE_FILES:
            dest = self.home / spec.dest_rel
            self.assertFalse(dest.exists(), f"still present: {dest}")

    def test_removes_managed_trees(self) -> None:
        self._run_clean()
        for tspec in cli.TEMPLATE_TREES:
            self.assertFalse((self.home / tspec.dest_rel).exists())

    def test_creates_bak_for_each(self) -> None:
        self._run_clean()
        for spec in cli.TEMPLATE_FILES:
            bak = self.home / (spec.dest_rel + ".bak")
            self.assertTrue(bak.exists(), f"missing bak: {bak}")

    def test_preserves_settings_json(self) -> None:
        self._run_clean()
        settings = self.home / cli.SETTINGS_DEST_REL
        self.assertTrue(
            settings.exists(),
            "clean() must not remove ~/.claude/settings.json (carries user values)",
        )

    def test_skip_when_already_absent(self) -> None:
        self._run_clean()
        out = self._run_clean()
        self.assertIn("skip:", out)


# --------------------------------------------------------------------------- #
# verify
# --------------------------------------------------------------------------- #
class VerifyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.home = Path(tempfile.mkdtemp(prefix="verify-test-"))
        with patch("sys.stdout", new=StringIO()):
            cli.install(self.home)

    def tearDown(self) -> None:
        shutil.rmtree(self.home, ignore_errors=True)

    def test_clean_install_verifies(self) -> None:
        with patch("sys.stdout", new=StringIO()):
            report = cli.verify(self.home)
        self.assertEqual(report.fail_count(), 0, f"unexpected failures: {report.failures}")
        self.assertGreater(report.checks, 0)

    def test_missing_file_detected(self) -> None:
        target = self.home / cli.TEMPLATE_FILES[0].dest_rel
        target.unlink()
        with patch("sys.stdout", new=StringIO()):
            report = cli.verify(self.home)
        self.assertGreater(report.fail_count(), 0)
        self.assertTrue(any("missing" in m for m in report.failures))

    def test_drift_detected(self) -> None:
        target = self.home / cli.TEMPLATE_FILES[0].dest_rel
        target.write_text("not the template content", encoding="utf-8")
        with patch("sys.stdout", new=StringIO()):
            report = cli.verify(self.home)
        self.assertTrue(any("drift" in m for m in report.failures))

    def test_mode_drift_detected_on_posix(self) -> None:
        if not cli.is_posix():
            self.skipTest("POSIX-only")
        target = self.home / cli.TEMPLATE_FILES[0].dest_rel
        target.chmod(0o644)
        with patch("sys.stdout", new=StringIO()):
            report = cli.verify(self.home)
        self.assertTrue(any("mode drift" in m for m in report.failures))

    def test_settings_missing_template_key_detected(self) -> None:
        settings = self.home / cli.SETTINGS_DEST_REL
        data = json.loads(settings.read_text(encoding="utf-8"))
        removed_key = next(iter(data))
        del data[removed_key]
        settings.write_text(json.dumps(data), encoding="utf-8")
        with patch("sys.stdout", new=StringIO()):
            report = cli.verify(self.home)
        self.assertTrue(
            any("settings missing template key" in m and removed_key in m for m in report.failures),
            report.failures,
        )

    def test_settings_invalid_json_detected(self) -> None:
        settings = self.home / cli.SETTINGS_DEST_REL
        settings.write_text("{not valid", encoding="utf-8")
        with patch("sys.stdout", new=StringIO()):
            report = cli.verify(self.home)
        self.assertTrue(any("invalid json" in m for m in report.failures))

    def test_settings_non_object_detected(self) -> None:
        settings = self.home / cli.SETTINGS_DEST_REL
        settings.write_text(json.dumps(["not", "object"]), encoding="utf-8")
        with patch("sys.stdout", new=StringIO()):
            report = cli.verify(self.home)
        self.assertTrue(any("settings.json must be a JSON object" in m for m in report.failures))

    def test_settings_existing_key_override_is_allowed(self) -> None:
        settings = self.home / cli.SETTINGS_DEST_REL
        data = json.loads(settings.read_text(encoding="utf-8"))
        override_key = next(iter(data))
        data[override_key] = "user override"
        settings.write_text(json.dumps(data), encoding="utf-8")
        with patch("sys.stdout", new=StringIO()):
            report = cli.verify(self.home)
        self.assertFalse(any(override_key in m for m in report.failures), report.failures)


if __name__ == "__main__":
    unittest.main()
