#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
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
ALLOWED_CATEGORIES = {
    "passed",
    "trigger_failure",
    "routing_failure",
    "quality_failure",
    "workflow_failure",
    "doc_drift",
}
TEMPLATE_CATEGORY = "passed | trigger_failure | routing_failure | quality_failure | workflow_failure | doc_drift"


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
        found = None
        for scenario in data["scenarios"]:
            if scenario.get("id") == case["scenario_id"]:
                found = scenario
                break
        if found is None:
            raise SystemExit(f"missing scenario id {case['scenario_id']} in {scenario_file}")
        merged = {
            "id": case["id"],
            "file": case["file"],
            "scenario_id": case["scenario_id"],
            "tags": case.get("tags", []),
            "title": found.get("title", case["scenario_id"]),
            "prompt": found.get("prompt", ""),
            "context": found.get("context", {}),
            "expected": found.get("expected", {}),
        }
        cases.append(merged)
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
        print(f"\n[{idx}] {case['id']}: {case['title']}")
        print(f"  prompt: {case['prompt']}")
        primary = case.get("expected", {}).get("primary_skill", "(none)")
        print(f"  expected primary skill: {primary}")
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
        "## Summary",
        "",
        f"- Total cases: {len(cases)}",
        "- Passed:",
        "- Failed:",
        "- Notes:",
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
                f"- Category: `passed | trigger_failure | routing_failure | quality_failure | workflow_failure | doc_drift`",
                f"- Prompt: {case['prompt']}",
                f"- Expected Primary Skill: {case.get('expected', {}).get('primary_skill', '')}",
                "- Actual:",
                "- Pass/Fail:",
                "- Notes:",
                "",
            ]
        )

    lines.extend(
        [
            "## Follow-ups",
            "",
            "- Blocking issues:",
            "- Non-blocking issues:",
            "- Suggested fixes:",
            "",
        ]
    )

    filename.write_text("\n".join(lines))
    return filename


def parse_run_file(path: Path) -> list[dict]:
    lines = path.read_text().splitlines()
    sections: list[dict] = []
    current: dict | None = None
    heading = re.compile(r"^### `(.+)`$")
    bullet = re.compile(r"^- ([^:]+):\s*(.*)$")

    for line in lines:
        match = heading.match(line)
        if match:
            if current is not None:
                sections.append(current)
            current = {"id": match.group(1)}
            continue
        if current is None:
            continue
        match = bullet.match(line)
        if match:
            current[match.group(1).strip()] = match.group(2).strip()

    if current is not None:
        sections.append(current)
    return sections


def display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def summarize_run(path: Path, selected_cases: list[dict]) -> int:
    sections = parse_run_file(path)
    selected_ids = {case["id"] for case in selected_cases}
    filtered = [section for section in sections if section.get("id") in selected_ids]
    if not filtered:
        print("no matching sections in run file", file=sys.stderr)
        return 1

    counts = {category: 0 for category in sorted(ALLOWED_CATEGORIES)}
    incomplete: set[str] = set()
    unknown_categories: list[str] = []
    seen_ids: set[str] = set()
    duplicate_ids: list[str] = []

    for section in filtered:
        case_id = section["id"]
        if case_id in seen_ids:
            duplicate_ids.append(case_id)
            continue
        seen_ids.add(case_id)
        category = section.get("Category", "").strip("` ")
        actual = section.get("Actual", "")
        verdict = section.get("Pass/Fail", "")

        if not actual or not verdict:
            incomplete.add(case_id)
        if category == TEMPLATE_CATEGORY:
            incomplete.add(case_id)
            continue
        if category:
            if category not in ALLOWED_CATEGORIES:
                unknown_categories.append(f"{case_id}:{category}")
            else:
                counts[category] += 1

    print(f"run file: {display_path(path)}")
    print(f"matched cases: {len(filtered)}")
    print("category counts:")
    for category, count in counts.items():
        print(f"  {category}: {count}")
    if incomplete:
        print("incomplete cases:")
        for case_id in sorted(incomplete):
            print(f"  {case_id}")
    if unknown_categories:
        print("unknown categories:")
        for item in unknown_categories:
            print(f"  {item}")
    if duplicate_ids:
        print("duplicate case sections:")
        for case_id in sorted(set(duplicate_ids)):
            print(f"  {case_id}")

    return 0 if not unknown_categories and not duplicate_ids else 1


