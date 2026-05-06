#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEST_ROOT="$REPO_ROOT/tests/skills"

if [[ ! -d "$TEST_ROOT" ]]; then
  echo "missing: $TEST_ROOT" >&2
  exit 1
fi

python3 - "$TEST_ROOT" <<'PY'
from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    import yaml
except Exception as exc:  # pragma: no cover - env-dependent
    print(f"missing dependency: pyyaml ({exc})", file=sys.stderr)
    sys.exit(1)


root = Path(sys.argv[1])
repo_root = root.parent.parent
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


def load_text(path: Path) -> str | None:
    global checks, failures
    checks += 1
    try:
        return path.read_text()
    except Exception as exc:
        print(f"invalid text: {path} ({exc})")
        failures += 1
        return None


def parse_frontmatter(text: str, path: Path) -> tuple[dict, list[str]] | tuple[None, None]:
    lines = text.splitlines()
    if len(lines) < 3 or lines[0].strip() != "---":
        check(False, f"{path}: missing frontmatter start")
        return None, None
    try:
        end = lines[1:].index("---") + 1
    except ValueError:
        check(False, f"{path}: missing frontmatter end")
        return None, None
    data = yaml.safe_load("\n".join(lines[1:end])) or {}
    if not isinstance(data, dict):
        check(False, f"{path}: invalid frontmatter object")
        return None, None
    return data, lines[end + 1 :]


def find_section_bullets(text: str, heading: str) -> list[str]:
    lines = text.splitlines()
    try:
        start = lines.index(heading)
    except ValueError:
        return []
    bullets: list[str] = []
    for line in lines[start + 1 :]:
        if line.startswith("## "):
            break
        if line.startswith("- "):
            bullets.append(line[2:].strip())
            continue
        ordered_match = re.match(r"^\d+\.\s+(.+)$", line)
        if ordered_match:
            bullets.append(ordered_match.group(1).strip())
    return bullets


def extract_backtick_paths(text: str) -> list[str]:
    results: list[str] = []
    for token in re.findall(r"`([^`\n]+)`", text):
        cleaned = token.strip()
        if "/" not in cleaned and not cleaned.startswith("."):
            continue
        if not cleaned.endswith((".md", ".yaml", ".json", ".toml", ".sh")):
            continue
        if cleaned.startswith(("http://", "https://", "<", "$", "/", "git ", "gh ", "python3 ", "bash ")):
            continue
        if any(ch in cleaned for ch in (" ", "*", "<", ">", "(", ")", "|")):
            continue
        results.append(cleaned)
    return results


def resolve_supporting_path(skill_dir: Path, token: str) -> Path | None:
    candidate = (skill_dir / token).resolve()
    if candidate.exists():
        return candidate
    candidate = (repo_root / "templates" / "skills" / token).resolve()
    if candidate.exists():
        return candidate
    candidate = (repo_root / token).resolve()
    if candidate.exists():
        return candidate
    return None


