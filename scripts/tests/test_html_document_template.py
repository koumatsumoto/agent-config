"""Guards the security invariants of the km:html-document HTML template.

The template ships a strict CSP, an SRI-pinned Mermaid load, and an inline init
script whose sha256 is baked into the CSP. These tests fail fast when a required
token is dropped, when the inline init is edited without recomputing its hash, or
when a Mermaid version bump leaves the CSP script-src path out of sync with the
<script src> URL. Verifying that the SRI sha384 matches the CDN bytes needs the
network and is out of scope here, so a version bump still requires a manual SRI
recompute.

Run with the scripts/ dir as the top-level import root:
    python3 -m unittest discover -s scripts/tests -t scripts
"""

from __future__ import annotations

import base64
import hashlib
import re
import unittest
from pathlib import Path

TEMPLATE = (
    Path(__file__).resolve().parents[2]
    / "templates"
    / "skills"
    / "html-document"
    / "references"
    / "document-template.html"
)


class HtmlDocumentTemplateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.html = TEMPLATE.read_text(encoding="utf-8")

    def test_template_exists(self) -> None:
        self.assertTrue(TEMPLATE.is_file(), f"missing template: {TEMPLATE}")

    def test_security_tokens_present(self) -> None:
        required = [
            "http-equiv=\"Content-Security-Policy\"",
            "default-src 'none'",
            'name="referrer" content="no-referrer"',
            "integrity=\"sha384-",
            'crossorigin="anonymous"',
            "securityLevel:'strict'",
            "--content-width: 1400px",
        ]
        for token in required:
            self.assertIn(token, self.html, f"template missing required token: {token}")

    def test_mermaid_is_version_pinned(self) -> None:
        # SRI only protects a pinned URL; an unpinned @latest would defeat it.
        self.assertRegex(
            self.html,
            r"cdn\.jsdelivr\.net/npm/mermaid@\d+\.\d+\.\d+/dist/mermaid\.min\.js",
            "Mermaid must be loaded from a version-pinned UMD path",
        )

    def test_csp_version_matches_script_src(self) -> None:
        # A version bump must update the <script src> URL and the CSP script-src
        # path together; otherwise the browser blocks the new script. Scope the
        # check to the CSP content so the <script src> line can't satisfy it.
        src = re.search(
            r'<script src="https://cdn\.jsdelivr\.net/npm/mermaid@(\d+\.\d+\.\d+)/dist/mermaid\.min\.js"',
            self.html,
        )
        self.assertIsNotNone(src, "version-pinned Mermaid <script src> not found")
        version = src.group(1)
        csp = re.search(
            r'http-equiv="Content-Security-Policy" content="([^"]*)"', self.html
        )
        self.assertIsNotNone(csp, "CSP meta tag not found")
        # Reject a missing OR extra Mermaid version: every mermaid@x.y.z path the
        # CSP allows must equal the pinned <script src> version. A substring check
        # would pass even if the CSP also whitelisted an old, vulnerable version.
        csp_versions = re.findall(
            r"cdn\.jsdelivr\.net/npm/mermaid@(\d+\.\d+\.\d+)/", csp.group(1)
        )
        self.assertEqual(
            set(csp_versions),
            {version},
            "CSP must pin exactly the <script src> Mermaid version (no missing/extra versions)",
        )

    def test_inline_init_hash_matches_csp(self) -> None:
        # The CSP allows the init script only by its sha256. Recompute the hash of
        # the actual inline script and assert the CSP's script-src still lists it,
        # so editing the init without updating the CSP is caught here, not at runtime.
        # Anchor on `mermaid.initialize(` so the literal "<script>" inside the
        # comment above and the CDN "<script src=...>" are both excluded; DOTALL
        # lets a `<` inside the script (e.g. `a < b`) not truncate the capture.
        match = re.search(
            r"<script>(mermaid\.initialize\(.*?)</script>", self.html, re.DOTALL
        )
        self.assertIsNotNone(match, "inline mermaid.initialize <script> not found")
        init = match.group(1)
        digest = base64.b64encode(hashlib.sha256(init.encode("utf-8")).digest()).decode()
        # The hash must live inside the CSP script-src directive, not merely somewhere
        # in the document (a hash in a comment or another directive must not satisfy).
        csp = re.search(
            r'http-equiv="Content-Security-Policy" content="([^"]*)"', self.html
        )
        self.assertIsNotNone(csp, "CSP meta tag not found")
        script_src = re.search(r"script-src ([^;]*)", csp.group(1))
        self.assertIsNotNone(script_src, "CSP has no script-src directive")
        self.assertIn(
            f"sha256-{digest}",
            script_src.group(1),
            "inline init sha256 is not in the CSP script-src (recompute the hash)",
        )


if __name__ == "__main__":
    unittest.main()
