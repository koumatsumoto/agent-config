"""Tests for agent_config.verify_install."""

from __future__ import annotations

import shutil
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from agent_config import fs, install, paths, verify_install


class VerifyInstallTests(unittest.TestCase):
    def setUp(self) -> None:
        self.home = Path(tempfile.mkdtemp(prefix="verify-test-"))
        with patch("sys.stdout", new=StringIO()):
            install.install(self.home)

    def tearDown(self) -> None:
        shutil.rmtree(self.home, ignore_errors=True)

    def test_clean_install_verifies(self) -> None:
        with patch("sys.stdout", new=StringIO()):
            report = verify_install.verify(self.home)
        self.assertEqual(
            report.fail_count(), 0, f"unexpected failures: {report.failures}"
        )
        self.assertGreater(report.checks, 0)

    def test_missing_file_detected(self) -> None:
        target = self.home / paths.TEMPLATE_FILES[0].dest_rel
        target.unlink()
        with patch("sys.stdout", new=StringIO()):
            report = verify_install.verify(self.home)
        self.assertGreater(report.fail_count(), 0)
        self.assertTrue(any("missing" in m for m in report.failures))

    def test_drift_detected(self) -> None:
        target = self.home / paths.TEMPLATE_FILES[0].dest_rel
        target.write_text("not the template content", encoding="utf-8")
        with patch("sys.stdout", new=StringIO()):
            report = verify_install.verify(self.home)
        self.assertTrue(any("drift" in m for m in report.failures))

    def test_mode_drift_detected_on_posix(self) -> None:
        if not fs.is_posix():
            self.skipTest("POSIX-only")
        target = self.home / paths.TEMPLATE_FILES[0].dest_rel
        target.chmod(0o644)
        with patch("sys.stdout", new=StringIO()):
            report = verify_install.verify(self.home)
        self.assertTrue(any("mode drift" in m for m in report.failures))


if __name__ == "__main__":
    unittest.main()
