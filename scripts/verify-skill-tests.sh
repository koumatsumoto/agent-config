#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEST_ROOT="$REPO_ROOT/tests/skills"
TMP_LABEL="verify-$$"
TMP_RUN="$TEST_ROOT/runs/$(date +%F)-$TMP_LABEL.md"

if [[ ! -d "$TEST_ROOT" ]]; then
  echo "missing: $TEST_ROOT" >&2
  exit 1
fi

python3 - "$TEST_ROOT" <<'PY'
from __future__ import annotations

import sys
from pathlib import Path

try:
    import yaml
except Exception as exc:  # pragma: no cover - env-dependent
    print(f"missing dependency: pyyaml ({exc})", file=sys.stderr)
    sys.exit(1)


root = Path(sys.argv[1])
failures = 0
checks = 0


def check(condition: bool, message: str) -> None:
    global checks, failures
    checks += 1
    if not condition:
        print(message)
        failures += 1


def load_yaml(path: Path) -> object:
    global checks, failures
    checks += 1
    try:
        return yaml.safe_load(path.read_text())
    except Exception as exc:
        print(f"invalid yaml: {path} ({exc})")
        failures += 1
        return None


def main() -> int:
    manifest_path = root / "manifest.yaml"
    readme_path = root / "README.md"
    runs_dir = root / "runs"
    rubrics_dir = root / "rubrics"
    scenarios_dir = root / "scenarios"
    template_path = runs_dir / "result-template.md"

    check(manifest_path.is_file(), f"missing: {manifest_path}")
    check(readme_path.is_file(), f"missing: {readme_path}")
    check(runs_dir.is_dir(), f"missing: {runs_dir}")
    check(rubrics_dir.is_dir(), f"missing: {rubrics_dir}")
    check(scenarios_dir.is_dir(), f"missing: {scenarios_dir}")
    check(template_path.is_file(), f"missing: {template_path}")

    if not manifest_path.is_file():
        return 1

    manifest = load_yaml(manifest_path)
    if not isinstance(manifest, dict):
        return 1

    cases = manifest.get("cases")
    check(isinstance(cases, list) and len(cases) > 0, "manifest cases missing")
    if not isinstance(cases, list):
        return 1

    seen_case_ids: set[str] = set()
    for case in cases:
        check(isinstance(case, dict), f"invalid case entry: {case!r}")
        if not isinstance(case, dict):
            continue

        case_id = case.get("id")
        check(isinstance(case_id, str) and bool(case_id), f"invalid case id: {case!r}")
        if isinstance(case_id, str):
            check(case_id not in seen_case_ids, f"duplicate case id: {case_id}")
            seen_case_ids.add(case_id)

        file_rel = case.get("file")
        scenario_id = case.get("scenario_id")
        check(isinstance(file_rel, str) and bool(file_rel), f"{case_id}: invalid file")
        check(isinstance(scenario_id, str) and bool(scenario_id), f"{case_id}: invalid scenario_id")
        if not isinstance(file_rel, str) or not isinstance(scenario_id, str):
            continue

        scenario_file = root / file_rel
        check(scenario_file.is_file(), f"missing file: {scenario_file}")
        if not scenario_file.is_file():
            continue

        data = load_yaml(scenario_file)
        if not isinstance(data, dict):
            continue
        scenarios = data.get("scenarios")
        check(isinstance(scenarios, list) and len(scenarios) > 0, f"{scenario_file}: scenarios missing")
        if not isinstance(scenarios, list):
            continue

        ids = []
        for scenario in scenarios:
            check(isinstance(scenario, dict), f"{scenario_file}: invalid scenario entry")
            if not isinstance(scenario, dict):
                continue
            sid = scenario.get("id")
            check(isinstance(sid, str) and bool(sid), f"{scenario_file}: scenario id missing")
            if isinstance(sid, str):
                ids.append(sid)

        check(len(ids) == len(set(ids)), f"{scenario_file}: duplicate scenario ids")
        check(scenario_id in ids, f"missing scenario id {scenario_id} in {scenario_file}")

    readme = readme_path.read_text() if readme_path.is_file() else ""
    for required in ("manifest.yaml", "scenarios/", "rubrics/", "runs/"):
        check(required in readme, f"README missing entry: {required}")

    for rubric in ("routing.md", "output-quality.md"):
        check((rubrics_dir / rubric).is_file(), f"missing rubric: {rubrics_dir / rubric}")

    gitkeep = runs_dir / ".gitkeep"
    check(gitkeep.is_file(), f"missing: {gitkeep}")

    if failures:
        print(f"verify failed: {failures} issue(s) across {checks} check(s)")
        return 1

    print(f"verify ok: {checks} check(s)")
    return 0


raise SystemExit(main())
PY

python3 "$REPO_ROOT/scripts/run-skill-tests.py" list >/dev/null
python3 "$REPO_ROOT/scripts/run-skill-tests.py" dry-run --tag review >/dev/null
python3 "$REPO_ROOT/scripts/run-skill-tests.py" scaffold --label "$TMP_LABEL" --client Codex --model verify >/dev/null
python3 "$REPO_ROOT/scripts/run-skill-tests.py" summary --run-file "$TMP_RUN" >/dev/null
python3 - "$TMP_RUN" <<'PY'
from pathlib import Path
import re
import sys

path = Path(sys.argv[1])
text = path.read_text()
text = re.sub(
    r"- Category: `passed \| trigger_failure \| routing_failure \| quality_failure \| workflow_failure \| doc_drift`\n- Prompt:",
    "- Category: `passed`\n- Prompt:",
    text,
)
text = text.replace("- Actual:\n", "- Actual: matched expected behavior\n")
text = text.replace("- Pass/Fail:\n", "- Pass/Fail: Pass\n")
path.write_text(text)
PY
python3 "$REPO_ROOT/scripts/run-skill-tests.py" validate-run --run-file "$TMP_RUN" >/dev/null
rm -f "$TMP_RUN"
