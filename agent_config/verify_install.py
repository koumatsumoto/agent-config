"""Verify installed templates match the repo source-of-truth.

Replaces the legacy scripts/verify-install.sh. On POSIX checks file modes
exactly; on Windows skips mode checks because NTFS does not honour POSIX
bits.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from agent_config import fs, paths


class VerifyReport:
    def __init__(self) -> None:
        self.failures: list[str] = []
        self.checks = 0

    def record(self, ok: bool, message: str) -> None:
        self.checks += 1
        if not ok:
            self.failures.append(message)

    def fail_count(self) -> int:
        return len(self.failures)


def _check_file(report: VerifyReport, src: Path, dest: Path) -> None:
    report.record(dest.exists(), f"missing: {dest}")
    if dest.exists():
        report.record(fs.same_content(src, dest), f"drift: {dest}")


def _check_mode(report: VerifyReport, path: Path, expected: int) -> None:
    if not fs.is_posix():
        return  # NTFS does not honour POSIX modes
    if not path.exists():
        report.record(False, f"missing: {path}")
        return
    actual = path.stat().st_mode & 0o777
    report.record(
        actual == expected,
        f"mode drift: {path} (expected {oct(expected)}, got {oct(actual)})",
    )


def _check_tree(report: VerifyReport, src_root: Path, dest_root: Path,
                dir_mode: int, file_mode: int) -> None:
    if not dest_root.exists():
        report.record(False, f"missing: {dest_root}")
        return
    _check_mode(report, dest_root, dir_mode)
    for src in sorted(src_root.rglob("*")):
        rel = src.relative_to(src_root)
        dest = dest_root / rel
        if src.is_dir():
            _check_mode(report, dest, dir_mode)
        elif src.is_file():
            _check_file(report, src, dest)
            _check_mode(report, dest, file_mode)


def _read_json_object(
    report: VerifyReport,
    path: Path,
    label: str,
) -> dict[str, object] | None:
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        report.record(False, f"missing: {path}")
        return None
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        report.record(False, f"invalid json: {path} ({exc})")
        return None
    is_object = isinstance(data, dict)
    report.record(is_object, f"{label} must be a JSON object: {path}")
    if not is_object:
        return None
    return data


def _check_settings_contract(
    report: VerifyReport,
    template: Path,
    dest: Path,
) -> None:
    template_data = _read_json_object(report, template, "settings template")
    dest_data = _read_json_object(report, dest, "settings.json")
    if template_data is None or dest_data is None:
        return

    for key in sorted(template_data):
        report.record(
            key in dest_data,
            f"settings missing template key: {dest} ({key})",
        )


def verify(home: Path, repo_root: Path = paths.REPO_ROOT) -> VerifyReport:
    report = VerifyReport()
    print("Verify Claude + Codex configuration")

    for spec in paths.TEMPLATE_FILES:
        src = repo_root / spec.src_rel
        dest = home / spec.dest_rel
        _check_file(report, src, dest)
        _check_mode(report, dest, spec.mode)

    for sub in paths.INSTALL_HOME_DIRS:
        _check_mode(report, home / sub, fs.DIR_MODE)

    for tspec in paths.TEMPLATE_TREES:
        src_root = repo_root / tspec.src_rel
        dest_root = home / tspec.dest_rel
        _check_tree(report, src_root, dest_root, tspec.dir_mode, tspec.file_mode)

    settings_dest = home / paths.SETTINGS_DEST_REL
    report.record(settings_dest.exists(), f"missing: {settings_dest}")
    _check_mode(report, settings_dest, fs.FILE_MODE)
    _check_settings_contract(
        report,
        repo_root / paths.SETTINGS_TEMPLATE_REL,
        settings_dest,
    )

    return report


def main(argv: list[str]) -> int:
    home = Path.home()
    report = verify(home)
    if report.failures:
        for msg in report.failures:
            print(msg)
        print(
            f"verify failed: {report.fail_count()} issue(s) "
            f"across {report.checks} check(s)"
        )
        return 1
    print(f"verify ok: {report.checks} check(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
