#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEST_ROOT="$REPO_ROOT/tests/skills"
TMP_LABEL="verify-$$"
TMP_RUN="$TEST_ROOT/runs/$(date +%F)-$TMP_LABEL.md"

cleanup() {
  rm -f "$TMP_RUN"
}

trap cleanup EXIT

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
repo_root = root.parent.parent


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


def check_contains(text: str, needle: str, message: str) -> None:
    check(needle in text, message)


def extract_skill_operation_bullets(path: Path) -> list[str] | None:
    text = path.read_text().splitlines()
    start = None
    for heading in ("## Skill 運用", "### Skill 運用"):
        try:
            start = text.index(heading)
            break
        except ValueError:
            continue
    if start is None:
        return None

    bullets: list[str] = []
    for line in text[start + 1 :]:
        stripped = line.strip()
        if stripped.startswith("## "):
            break
        if not stripped:
            continue
        if "意図的に同一内容" in stripped:
            continue
        if stripped.startswith("- "):
            bullets.append(stripped)
    return bullets


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

    repo_readme = repo_root / "README.md"
    agents_md = repo_root / "templates" / "AGENTS.md"
    claude_md = repo_root / "templates" / "CLAUDE.md"
    review_skill = repo_root / "templates" / "skills" / "review" / "SKILL.md"

    if repo_readme.is_file():
        readme_text = repo_readme.read_text()
        check("### 推奨 profile" not in readme_text, "README should not define recommended profiles")
        check("既定のレビュー入口" not in readme_text, "README skill list should not define invocation policy")
        check("明示起動のみ" not in readme_text, "README skill list should not define manual-only policy")
        check_contains(readme_text, "## Codex 設計メモ", "README missing Codex design notes section")
        check_contains(readme_text, "`web_search = \"cached\"`", "README missing config rationale for cached web_search")
        check_contains(readme_text, "`alternate_screen = \"never\"`", "README missing config rationale for alternate_screen")

    if agents_md.is_file() and claude_md.is_file():
        agents_bullets = extract_skill_operation_bullets(agents_md)
        claude_bullets = extract_skill_operation_bullets(claude_md)
        check(agents_bullets is not None, "templates/AGENTS.md missing Skill 運用 section")
        check(claude_bullets is not None, "templates/CLAUDE.md missing Skill 運用 section")
        if agents_bullets is not None and claude_bullets is not None:
            check(agents_bullets == claude_bullets, "templates/AGENTS.md and templates/CLAUDE.md Skill 運用 bullets must match")

    if review_skill.is_file():
        review_lines = review_skill.read_text().splitlines()
        persona_count = 0
        in_persona_section = False
        for line in review_lines:
            if line.strip() == "### 専門家の構成":
                in_persona_section = True
                continue
            if in_persona_section and line.startswith("### "):
                break
            if in_persona_section and (line.startswith("1. **") or line.startswith("2. **")):
                persona_count += 1
        check(persona_count == 2, f"review skill should define exactly 2 expert personas, got {persona_count}")
        reviewer_dir = review_skill.parent / "reviewers"
        check(not reviewer_dir.exists(), "review reviewer directory should not exist")

    # --- orphan scenario detection ---
    manifest_scenario_ids: set[str] = set()
    for case in cases:
        file_rel = case.get("file")
        scenario_id = case.get("scenario_id")
        if isinstance(file_rel, str) and isinstance(scenario_id, str):
            manifest_scenario_ids.add(f"{file_rel}:{scenario_id}")

    for scenario_file in scenarios_dir.glob("*.yaml"):
        data = load_yaml(scenario_file)
        if not isinstance(data, dict):
            continue
        scenarios = data.get("scenarios")
        if not isinstance(scenarios, list):
            continue
        rel = f"scenarios/{scenario_file.name}"
        for scenario in scenarios:
            if not isinstance(scenario, dict):
                continue
            sid = scenario.get("id")
            if isinstance(sid, str):
                key = f"{rel}:{sid}"
                check(key in manifest_scenario_ids, f"orphan scenario: {sid} in {rel} not referenced by manifest")

    # --- agents/openai.yaml contract ---
    skills_root = root.parent.parent / "templates" / "skills"
    if skills_root.is_dir():
        # Manual-only skills MUST have agents/openai.yaml with allow_implicit_invocation: false
        manual_only = ["code-review", "quality-review", "intent-review", "doc-review"]
        for skill_name in manual_only:
            oa_path = skills_root / skill_name / "agents" / "openai.yaml"
            check(oa_path.is_file(), f"missing agents/openai.yaml for manual-only skill: {skill_name}")
            if oa_path.is_file():
                oa_data = load_yaml(oa_path)
                if isinstance(oa_data, dict):
                    policy = oa_data.get("policy", {})
                    if isinstance(policy, dict):
                        check(
                            policy.get("allow_implicit_invocation") is False,
                            f"{skill_name}: allow_implicit_invocation must be false",
                        )
                    else:
                        check(False, f"{skill_name}: agents/openai.yaml missing policy section")

        # Workflow skills MUST NOT have agents/openai.yaml (auto-invocable)
        workflow_skills = ["commit", "github-workflow", "review"]
        for skill_name in workflow_skills:
            oa_path = skills_root / skill_name / "agents" / "openai.yaml"
            check(
                not oa_path.exists(),
                f"workflow skill {skill_name} should not have agents/openai.yaml (must stay auto-invocable)",
            )

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
