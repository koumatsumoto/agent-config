from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[2]
HELPER = REPO_ROOT / "templates/skills/km-plan/scripts/plan-artifact.py"
MARKER = "<!-- km:plan:managed -->"


class PlanArtifactHelperTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="plan-artifact-test-"))
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.outside = self.root / "outside"
        self.outside.mkdir()

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def _run(self, *args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, os.fspath(HELPER), *args],
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def _artifact(self, content: str = f"{MARKER}\n\n## 実装時確認事項\n\nなし。\n") -> Path:
        path = self.outside / "plan.md"
        path.write_text(content, encoding="utf-8")
        return path

    def _validate(self, artifact: Path) -> subprocess.CompletedProcess[str]:
        return self._run("validate", "--repo-root", os.fspath(self.repo), os.fspath(artifact))

    def test_init_creates_expected_unique_artifact_outside_repo(self) -> None:
        first = self._run("init", "--repo-root", os.fspath(self.repo))
        second = self._run("init", "--repo-root", os.fspath(self.repo))
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(len(first.stdout.splitlines()), 1)
        first_path = Path(first.stdout.strip())
        second_path = Path(second.stdout.strip())
        self.assertTrue(first_path.is_absolute())
        self.assertEqual(first_path.name, "plan.md")
        self.assertEqual(first_path.read_bytes(), f"{MARKER}\n\n".encode())
        self.assertNotEqual(first_path.parent, second_path.parent)
        with self.assertRaises(ValueError):
            first_path.resolve().relative_to(self.repo.resolve())
        shutil.rmtree(first_path.parent, ignore_errors=True)
        shutil.rmtree(second_path.parent, ignore_errors=True)

    def test_init_rejects_temp_directory_inside_repo_and_cleans_it(self) -> None:
        env = os.environ.copy()
        env["TMPDIR"] = os.fspath(self.repo)
        result = self._run("init", "--repo-root", os.fspath(self.repo), env=env)
        self.assertEqual(result.returncode, 3)
        self.assertEqual(result.stdout, "")
        self.assertIn("outside", result.stderr)
        self.assertEqual(list(self.repo.iterdir()), [])

    def test_init_reports_cleanup_failure_as_runtime_failure(self) -> None:
        spec = spec_from_file_location("plan_artifact_test_module", HELPER)
        assert spec is not None and spec.loader is not None
        module = module_from_spec(spec)
        spec.loader.exec_module(module)
        created = self.repo / "km-plan-forced"
        created.mkdir()
        cleanup_error = OSError("cleanup failed")

        with (
            mock.patch.object(module.tempfile, "mkdtemp", return_value=os.fspath(created)),
            mock.patch.object(module.shutil, "rmtree", side_effect=cleanup_error),
        ):
            with self.assertRaisesRegex(RuntimeError, "cannot remove temporary directory"):
                module.init_artifact(os.fspath(self.repo))

    def test_validate_accepts_valid_artifact_without_modifying_bytes(self) -> None:
        artifact = self._artifact()
        before = artifact.read_bytes()
        result = self._validate(artifact)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, f"{artifact.resolve()}\n")
        self.assertEqual(artifact.read_bytes(), before)

    def test_validate_rejects_missing_duplicate_and_displaced_marker(self) -> None:
        cases = {
            "missing": "## 実装時確認事項\n",
            "duplicate": f"{MARKER}\n{MARKER}\n## 実装時確認事項\n",
            "displaced": f"intro\n{MARKER}\n## 実装時確認事項\n",
        }
        for name, content in cases.items():
            with self.subTest(name=name):
                result = self._validate(self._artifact(content))
                self.assertEqual(result.returncode, 3)
                self.assertEqual(result.stdout, "")
                self.assertIn("marker", result.stderr)

    def test_validate_rejects_missing_duplicate_and_inexact_heading(self) -> None:
        cases = {
            "missing": f"{MARKER}\n",
            "duplicate": f"{MARKER}\n# 実装時確認事項\n### 実装時確認事項\n",
            "suffix": f"{MARKER}\n## 実装時確認事項（任意）\n",
            "colon": f"{MARKER}\n## 実装時確認事項:\n",
        }
        for name, content in cases.items():
            with self.subTest(name=name):
                result = self._validate(self._artifact(content))
                self.assertEqual(result.returncode, 3)
                self.assertEqual(result.stdout, "")
                self.assertIn("heading", result.stderr)

    def test_validate_rejects_artifact_inside_repository(self) -> None:
        artifact = self.repo / "plan.md"
        artifact.write_text(f"{MARKER}\n## 実装時確認事項\n", encoding="utf-8")
        result = self._validate(artifact)
        self.assertEqual(result.returncode, 3)
        self.assertIn("outside", result.stderr)

    def test_validate_rejects_empty_artifact(self) -> None:
        result = self._validate(self._artifact(""))
        self.assertEqual(result.returncode, 3)
        self.assertIn("empty", result.stderr)

    def test_validate_reports_invalid_utf8_as_runtime_failure(self) -> None:
        artifact = self.outside / "plan.md"
        artifact.write_bytes(b"\xff\xfe")
        result = self._validate(artifact)
        self.assertEqual(result.returncode, 1)
        self.assertIn("UTF-8", result.stderr)

    def test_usage_errors_exit_two(self) -> None:
        for args in (("init",), ("validate",), ("--unknown",)):
            with self.subTest(args=args):
                result = self._run(*args)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(result.stdout, "")

    def test_helper_does_not_require_git_or_gh_on_path(self) -> None:
        artifact = self._artifact()
        env = os.environ.copy()
        env["PATH"] = ""
        result = self._run(
            "validate", "--repo-root", os.fspath(self.repo), os.fspath(artifact), env=env
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
