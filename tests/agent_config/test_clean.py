"""Tests for agent_config.clean."""

from __future__ import annotations

import shutil
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from agent_config import clean, install, paths


class CleanTests(unittest.TestCase):
    def setUp(self) -> None:
        self.home = Path(tempfile.mkdtemp(prefix="clean-test-"))
        with patch("sys.stdout", new=StringIO()):
            install.install(self.home)

    def tearDown(self) -> None:
        shutil.rmtree(self.home, ignore_errors=True)

    def _run_clean(self) -> str:
        with patch("sys.stdout", new=StringIO()) as out:
            rc = clean.clean(self.home)
        self.assertEqual(rc, 0)
        return out.getvalue()

    def test_removes_managed_files(self) -> None:
        self._run_clean()
        for spec in paths.TEMPLATE_FILES:
            dest = self.home / spec.dest_rel
            self.assertFalse(dest.exists(), f"still present: {dest}")

    def test_removes_managed_trees(self) -> None:
        self._run_clean()
        for tspec in paths.TEMPLATE_TREES:
            self.assertFalse((self.home / tspec.dest_rel).exists())

    def test_creates_bak_for_each(self) -> None:
        self._run_clean()
        for spec in paths.TEMPLATE_FILES:
            bak = self.home / (spec.dest_rel + ".bak")
            self.assertTrue(bak.exists(), f"missing bak: {bak}")

    def test_preserves_settings_json(self) -> None:
        self._run_clean()
        settings = self.home / paths.SETTINGS_DEST_REL
        self.assertTrue(
            settings.exists(),
            "clean() must not remove ~/.claude/settings.json (carries user values)",
        )

    def test_skip_when_already_absent(self) -> None:
        self._run_clean()
        out = self._run_clean()
        self.assertIn("skip:", out)


if __name__ == "__main__":
    unittest.main()
