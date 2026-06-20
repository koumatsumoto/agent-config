"""Guards the security invariants of the km:html-document HTML template.

The template ships a strict CSP and an SRI-pinned Mermaid load. The script-src
allows only the pinned Mermaid CDN path — no inline scripts, no 'unsafe-inline',
no hash or nonce — so a stray inline <script> (e.g. from an escaping gap) is
blocked by the browser. Mermaid auto-renders on load with its default strict
securityLevel, so no inline init script is needed. These tests fail fast when an
egress/backstop token is dropped, when an inline <script> or 'unsafe-inline' is
introduced, or when a Mermaid version bump leaves the CSP script-src path out of
sync with the <script src> URL. Verifying that the SRI sha384 matches the CDN
bytes needs the network and is out of scope here, so a version bump still
requires a manual SRI recompute.

Run with the scripts/ dir as the top-level import root:
    python3 -m unittest discover -s scripts/tests -t scripts
"""

from __future__ import annotations

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
            "connect-src 'none'",
            'name="referrer" content="no-referrer"',
            "integrity=\"sha384-",
            'crossorigin="anonymous"',
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

    def test_script_src_disallows_inline_execution(self) -> None:
        # The XSS backstop: script-src lists only the pinned CDN host, with no way
        # to run inline script. So a stray <script> from an escaping gap is blocked
        # by the browser rather than executed.
        csp = re.search(
            r'http-equiv="Content-Security-Policy" content="([^"]*)"', self.html
        )
        self.assertIsNotNone(csp, "CSP meta tag not found")
        script_src = re.search(r"script-src ([^;]*)", csp.group(1))
        self.assertIsNotNone(script_src, "CSP has no script-src directive")
        directive = script_src.group(1)
        self.assertNotIn(
            "'unsafe-inline'", directive, "script-src must not allow 'unsafe-inline'"
        )
        self.assertNotIn(
            "sha256-", directive, "script-src must not whitelist an inline-script hash"
        )
        self.assertNotIn("nonce-", directive, "script-src must not use a nonce")

    def test_no_inline_script(self) -> None:
        # Mermaid auto-renders on load (default startOnLoad + strict securityLevel),
        # so the only <script> is the SRI-pinned CDN loader. Comments are stripped
        # first so the literal "<script>" inside the CSP comment is not counted.
        no_comments = re.sub(r"<!--.*?-->", "", self.html, flags=re.DOTALL)
        script_opens = re.findall(r"<script\b([^>]*)>", no_comments)
        self.assertEqual(
            len(script_opens),
            1,
            "expected exactly one <script>: the Mermaid CDN loader",
        )
        self.assertIn(
            "src=",
            script_opens[0],
            "the only <script> must be an external src= loader (no inline script)",
        )


if __name__ == "__main__":
    unittest.main()
