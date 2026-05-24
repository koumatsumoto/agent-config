"""Tests for scripts/run-skill-tests.py."""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "run-skill-tests.py"


def has_pyyaml() -> bool:
    return importlib.util.find_spec("yaml") is not None


@unittest.skipUnless(has_pyyaml(), "pyyaml is required for skill test runner")
class RunSkillTestsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = Path(tempfile.mkdtemp(prefix="skill-runs-test-"))

    def tearDown(self) -> None:
        shutil.rmtree(self.dir, ignore_errors=True)

    def run_script(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_scaffold_writes_to_output_dir(self) -> None:
        result = self.run_script(
            "scaffold",
            "--label",
            "unit",
            "--client",
            "Codex",
            "--model",
            "static",
            "--output-dir",
            str(self.dir),
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        run_file = Path(result.stdout.strip())
        self.assertTrue(run_file.is_file(), result.stdout)
        self.assertEqual(run_file.parent, self.dir)
        self.assertIn("# Skills Test Run", run_file.read_text(encoding="utf-8"))

    def test_list_still_reads_manifest(self) -> None:
        result = self.run_script("list")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("case(s)", result.stdout)


if __name__ == "__main__":
    unittest.main()
