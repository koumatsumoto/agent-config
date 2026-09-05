from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS = REPO_ROOT / "templates/skills"


class SkillHelperContractTests(unittest.TestCase):
    @staticmethod
    def _section(text: str, heading: str, next_heading: str) -> str:
        return text.split(heading, 1)[1].split(next_heading, 1)[0]

    def test_html_generation_success_does_not_depend_on_opening(self) -> None:
        text = (SKILLS / "km-html-document/SKILL.md").read_text(encoding="utf-8")
        workflow = self._section(text, "## Workflow", "## Success Criteria")
        success = self._section(text, "## Success Criteria", "## Safety Rules")
        self.assertIn("$km-open-file", workflow)
        self.assertNotIn("km-open-file", success)

    def test_open_file_keeps_trust_decisions_outside_helper(self) -> None:
        skill = (SKILLS / "km-open-file/SKILL.md").read_text(encoding="utf-8")
        success = self._section(skill, "## Success Criteria", "## Workflow")
        workflow = self._section(skill, "## Workflow", "## Safety Rules")
        safety = skill.split("## Safety Rules", 1)[1]
        self.assertIn("起動要求", success)
        self.assertIn('bash "<skill-directory>/scripts/open-file.sh" "<path>"', workflow)
        self.assertIn("HTML", safety)
        self.assertIn("helper", safety)
        self.assertNotIn("case \"$(uname", skill)

    def test_worktree_helper_has_deterministic_invocation_contract(self) -> None:
        skill = (SKILLS / "km-github-workflow/SKILL.md").read_text(encoding="utf-8")
        setup = self._section(skill, "### Setup", "### Implement")
        self.assertLess(setup.index("`python3`"), setup.index("`python`"))
        self.assertIn("sys.version_info >= (3, 9)", setup)
        self.assertIn(
            '"<python>" "<skill-directory>/scripts/prepare-worktree.py" '
            '"<source-root>" "<destination-root>"',
            setup,
        )


if __name__ == "__main__":
    unittest.main()
