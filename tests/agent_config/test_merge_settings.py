"""Tests for agent_config.merge_settings."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from agent_config import merge_settings


class MergeFunctionTests(unittest.TestCase):
    def test_existing_wins_for_shared_keys(self) -> None:
        merged = merge_settings.merge({"a": 1, "b": "tpl"}, {"a": 99})
        self.assertEqual(merged["a"], 99)
        self.assertEqual(merged["b"], "tpl")

    def test_template_keys_added(self) -> None:
        merged = merge_settings.merge({"a": 1}, {})
        self.assertEqual(merged, {"a": 1})

    def test_user_only_keys_kept(self) -> None:
        merged = merge_settings.merge({"a": 1}, {"theme": "dark"})
        self.assertEqual(merged["theme"], "dark")
        self.assertEqual(merged["a"], 1)


class MergeIntoTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = Path(tempfile.mkdtemp(prefix="merge-test-"))
        self.template = self.dir / "template.json"
        self.dest = self.dir / "dest.json"
        self.bak = Path(f"{self.dest}.bak")
        self.template.write_text(
            json.dumps({"a": 1, "b": "template"}),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_creates_when_dest_missing(self) -> None:
        result = merge_settings.merge_into(self.template, self.dest)
        self.assertEqual(result, "created")
        self.assertEqual(json.loads(self.dest.read_text(encoding="utf-8")), {"a": 1, "b": "template"})

    def test_ok_when_no_change(self) -> None:
        merge_settings.merge_into(self.template, self.dest)
        result = merge_settings.merge_into(self.template, self.dest)
        self.assertEqual(result, "ok")
        self.assertFalse(self.bak.exists())

    def test_merged_preserves_user_values(self) -> None:
        self.dest.write_text(json.dumps({"a": 99, "theme": "dark"}), encoding="utf-8")
        result = merge_settings.merge_into(self.template, self.dest)
        self.assertEqual(result, "merged")
        merged = json.loads(self.dest.read_text(encoding="utf-8"))
        self.assertEqual(merged["a"], 99)
        self.assertEqual(merged["theme"], "dark")
        self.assertEqual(merged["b"], "template")
        self.assertTrue(self.bak.exists())

    def test_invalid_json_warned_and_replaced(self) -> None:
        self.dest.write_text("{not valid", encoding="utf-8")
        with patch("sys.stderr", new=StringIO()) as err:
            result = merge_settings.merge_into(self.template, self.dest)
        self.assertEqual(result, "merged")
        self.assertIn("warn:", err.getvalue())
        self.assertEqual(self.bak.read_text(encoding="utf-8"), "{not valid")

    def test_non_object_json_warned(self) -> None:
        self.dest.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
        with patch("sys.stderr", new=StringIO()) as err:
            result = merge_settings.merge_into(self.template, self.dest)
        self.assertEqual(result, "merged")
        self.assertIn("warn:", err.getvalue())

    def test_template_must_be_object(self) -> None:
        self.template.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
        with self.assertRaises(ValueError):
            merge_settings.merge_into(self.template, self.dest)


class MainTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = Path(tempfile.mkdtemp(prefix="merge-test-"))
        self.template = self.dir / "template.json"
        self.dest = self.dir / "dest.json"
        self.template.write_text(json.dumps({"a": 1}), encoding="utf-8")

    def tearDown(self) -> None:
        shutil.rmtree(self.dir, ignore_errors=True)

    def test_usage_error_returns_2(self) -> None:
        with patch("sys.stderr", new=StringIO()) as err:
            rc = merge_settings.main(["prog"])
        self.assertEqual(rc, 2)
        self.assertIn("usage:", err.getvalue())

    def test_main_creates(self) -> None:
        with patch("sys.stdout", new=StringIO()) as out:
            rc = merge_settings.main(["prog", str(self.template), str(self.dest)])
        self.assertEqual(rc, 0)
        self.assertIn("created:", out.getvalue())


if __name__ == "__main__":
    unittest.main()
