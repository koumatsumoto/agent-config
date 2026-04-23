#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

try:
    import yaml
except Exception as exc:  # pragma: no cover - env dependent
    print(f"missing dependency: pyyaml ({exc})", file=sys.stderr)
    raise SystemExit(1)


REPO_ROOT = Path(__file__).resolve().parent.parent
TEST_ROOT = REPO_ROOT / "tests" / "skills"
MANIFEST_PATH = TEST_ROOT / "manifest.yaml"
RUNS_DIR = TEST_ROOT / "runs"


def load_yaml(path: Path) -> object:
    return yaml.safe_load(path.read_text())


def load_cases() -> list[dict]:
    manifest = load_yaml(MANIFEST_PATH)
    if not isinstance(manifest, dict) or not isinstance(manifest.get("cases"), list):
        raise SystemExit(f"invalid manifest: {MANIFEST_PATH}")

    cases: list[dict] = []
    for case in manifest["cases"]:
        if not isinstance(case, dict):
            raise SystemExit(f"invalid case entry in manifest: {case!r}")
        scenario_file = TEST_ROOT / case["file"]
        data = load_yaml(scenario_file)
        if not isinstance(data, dict) or not isinstance(data.get("scenarios"), list):
            raise SystemExit(f"invalid scenario file: {scenario_file}")

        found = next((s for s in data["scenarios"] if s.get("id") == case["scenario_id"]), None)
        if found is None:
            raise SystemExit(f"missing scenario id {case['scenario_id']} in {scenario_file}")

        cases.append(
            {
                "id": case["id"],
                "file": case["file"],
                "scenario_id": case["scenario_id"],
                "tags": case.get("tags", []),
                "title": found.get("title", case["scenario_id"]),
                "prompt": found.get("prompt", ""),
                "expected": found.get("expected", {}),
            }
        )
    return cases


def filter_cases(cases: list[dict], selected_ids: list[str], tags: list[str]) -> list[dict]:
    result = cases
    if selected_ids:
        selected = set(selected_ids)
        result = [case for case in result if case["id"] in selected or case["scenario_id"] in selected]
    if tags:
        required = set(tags)
        result = [case for case in result if required.intersection(case.get("tags", []))]
    return result


def print_list(cases: list[dict]) -> int:
    for case in cases:
        tags = ",".join(case.get("tags", []))
        print(f"{case['id']}\t{case['title']}\t[{tags}]")
    print(f"\n{len(cases)} case(s)")
    return 0


def print_dry_run(cases: list[dict]) -> int:
    print(f"dry-run: {len(cases)} case(s)")
    for idx, case in enumerate(cases, start=1):
        expected = case.get("expected", {})
        print(f"\n[{idx}] {case['id']}: {case['title']}")
        print(f"  prompt: {case['prompt']}")
        if expected.get("primary_skill"):
            print(f"  expected primary skill: {expected['primary_skill']}")
        if expected.get("child_skills"):
            print(f"  expected child skills: {', '.join(expected['child_skills'])}")
        if expected.get("required_behavior"):
            print(f"  required behavior: {', '.join(expected['required_behavior'])}")
        if expected.get("should_not_trigger"):
            print(f"  should not trigger: {', '.join(expected['should_not_trigger'])}")
        tags = ", ".join(case.get("tags", []))
        if tags:
            print(f"  tags: {tags}")
    return 0


def scaffold_run(cases: list[dict], label: str, client: str, model: str, branch: str) -> Path:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d")
    filename = RUNS_DIR / f"{stamp}-{label}.md"

    lines: list[str] = [
        "# Skills Test Run",
        "",
        f"- Date: {datetime.now().isoformat(timespec='minutes')}",
        "- Tester:",
        f"- Client: {client}",
        f"- Model / Profile: {model or ''}",
        f"- Branch / Commit: {branch or ''}",
        "- Suite: `tests/skills/manifest.yaml`",
        "",
        "## Results",
        "",
    ]

    for case in cases:
        lines.extend(
            [
                f"### `{case['id']}`",
                f"- Scenario ID: {case['scenario_id']}",
                f"- Title: {case['title']}",
                f"- Prompt: {case['prompt']}",
                f"- Expected: {case.get('expected', {})}",
                "- Actual:",
                "- Notes:",
                "",
            ]
        )

    filename.write_text("\n".join(lines))
    return filename


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="List or scaffold canonical skills test cases.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    base = argparse.ArgumentParser(add_help=False)
    base.add_argument("--id", action="append", default=[], help="Select case id or scenario id")
    base.add_argument("--tag", action="append", default=[], help="Filter by tag")

    subparsers.add_parser("list", parents=[base], help="List canonical cases")
    subparsers.add_parser("dry-run", parents=[base], help="Print selected cases with expectations")

    scaffold = subparsers.add_parser("scaffold", parents=[base], help="Create a run sheet for manual spot checks")
    scaffold.add_argument("--label", required=True, help="Run label")
    scaffold.add_argument("--client", default="", help="Client name")
    scaffold.add_argument("--model", default="", help="Model or profile")
    scaffold.add_argument("--branch", default="", help="Branch or commit")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    cases = filter_cases(load_cases(), args.id, args.tag)
    if not cases:
        print("no cases selected", file=sys.stderr)
        return 1

    if args.command == "list":
        return print_list(cases)
    if args.command == "dry-run":
        return print_dry_run(cases)
    if args.command == "scaffold":
        run_file = scaffold_run(cases, args.label, args.client, args.model, args.branch)
        print(run_file)
        return 0
    raise SystemExit(f"unsupported command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
