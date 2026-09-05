from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS = REPO_ROOT / "templates/skills"


class SkillHelperContractTests(unittest.TestCase):
    def test_html_generation_success_does_not_depend_on_opening(self) -> None:
        text = (SKILLS / "km-html-document/SKILL.md").read_text(encoding="utf-8")
        success = text.split("## Success Criteria", 1)[1].split("## Safety Rules", 1)[0]
        self.assertNotIn("km-open-file", success)
        self.assertIn("best-effort", text)
        self.assertIn("表示できなくても生成成功は取り消さず", text)

    def test_open_file_keeps_trust_decisions_outside_helper(self) -> None:
        skill = (SKILLS / "km-open-file/SKILL.md").read_text(encoding="utf-8")
        helper = (SKILLS / "km-open-file/scripts/open-file.sh").read_text(encoding="utf-8")
        self.assertIn("ユーザーが明示したHTML", skill)
        self.assertIn("HTMLの信頼判断とユーザー意図の確認をhelperへ委ねない", skill)
        self.assertNotIn("ユーザーが明示したHTML", helper)
        self.assertNotIn("case \"$(uname", skill)

    def test_worktree_copy_algorithm_is_only_in_helper(self) -> None:
        skill = (SKILLS / "km-github-workflow/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("scripts/prepare-worktree.py", skill)
        self.assertIn("失敗した場合はそのworktreeで作業を始めず停止", skill)
        self.assertNotIn("シンボリックリンク", skill)
        self.assertNotIn("同じ相対パスへコピー", skill)


if __name__ == "__main__":
    unittest.main()