def validate_run(path: Path, selected_cases: list[dict]) -> int:
    sections = parse_run_file(path)
    by_id: dict[str, dict] = {}
    failures: list[str] = []
    valid_ids = {case["id"] for case in selected_cases}

    for section in sections:
        section_id = section.get("id")
        if not section_id:
            continue
        if section_id in by_id:
            failures.append(f"duplicate case section: {section_id}")
            continue
        by_id[section_id] = section

    for case in selected_cases:
        section = by_id.get(case["id"])
        if section is None:
            failures.append(f"missing case section: {case['id']}")
            continue

        category = section.get("Category", "").strip("` ")
        if category == TEMPLATE_CATEGORY:
            failures.append(f"{case['id']}: Category still has template placeholder")
        elif category not in ALLOWED_CATEGORIES:
            failures.append(f"{case['id']}: invalid category {category!r}")
        if not section.get("Actual", "").strip():
            failures.append(f"{case['id']}: Actual is empty")
        if section.get("Pass/Fail", "").strip() not in {"Pass", "Fail"}:
            failures.append(f"{case['id']}: Pass/Fail must be Pass or Fail")

        scenario_id = section.get("Scenario ID", "").strip()
        if scenario_id and scenario_id != case["scenario_id"]:
            failures.append(
                f"{case['id']}: Scenario ID mismatch (expected {case['scenario_id']!r}, got {scenario_id!r})"
            )

    extra_sections = sorted(set(by_id) - valid_ids)
    for section_id in extra_sections:
        failures.append(f"unexpected case section: {section_id}")

    if failures:
        for failure in failures:
            print(failure)
        print(f"run validation failed: {len(failures)} issue(s)")
        return 1

    print(f"run validation ok: {len(selected_cases)} case(s)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run or scaffold skills test scenarios.")
    parser.add_argument("command", choices=["list", "dry-run", "scaffold", "summary", "validate-run"])
    parser.add_argument("--case", action="append", default=[], dest="cases", help="Case id or scenario id to include")
    parser.add_argument("--tag", action="append", default=[], dest="tags", help="Filter by tag")
    parser.add_argument("--label", default="manual", help="Output label for scaffold")
    parser.add_argument("--client", default="Codex", help="Client name for scaffold output")
    parser.add_argument("--model", default="", help="Model/profile for scaffold output")
    parser.add_argument("--branch", default="", help="Branch/commit text for scaffold output")
    parser.add_argument("--run-file", default="", help="Run sheet to summarize or validate")
    args = parser.parse_args()

    cases = filter_cases(load_cases(), args.cases, args.tags)
    if not cases:
        print("no cases selected", file=sys.stderr)
        return 1

    if args.command == "list":
        return print_list(cases)
    if args.command == "dry-run":
        return print_dry_run(cases)
    if args.command == "scaffold":
        path = scaffold_run(cases, args.label, args.client, args.model, args.branch)
        print(path.relative_to(REPO_ROOT))
        return 0
    if args.command in {"summary", "validate-run"}:
        if not args.run_file:
            print("--run-file is required", file=sys.stderr)
            return 1
        run_path = Path(args.run_file)
        if not run_path.is_absolute():
            run_path = REPO_ROOT / run_path
        if not run_path.is_file():
            print(f"missing run file: {run_path}", file=sys.stderr)
            return 1
        if args.command == "summary":
            return summarize_run(run_path, cases)
        return validate_run(run_path, cases)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