def main() -> int:
    manifest_path = root / "manifest.yaml"
    skills_readme = root / "README.md"
    tests_readme = repo_root / "tests" / "README.md"
    docs_dir = repo_root / "tests" / "docs"
    strategy_doc = docs_dir / "skills-test-strategy.md"
    catalog_doc = docs_dir / "skills-test-catalog.md"
    runs_dir = root / "runs"
    rubrics_dir = root / "rubrics"
    scenarios_dir = root / "scenarios"
    template_path = runs_dir / "result-template.md"

    for path in (manifest_path, skills_readme, tests_readme, strategy_doc, catalog_doc, template_path):
        check(path.is_file(), f"missing: {path}")
    for path in (runs_dir, rubrics_dir, scenarios_dir, docs_dir):
        check(path.is_dir(), f"missing: {path}")

    manifest = load_yaml(manifest_path)
    if not isinstance(manifest, dict):
        return 1
    cases = manifest.get("cases")
    check(isinstance(cases, list) and len(cases) > 0, "manifest cases missing")
    if not isinstance(cases, list):
        return 1
    check(15 <= len(cases) <= 18, f"manifest should stay in canonical range (15-18 cases), got {len(cases)}")

    seen_case_ids: set[str] = set()
    case_ids: list[str] = []
    manifest_scenario_ids: set[str] = set()
    for case in cases:
        check(isinstance(case, dict), f"invalid case entry: {case!r}")
        if not isinstance(case, dict):
            continue
        case_id = case.get("id")
        file_rel = case.get("file")
        scenario_id = case.get("scenario_id")
        tags = case.get("tags")
        check(isinstance(case_id, str) and bool(case_id), f"invalid case id: {case!r}")
        check(isinstance(file_rel, str) and bool(file_rel), f"{case_id}: invalid file")
        check(isinstance(scenario_id, str) and bool(scenario_id), f"{case_id}: invalid scenario_id")
        check(isinstance(tags, list) and bool(tags), f"{case_id}: missing tags")
        if not isinstance(case_id, str) or not isinstance(file_rel, str) or not isinstance(scenario_id, str):
            continue
        check(case_id not in seen_case_ids, f"duplicate case id: {case_id}")
        seen_case_ids.add(case_id)
        case_ids.append(case_id)

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
        ids: list[str] = []
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
                check(f"{rel}:{sid}" in manifest_scenario_ids, f"orphan scenario: {sid} in {rel} not referenced by manifest")

    for rubric in ("routing.md", "output-quality.md"):
        check((rubrics_dir / rubric).is_file(), f"missing rubric: {rubrics_dir / rubric}")

    gitkeep = runs_dir / ".gitkeep"
    check(gitkeep.is_file(), f"missing: {gitkeep}")

    tests_readme_text = load_text(tests_readme) or ""
    for required in ("tests/docs/skills-test-strategy.md", "tests/docs/skills-test-catalog.md", "軽量な静的検証 + 必要時の手動 spot check"):
        check(required in tests_readme_text, f"tests/README.md missing: {required}")

    repo_readme = repo_root / "README.md"
    repo_readme_text = load_text(repo_readme) or ""
    for required in ("## Codex 設計メモ", "## スキル一覧", "`web_search = \"cached\"`", "`alternate_screen = \"never\"`"):
        check(required in repo_readme_text, f"README.md missing: {required}")

    skills_readme_text = load_text(skills_readme) or ""
    for required in ("manifest.yaml", "scenarios/", "rubrics/", "runs/", "canonical decision boundary"):
        check(required in skills_readme_text, f"tests/skills/README.md missing: {required}")

    strategy_text = load_text(strategy_doc) or ""
    for required in ("Tier 1: Static Contracts", "Tier 2: Canonical Decision Cases", "Tier 3: Human Guidance", "disable-model-invocation", "allow_implicit_invocation"):
        check(required in strategy_text, f"skills-test-strategy.md missing: {required}")

    catalog_text = load_text(catalog_doc) or ""
    for required in ("## Canonical Cases", "## Retired Cases", "## Canary Samples"):
        check(required in catalog_text, f"skills-test-catalog.md missing section: {required}")
    for case_id in case_ids:
        check(f"`{case_id}`" in catalog_text, f"skills-test-catalog.md missing canonical case: {case_id}")

    agents_md = repo_root / "templates" / "AGENTS.md"
    claude_md = repo_root / "templates" / "CLAUDE.md"
    if agents_md.is_file() and claude_md.is_file():
        agents_text = load_text(agents_md) or ""
        claude_text = load_text(claude_md) or ""
        check("Skill 運用" not in agents_text, "templates/AGENTS.md should not reintroduce Skill 運用 section")
        check("Skill 運用" not in claude_text, "templates/CLAUDE.md should not reintroduce Skill 運用 section")
        for heading in ("## 主要原則", "## ワークフロー", "## 運用ルールの参照"):
            agents_bullets = find_section_bullets(agents_text, heading)
            claude_bullets = find_section_bullets(claude_text, heading)
            check(bool(agents_bullets), f"templates/AGENTS.md missing bullets under {heading}")
            check(bool(claude_bullets), f"templates/CLAUDE.md missing bullets under {heading}")
            if agents_bullets and claude_bullets:
                normalized_agents = [b.replace("`AGENTS.md`", "`<agent-guideline>`") for b in agents_bullets]
                normalized_claude = [b.replace("`CLAUDE.md`", "`<agent-guideline>`") for b in claude_bullets]
                check(
                    normalized_agents == normalized_claude,
                    f"templates/AGENTS.md and templates/CLAUDE.md bullets must match under {heading}",
                )

    skills_root = repo_root / "templates" / "skills"
    manual_only_codex = {"code-review", "doc-review", "intent-review", "quality-review", "third-party-oss-security-review"}
    workflow_codex = {"commit", "github-workflow", "plan", "review"}
    manual_only_claude = {"code-review", "doc-review", "intent-review", "quality-review", "third-party-oss-security-review"}

    stable_contracts = {
        "review": {
            "success": [
                "変更タイプに応じた review 候補を正しく選ぶ",
                "`CRITICAL` / `HIGH`、または intent-review の `HIGH` を見逃さずにブロックする",
            ],
            "safety": None,
            "phrases": [],
        },
        "github-workflow": {
            "success": [
                "GitHub 管理リポジトリであることを確認してから進める",
                "PR 作成後は PR を実装成果物の正とし、issue の詳細同期を続けない",
            ],
            "safety": [
                "branch 作成 / push / PR 作成の要求が曖昧な場合は、workflow 開始前にユーザーへ確認する",
                "`--body \"...\"` や非クォート heredoc で issue / PR 本文を流し込まない",
            ],
            "phrases": [
                "issue / PR 本文は `--body-file - <<'EOF'` で流し込む",
            ],
        },
        "plan": {
            "success": [
                "Plan Mode 中は `.plan/`, `.gitignore`, GitHub issue を変更しない",
                "GitHub 管理 repo では新規 issue を作り、`.plan/` ファイルを `--body-file` に直接渡して全文ミラーする",
            ],
            "safety": [
                "明示のない限り既存 issue を探索・再利用しない。類似 issue の自動 search は行わない",
                "既存 issue を更新する場合でも、marker がなければ全文置換前にユーザーへ確認する",
            ],
            "phrases": [],
        },
    }

    for skill_dir in sorted(p for p in skills_root.iterdir() if p.is_dir()):
        skill_name = skill_dir.name
        skill_path = skill_dir / "SKILL.md"
        check(skill_path.is_file(), f"missing SKILL.md: {skill_path}")
        if not skill_path.is_file():
            continue
        text = load_text(skill_path)
        if text is None:
            continue
        frontmatter, body_lines = parse_frontmatter(text, skill_path)
        if frontmatter is None or body_lines is None:
            continue

        name = frontmatter.get("name")
        description = frontmatter.get("description")
        when_to_use = frontmatter.get("when_to_use", "")
        disable_model_invocation = frontmatter.get("disable-model-invocation")
        check(isinstance(name, str) and bool(name), f"{skill_path}: missing frontmatter name")
        check(isinstance(description, str) and bool(description), f"{skill_path}: missing frontmatter description")
        if isinstance(name, str):
            check(name.startswith("km:"), f"{skill_path}: frontmatter name should follow repo km: prefix convention")
            check(len(name) <= 64, f"{skill_path}: frontmatter name exceeds 64 chars")
            if ":" in name:
                suffix = name.split(":", 1)[1]
                check(bool(re.fullmatch(r"[a-z0-9-]+", suffix)), f"{skill_path}: frontmatter name suffix should be kebab-case")
        if isinstance(description, str):
            total_len = len(description) + (len(when_to_use) if isinstance(when_to_use, str) else 0)
            check(total_len <= 1536, f"{skill_path}: description + when_to_use exceeds 1536 chars")
        check(len(text.splitlines()) <= 500, f"{skill_path}: body exceeds 500 lines")

        if skill_name in manual_only_claude:
            check(disable_model_invocation is True, f"{skill_path}: disable-model-invocation must be true for manual-only skill")
        elif disable_model_invocation is not None:
            check(disable_model_invocation is not True, f"{skill_path}: workflow/default skill should not set disable-model-invocation true")

        referenced_paths = extract_backtick_paths(text)
        for token in referenced_paths:
            if token == "agents/openai.yaml":
                continue
            if resolve_supporting_path(skill_dir, token) is None:
                check(False, f"{skill_path}: referenced supporting path not found: {token}")

        success_bullets = find_section_bullets(text, "## Success Criteria")
        check(bool(success_bullets), f"{skill_path}: missing Success Criteria bullets")
        if skill_name in stable_contracts:
            for bullet in stable_contracts[skill_name]["success"]:
                check(bullet in success_bullets, f"{skill_path}: missing stable Success Criteria bullet: {bullet}")
            expected_safety = stable_contracts[skill_name]["safety"]
            if expected_safety is not None:
                safety_bullets = find_section_bullets(text, "## Safety Rules")
                check(bool(safety_bullets), f"{skill_path}: missing Safety Rules bullets")
                for bullet in expected_safety:
                    check(bullet in safety_bullets, f"{skill_path}: missing stable Safety Rules bullet: {bullet}")
            for phrase in stable_contracts[skill_name]["phrases"]:
                check(phrase in text, f"{skill_path}: missing stable contract phrase: {phrase}")

        oa_path = skill_dir / "agents" / "openai.yaml"
        if skill_name in manual_only_codex:
            check(oa_path.is_file(), f"missing agents/openai.yaml for manual-only skill: {skill_name}")
            if oa_path.is_file():
                oa_data = load_yaml(oa_path)
                if isinstance(oa_data, dict):
                    policy = oa_data.get("policy", {})
                    if isinstance(policy, dict):
                        check(policy.get("allow_implicit_invocation") is False, f"{skill_name}: allow_implicit_invocation must be false")
                    else:
                        check(False, f"{skill_name}: agents/openai.yaml missing policy section")
        elif skill_name in workflow_codex:
            check(not oa_path.exists(), f"workflow skill {skill_name} should not have agents/openai.yaml")

    if failures:
        print(f"verify failed: {failures} issue(s) across {checks} check(s)")
        return 1

    print(f"verify ok: {checks} check(s)")
    return 0


raise SystemExit(main())
PY

python3 "$REPO_ROOT/scripts/run-skill-tests.py" list >/dev/null
python3 "$REPO_ROOT/scripts/run-skill-tests.py" dry-run --tag trigger >/dev/null
python3 "$REPO_ROOT/scripts/run-skill-tests.py" scaffold --label verify --client Codex --model static >/dev/null
