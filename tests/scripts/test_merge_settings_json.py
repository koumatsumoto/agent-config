"""Tests for scripts/merge-settings-json.py.

Run from repo root:
    python3 -m unittest tests.scripts.test_merge_settings_json
or:
    python3 tests/scripts/test_merge_settings_json.py
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "merge-settings-json.py"


def run_script(template: str, dest: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), template, dest],
        capture_output=True,
        text=True,
        check=False,
    )


class MergeSettingsJsonTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = Path(tempfile.mkdtemp(prefix="merge-test-"))
        self.template = self.dir / "template.json"
        self.dest = self.dir / "dest.json"
        self.bak = Path(f"{self.dest}.bak")
        self.template.write_text(
            json.dumps({"a": 1, "b": "template", "nested": {"x": 1}}),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.dir)

    def read_dest(self) -> dict:
        return json.loads(self.dest.read_text(encoding="utf-8"))

    def test_creates_when_missing(self) -> None:
        result = run_script(str(self.template), str(self.dest))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("created:", result.stdout)
        self.assertEqual(
            self.read_dest(),
            {"a": 1, "b": "template", "nested": {"x": 1}},
        )

    def test_output_has_0600_permissions(self) -> None:
        run_script(str(self.template), str(self.dest))
        mode = self.dest.stat().st_mode & 0o777
        self.assertEqual(mode, 0o600)

    def test_preserves_user_values_for_shared_keys(self) -> None:
        self.dest.write_text(
            json.dumps({"a": 99, "b": "user"}), encoding="utf-8"
        )
        result = run_script(str(self.template), str(self.dest))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("merged:", result.stdout)
        merged = self.read_dest()
        self.assertEqual(merged["a"], 99)
        self.assertEqual(merged["b"], "user")
        self.assertEqual(merged["nested"], {"x": 1})

    def test_keeps_user_only_keys(self) -> None:
        self.dest.write_text(
            json.dumps({"theme": "dark"}), encoding="utf-8"
        )
        run_script(str(self.template), str(self.dest))
        merged = self.read_dest()
        self.assertEqual(merged["theme"], "dark")
        self.assertEqual(merged["a"], 1)

    def test_idempotent_on_no_op_rerun(self) -> None:
        run_script(str(self.template), str(self.dest))
        if self.bak.exists():
            self.bak.unlink()
        result = run_script(str(self.template), str(self.dest))
        self.assertEqual(result.returncode, 0)
        self.assertIn("ok:", result.stdout)
        self.assertFalse(self.bak.exists(), "no-op rerun should not create a backup")

    def test_backup_created_on_change(self) -> None:
        original = json.dumps({"a": 99})
        self.dest.write_text(original, encoding="utf-8")
        result = run_script(str(self.template), str(self.dest))
        self.assertEqual(result.returncode, 0)
        self.assertIn("backup:", result.stdout)
        self.assertTrue(self.bak.exists())
        self.assertEqual(self.bak.read_text(encoding="utf-8"), original)

    def test_invalid_json_replaced_with_backup(self) -> None:
        self.dest.write_text("{not valid", encoding="utf-8")
        result = run_script(str(self.template), str(self.dest))
        self.assertEqual(result.returncode, 0)
        self.assertIn("warn:", result.stderr)
        self.assertIn("backup:", result.stdout)
        self.assertEqual(self.read_dest()["a"], 1)
        self.assertEqual(self.bak.read_text(encoding="utf-8"), "{not valid")

    def test_empty_file_treated_as_empty(self) -> None:
        self.dest.write_text("", encoding="utf-8")
        result = run_script(str(self.template), str(self.dest))
        self.assertEqual(result.returncode, 0)
        self.assertEqual(self.read_dest()["a"], 1)

    def test_non_object_json_treated_as_empty(self) -> None:
        self.dest.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
        result = run_script(str(self.template), str(self.dest))
        self.assertEqual(result.returncode, 0)
        self.assertIn("warn:", result.stderr)
        self.assertEqual(self.read_dest()["a"], 1)

    def test_usage_error_returns_2(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("usage:", result.stderr)

    def test_no_predictable_tmp_left_behind(self) -> None:
        run_script(str(self.template), str(self.dest))
        leftovers = [p for p in self.dir.iterdir() if p.name.startswith(self.dest.name + ".")
                     and p.suffix != ".bak"]
        self.assertEqual(leftovers, [], f"unexpected tmp files: {leftovers}")


if __name__ == "__main__":
    unittest.main()
