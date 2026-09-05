from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
HELPER = REPO_ROOT / "templates/skills/km-open-file/scripts/open-file.sh"


class OpenFileHelperTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="open-file-test-"))
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.log = self.root / "calls.log"
        self._command("uname", 'printf "%s\\n" "${FAKE_UNAME:-MINGW64_NT}"')
        self._command(
            "grep",
            '[ "${FAKE_WSL:-0}" = 1 ]',
        )
        converter = r'''
printf '%s\n' "$0 $*" >> "$FAKE_CALL_LOG"
[ "${FAKE_CONVERT_FAIL:-0}" != 1 ] || exit 2
if [ "$1" = -u ]; then
  printf '%s\n' "$FAKE_POSIX_PATH"
else
  printf '%s\n' 'C:\converted path'
fi
'''
        self._command("cygpath", converter)
        self._command("wslpath", converter)
        self._command(
            "explorer.exe",
            r'''printf 'explorer env=%s' "${MSYS2_ARG_CONV_EXCL:-}" >> "$FAKE_CALL_LOG"
printf ' arg=<%s>' "$@" >> "$FAKE_CALL_LOG"
printf '\n' >> "$FAKE_CALL_LOG"
exit "${FAKE_EXPLORER_RC:-0}"
''',
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)

    def _command(self, name: str, body: str) -> None:
        path = self.bin / name
        path.write_text(f"#!/usr/bin/env bash\n{body}\n", encoding="utf-8")
        path.chmod(0o755)

    def _run(
        self, target: str, *, cwd: Path | None = None, env_extra: dict[str, str] | None = None
    ) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env.update(
            {
                "PATH": f"{self.bin}:{env['PATH']}",
                "FAKE_CALL_LOG": os.fspath(self.log),
                "FAKE_POSIX_PATH": os.fspath(self.root / "windows input.html"),
            }
        )
        if env_extra:
            env.update(env_extra)
        return subprocess.run(
            ["bash", os.fspath(HELPER), target],
            cwd=cwd or self.root,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    def test_git_bash_uses_cygpath_and_relative_html_from_calling_cwd(self) -> None:
        target = self.root / "space name.HTML"
        target.write_text("html", encoding="utf-8")
        result = self._run(target.name)
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = self.log.read_text(encoding="utf-8")
        self.assertIn("cygpath -w -- space name.HTML", calls)
        self.assertIn("explorer env= arg=<C:\\converted path>", calls)

    def test_wsl_uses_wslpath(self) -> None:
        target = self.root / "page.html"
        target.write_text("html", encoding="utf-8")
        result = self._run(
            os.fspath(target), env_extra={"FAKE_UNAME": "Linux", "FAKE_WSL": "1"}
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("wslpath -w", self.log.read_text(encoding="utf-8"))

    def test_windows_path_is_normalized_before_dispatch(self) -> None:
        normalized = self.root / "windows input.html"
        normalized.write_text("html", encoding="utf-8")
        result = self._run(r"C:\with space\page.html")
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = self.log.read_text(encoding="utf-8")
        self.assertIn(r"cygpath -u -- C:\with space\page.html", calls)
        self.assertIn(f"cygpath -w -- {normalized}", calls)

    def test_directory_and_non_html_file_use_safe_dispatches(self) -> None:
        directory = self.root / "folder"
        directory.mkdir()
        other = self.root / "note.txt"
        other.write_text("do not run", encoding="utf-8")
        directory_result = self._run(os.fspath(directory))
        self.assertEqual(directory_result.returncode, 0, directory_result.stderr)
        directory_call = self.log.read_text(encoding="utf-8").splitlines()[-1]
        self.assertEqual(directory_call, r"explorer env= arg=<C:\converted path>")

        self.log.unlink()
        file_result = self._run(os.fspath(other))
        self.assertEqual(file_result.returncode, 0, file_result.stderr)
        file_call = self.log.read_text(encoding="utf-8").splitlines()[-1]
        self.assertEqual(
            file_call, r"explorer env=* arg=</select,C:\converted path>"
        )

    def test_unsupported_environment_does_not_dispatch(self) -> None:
        target = self.root / "page.html"
        target.write_text("html", encoding="utf-8")
        result = self._run(os.fspath(target), env_extra={"FAKE_UNAME": "Linux"})
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("未対応", result.stderr)
        self.assertFalse(self.log.exists())

    def test_missing_path_and_conversion_failure_do_not_dispatch(self) -> None:
        missing = self._run(os.fspath(self.root / "missing.html"))
        self.assertNotEqual(missing.returncode, 0)
        self.assertIn("見つかりません", missing.stderr)

        target = self.root / "page.html"
        target.write_text("html", encoding="utf-8")
        failed = self._run(
            os.fspath(target), env_extra={"FAKE_CONVERT_FAIL": "1"}
        )
        self.assertNotEqual(failed.returncode, 0)
        self.assertIn("path変換", failed.stderr)
        calls = self.log.read_text(encoding="utf-8")
        self.assertNotIn("explorer", calls)

    def test_explorer_nonzero_still_means_dispatch_succeeded(self) -> None:
        target = self.root / "page.html"
        target.write_text("html", encoding="utf-8")
        result = self._run(
            os.fspath(target), env_extra={"FAKE_EXPLORER_RC": "17"}
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("起動要求", result.stdout)

    def test_file_content_is_not_printed(self) -> None:
        secret = "CONTENT-MUST-NOT-APPEAR"
        target = self.root / "note.txt"
        target.write_text(secret, encoding="utf-8")
        result = self._run(os.fspath(target))
        self.assertNotIn(secret, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
