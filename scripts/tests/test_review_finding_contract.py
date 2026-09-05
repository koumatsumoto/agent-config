from __future__ import annotations

import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
REVIEW_ROOT = REPO_ROOT / "templates/skills/km-review"


class ReviewFindingContractTests(unittest.TestCase):
    def test_main_and_dispatch_load_the_shared_contract(self) -> None:
        skill = (REVIEW_ROOT / "SKILL.md").read_text(encoding="utf-8")
        verdict = (REVIEW_ROOT / "references/verdict.md").read_text(encoding="utf-8")
        dispatch = (REVIEW_ROOT / "references/dispatch.md").read_text(encoding="utf-8")
        reviewer = (REVIEW_ROOT / "reviewers/contract.md").read_text(encoding="utf-8")
        for text in (skill, verdict, dispatch, reviewer):
            self.assertIn("references/finding-contract.md", text)


if __name__ == "__main__":
    unittest.main()
