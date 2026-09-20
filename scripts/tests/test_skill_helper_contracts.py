from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS = REPO_ROOT / "templates/skills"


class SkillHelperContractTests(unittest.TestCase):
    def test_plan_artifact_helper_invocation_contract(self) -> None:
        skill = (SKILLS / "km-plan/SKILL.md").read_text(encoding="utf-8")
        self.assertIn(
            'bash "<skill-directory>/scripts/run-python.sh" '
            '"<skill-directory>/scripts/plan-artifact.py" init '
            '--repo-root "<absolute-repository-root>"',
            skill,
        )
        self.assertIn(
            'bash "<skill-directory>/scripts/run-python.sh" '
            '"<skill-directory>/scripts/plan-artifact.py" validate '
            '--repo-root "<absolute-repository-root>" "<absolute-plan-file>"',
            skill,
        )
        self.assertTrue((SKILLS / "km-plan/scripts/plan-artifact.py").is_file())
        self.assertTrue((SKILLS / "km-plan/scripts/run-python.sh").is_file())

    def test_open_file_helper_invocation_contract(self) -> None:
        skill = (SKILLS / "km-open-file/SKILL.md").read_text(encoding="utf-8")
        self.assertIn('bash "<skill-directory>/scripts/open-file.sh" "<path>"', skill)
        self.assertTrue((SKILLS / "km-open-file/scripts/open-file.sh").is_file())

    def test_worktree_helper_invocation_contract(self) -> None:
        skill = (SKILLS / "km-github-workflow/SKILL.md").read_text(encoding="utf-8")
        self.assertIn(
            'bash "<skill-directory>/scripts/run-python.sh" '
            '"<skill-directory>/scripts/prepare-worktree.py" '
            '"<source-root>" "<destination-root>" --branch "<branch>"',
            skill,
        )
        self.assertIn(
            '`<type>/<issue番号>-<slug>`（issueなしなら`<type>/<slug>`）', skill
        )
        self.assertTrue((SKILLS / "km-github-workflow/scripts/run-python.sh").is_file())
        self.assertTrue((SKILLS / "km-github-workflow/scripts/prepare-worktree.py").is_file())
        self.assertIn(
            'bash "<skill-directory>/scripts/run-python.sh" '
            '"<skill-directory>/scripts/cleanup-worktree.py" '
            '"<source-root>" "<destination-root>" --branch "<branch>"',
            skill,
        )
        self.assertTrue((SKILLS / "km-github-workflow/scripts/cleanup-worktree.py").is_file())


if __name__ == "__main__":
    unittest.main()
