#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path


MARKER = "<!-- km:plan:managed -->"
INITIAL_CONTENT = f"{MARKER}\n\n".encode("utf-8")
REQUIRED_HEADING = "実装時確認事項"


class ContractViolation(Exception):
    pass


def resolve_directory(value: str, *, label: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        raise ContractViolation(f"{label} must be an absolute path")
    if not path.exists() or not path.is_dir():
        raise ContractViolation(f"{label} must be an existing directory")
    try:
        resolved = path.resolve(strict=True)
    except OSError as error:
        raise RuntimeError(f"cannot resolve {label}: {error}") from error
    return resolved


def is_within(candidate: Path, root: Path) -> bool:
    try:
        candidate.relative_to(root)
    except ValueError:
        return False
    return True


def init_artifact(repo_root_value: str) -> Path:
    repo_root = resolve_directory(repo_root_value, label="repo root")
    temp_directory: Path | None = None
    try:
        temp_directory = Path(tempfile.mkdtemp(prefix="km-plan-")).resolve()
        artifact = (temp_directory / "plan.md").resolve()
        if is_within(temp_directory, repo_root) or is_within(artifact, repo_root):
            raise ContractViolation("temporary artifact must be outside repository root")
        with artifact.open("xb") as stream:
            stream.write(INITIAL_CONTENT)
        return artifact
    except Exception:
        if temp_directory is not None:
            shutil.rmtree(temp_directory, ignore_errors=True)
        raise


def is_required_heading(line: str) -> bool:
    stripped = line.rstrip()
    hashes = len(stripped) - len(stripped.lstrip("#"))
    if not 1 <= hashes <= 6:
        return False
    remainder = stripped[hashes:]
    return bool(remainder) and remainder[0].isspace() and remainder.lstrip() == REQUIRED_HEADING


def validate_artifact(repo_root_value: str, artifact_value: str) -> Path:
    repo_root = resolve_directory(repo_root_value, label="repo root")
    artifact = Path(artifact_value)
    if not artifact.is_absolute():
        raise ContractViolation("artifact path must be absolute")
    if not artifact.exists() or not artifact.is_file():
        raise ContractViolation("artifact must be an existing regular file")
    try:
        resolved = artifact.resolve(strict=True)
    except OSError as error:
        raise RuntimeError(f"cannot resolve artifact: {error}") from error
    if is_within(resolved, repo_root):
        raise ContractViolation("artifact must be outside repository root")

    try:
        text = resolved.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise RuntimeError(f"cannot read artifact as UTF-8: {error}") from error
    if not text:
        raise ContractViolation("artifact must not be empty")
    lines = text.splitlines()
    if not lines or lines[0] != MARKER:
        raise ContractViolation("managed marker must be the exact first line")
    if text.count(MARKER) != 1:
        raise ContractViolation("managed marker must occur exactly once")
    if sum(is_required_heading(line) for line in lines) != 1:
        raise ContractViolation(f"ATX heading '{REQUIRED_HEADING}' must occur exactly once")
    return resolved


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description="Prepare and validate km-plan artifacts")
    commands = root.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init")
    init.add_argument("--repo-root", required=True)
    validate = commands.add_parser("validate")
    validate.add_argument("--repo-root", required=True)
    validate.add_argument("artifact")
    return root


def main() -> int:
    arguments = parser().parse_args()
    try:
        if arguments.command == "init":
            result = init_artifact(arguments.repo_root)
        else:
            result = validate_artifact(arguments.repo_root, arguments.artifact)
    except ContractViolation as error:
        print(f"plan-artifact: {error}", file=sys.stderr)
        return 3
    except (OSError, RuntimeError) as error:
        print(f"plan-artifact: {error}", file=sys.stderr)
        return 1
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
