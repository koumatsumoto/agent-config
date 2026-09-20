from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
LAUNCHERS = (
    REPO_ROOT / "templates/skills/km-github-workflow/scripts/run-python.sh",
    REPO_ROOT / "templates/skills/km-plan/scripts/run-python.sh",
)


@unittest.skipUnless(shutil.which("bash"), "bash is required")
class RunPythonLauncherTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="run-python-test-"))
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.bash = shutil.which("bash")
        assert self.bash is not None

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def _candidate(self, name: str, *, supports: bool) -> None:
        body = """#!/bin/sh
if [ "$1" = "-c" ]; then
  exit %d
fi
printf '%%s\\n' "$0" "$@"
""" % (0 if supports else 1)
        path = self.bin / name
        path.write_text(body, encoding="utf-8")
        path.chmod(0o755)

    def _run(self, launcher: Path, *args: str) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["PATH"] = os.fspath(self.bin)
        return subprocess.run(
            [self.bash, os.fspath(launcher), *args],
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def test_prefers_python3_and_preserves_arguments(self) -> None:
        self._candidate("python3", supports=True)
        self._candidate("python", supports=True)

        for launcher in LAUNCHERS:
            with self.subTest(launcher=launcher):
                result = self._run(launcher, "script.py", "value with spaces", "--flag")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(
                    result.stdout.splitlines(),
                    [os.fspath(self.bin / "python3"), "script.py", "value with spaces", "--flag"],
                )

    def test_falls_back_to_compatible_python(self) -> None:
        self._candidate("python3", supports=False)
        self._candidate("python", supports=True)

        for launcher in LAUNCHERS:
            with self.subTest(launcher=launcher):
                result = self._run(launcher, "script.py")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.splitlines()[0], os.fspath(self.bin / "python"))

    def test_fails_without_compatible_python(self) -> None:
        self._candidate("python3", supports=False)

        for launcher in LAUNCHERS:
            with self.subTest(launcher=launcher):
                result = self._run(launcher, "script.py")
                self.assertEqual(result.returncode, 1)
                self.assertIn("Python 3.9+ not found", result.stderr)

    def test_requires_script_argument(self) -> None:
        self._candidate("python3", supports=True)

        for launcher in LAUNCHERS:
            with self.subTest(launcher=launcher):
                result = self._run(launcher)
                self.assertEqual(result.returncode, 2)
                self.assertIn("script is required", result.stderr)
