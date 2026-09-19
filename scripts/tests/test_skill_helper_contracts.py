from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS = REPO_ROOT / "templates/skills"


class SkillHelperContractTests(unittest.TestCase):
    def test_open_file_helper_invocation_contract(self) -> None:
        skill = (SKILLS / "km-open-file/SKILL.md").read_text(encoding="utf-8")
        self.assertIn('bash "<skill-directory>/scripts/open-file.sh" "<path>"', skill)
        self.assertTrue((SKILLS / "km-open-file/scripts/open-file.sh").is_file())

    def test_worktree_helper_has_deterministic_invocation_contract(self) -> None:
        skill = (SKILLS / "km-github-workflow/SKILL.md").read_text(encoding="utf-8")
        self.assertLess(skill.index("`python3`"), skill.index("`python`"))
        self.assertIn("sys.version_info >= (3, 9)", skill)
        self.assertIn(
            '"<python>" "<skill-directory>/scripts/prepare-worktree.py" '
            '"<source-root>" "<destination-root>"',
            skill,
        )
        self.assertTrue((SKILLS / "km-github-workflow/scripts/prepare-worktree.py").is_file())


if __name__ == "__main__":
    unittest.main()
