from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


class DocumentationContractTests(unittest.TestCase):
    def test_readme_skill_inventory_matches_templates(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        documented = set(re.findall(r"^\| `(km-[a-z-]+)` \|", readme, re.MULTILINE))
        actual = {p.parent.name for p in (REPO_ROOT / "templates/skills").glob("*/SKILL.md")}
        self.assertEqual(actual, documented)

    def test_local_markdown_links_resolve(self) -> None:
        paths = [REPO_ROOT / "README.md", REPO_ROOT / "scripts/tests/README.md"]
        for path in paths:
            for target in re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
                if "://" in target or target.startswith("#"):
                    continue
                with self.subTest(path=path.relative_to(REPO_ROOT), target=target):
                    self.assertTrue((path.parent / target.split("#", 1)[0]).exists())


if __name__ == "__main__":
    unittest.main()
