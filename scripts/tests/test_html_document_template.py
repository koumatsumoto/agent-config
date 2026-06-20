"""Guards the security invariants of the km:html-document HTML template.

The template ships as a skeleton (document-template.html) plus separate asset
files (document-template.css, document-template.js) that build.js inlines into a
single self-contained report. The diagram tools (wheel zoom, drag, PNG/WebP
export) run as an inline script, so script-src allows 'unsafe-inline' — the
security floor here is no external egress, not inline-script blocking.

These tests assemble the real output and fail fast when an egress control is
dropped or widened to a remote host (a report must not phone home): default-src
and connect-src must stay 'none', img-src must stay local (blob:/data:), and the
only remote host script-src/img-src may name is the pinned Mermaid CDN. They also
fail when the build markers go missing or a Mermaid version bump leaves the CSP
script-src path out of sync with the <script src> URL. Verifying that the SRI
sha384 matches the CDN bytes needs the network and is out of scope here, so a
version bump still requires a manual SRI recompute.

Run with the scripts/ dir as the top-level import root:
    python3 -m unittest discover -s scripts/tests -t scripts
"""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REF = (
    Path(__file__).resolve().parents[2]
    / "templates"
    / "skills"
    / "html-document"
    / "references"
)
SKELETON = REF / "document-template.html"
CSS = REF / "document-template.css"
JS = REF / "document-template.js"
BUILD_JS = REF / "build.js"

# Must match the markers in build.js and the skeleton.
CSS_MARKER = "/* BUILD:INLINE document-template.css */"
JS_MARKER = "/* BUILD:INLINE document-template.js */"


def _assemble(skeleton: str, css: str, js: str) -> str:
    """build.js と同じ素朴な置換でアセンブルした出力を返す（不変条件チェック用）。"""
    return skeleton.replace(CSS_MARKER, css).replace(JS_MARKER, js)


class HtmlDocumentTemplateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skeleton = SKELETON.read_text(encoding="utf-8")
        cls.css = CSS.read_text(encoding="utf-8")
        cls.js = JS.read_text(encoding="utf-8")
        # The real artifact is the assembled single file; assert invariants on it.
        cls.html = _assemble(cls.skeleton, cls.css, cls.js)

    def test_sources_exist(self) -> None:
        for path in (SKELETON, CSS, JS, BUILD_JS):
            self.assertTrue(path.is_file(), f"missing template source: {path}")

    def test_skeleton_keeps_build_markers(self) -> None:
        # The skeleton must keep both markers so build.js can inline the assets.
        # The agent edits body content only and leaves these in place.
        self.assertIn(CSS_MARKER, self.skeleton, "CSS build marker missing")
        self.assertIn(JS_MARKER, self.skeleton, "JS build marker missing")

    def test_assembly_consumes_markers(self) -> None:
        # After assembly the single file carries the css/js and no leftover markers.
        self.assertNotIn("BUILD:INLINE", self.html, "assembly left an un-inlined marker")
        self.assertIn("--content-width: 1400px", self.html, "css not inlined")
        self.assertIn("mermaid.initialize", self.html, "js (mermaid init) not inlined")

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_build_js_matches_assembly(self) -> None:
        # build.js must produce exactly the assembled output (no markers left).
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out.html"
            out.write_text(self.skeleton, encoding="utf-8")
            subprocess.run(
                ["node", str(BUILD_JS), str(out)], check=True, capture_output=True
            )
            built = out.read_text(encoding="utf-8")
        self.assertNotIn("BUILD:INLINE", built)
        self.assertEqual(built, self.html, "build.js output diverges from assembly")

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_build_js_requires_markers(self) -> None:
        # build.js must fail loudly when a marker is absent, so a broken skeleton is
        # caught at build time rather than silently shipping an unstyled report.
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out.html"
            out.write_text("<html>no markers</html>", encoding="utf-8")
            result = subprocess.run(
                ["node", str(BUILD_JS), str(out)], capture_output=True
            )
        self.assertNotEqual(result.returncode, 0, "build.js should fail on missing markers")

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
            self.assertIn(token, self.html, f"assembled report missing token: {token}")

    def test_mermaid_is_version_pinned(self) -> None:
        # SRI only protects a pinned URL; an unpinned @latest would defeat it.
        self.assertRegex(
            self.html,
            r"cdn\.jsdelivr\.net/npm/mermaid@\d+\.\d+\.\d+/dist/mermaid\.min\.js",
            "Mermaid must be loaded from a version-pinned UMD path",
        )

    def test_csp_version_matches_script_src(self) -> None:
        # A version bump must update the <script src> URL and the CSP script-src
        # path together; otherwise the browser blocks the new script.
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
        csp_versions = re.findall(
            r"cdn\.jsdelivr\.net/npm/mermaid@(\d+\.\d+\.\d+)/", csp.group(1)
        )
        self.assertEqual(
            set(csp_versions),
            {version},
            "CSP must pin exactly the <script src> Mermaid version (no missing/extra versions)",
        )

    def test_no_external_egress(self) -> None:
        # The security floor: a report must not be able to send data out. Inline
        # script is allowed (for the diagram tools), so egress control — not inline
        # blocking — is what these directives must guarantee.
        csp_match = re.search(
            r'http-equiv="Content-Security-Policy" content="([^"]*)"', self.html
        )
        self.assertIsNotNone(csp_match, "CSP meta tag not found")
        csp = csp_match.group(1)
        self.assertIn("default-src 'none'", csp, "default-src must stay 'none'")
        self.assertIn(
            "connect-src 'none'", csp, "connect-src must stay 'none' (no fetch/XHR/beacon)"
        )
        # img-src may allow local blob:/data: for canvas export, but no remote host.
        img = re.search(r"img-src ([^;]*)", csp)
        self.assertIsNotNone(img, "CSP has no img-src directive")
        for token in img.group(1).split():
            self.assertIn(
                token,
                {"blob:", "data:", "'none'", "'self'"},
                f"img-src must not allow a remote image source: {token}",
            )
        # script-src may allow 'unsafe-inline', but the only remote host is the Mermaid CDN.
        script_src = re.search(r"script-src ([^;]*)", csp)
        self.assertIsNotNone(script_src, "CSP has no script-src directive")
        for token in script_src.group(1).split():
            if token.startswith("http"):
                self.assertTrue(
                    token.startswith("https://cdn.jsdelivr.net/npm/mermaid@"),
                    f"script-src must not name a remote host other than the Mermaid CDN: {token}",
                )

    def test_diagram_tools_present(self) -> None:
        # The diagram interactivity (wheel zoom + raster export) is template infra;
        # guard that it isn't silently dropped. htmlLabels:false keeps SVGs
        # foreignObject-free so the canvas export is not tainted.
        self.assertIn("diagram-tools", self.html, "diagram toolbar (diagram-tools) is missing")
        self.assertIn("'wheel'", self.html, "wheel-zoom handler is missing")
        self.assertIn("toBlob", self.html, "canvas raster export (toBlob) is missing")
        self.assertIn("htmlLabels: false", self.html, "htmlLabels:false (export-safe SVG) is missing")


if __name__ == "__main__":
    unittest.main()
