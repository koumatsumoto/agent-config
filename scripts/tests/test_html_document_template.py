"""Guards the render and security contracts of km-html-document.

The trusted shell and assets stay separate from caller-authored HTML fragments.
render.js validates all shell markers and combines those inputs into the final
single-file report. Mermaid remains pinned to its CDN with SRI.

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
from typing import Optional

REF = (
    Path(__file__).resolve().parents[2]
    / "templates"
    / "skills"
    / "km-html-document"
    / "references"
)
SKILL = REF.parent
SKELETON = REF / "document-template.html"
CSS = REF / "document-template.css"
JS = REF / "document-template.js"
RENDER_JS = SKILL / "scripts" / "render.js"
TITLE_MARKER = "<!-- RENDER:TITLE -->"
CONTENT_MARKER = "<!-- RENDER:CONTENT -->"
CSS_MARKER = "<style>/* BUILD:INLINE document-template.css */</style>"
JS_MARKER = "<script>/* BUILD:INLINE document-template.js */</script>"


class HtmlDocumentTemplateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skeleton = SKELETON.read_text(encoding="utf-8")
        cls.css = CSS.read_text(encoding="utf-8")
        cls.js = JS.read_text(encoding="utf-8")
        cls.html = cls.skeleton + cls.css + cls.js

    def test_sources_exist(self) -> None:
        for path in (SKELETON, CSS, JS, RENDER_JS):
            self.assertTrue(path.is_file(), f"missing template source: {path}")

    def test_skeleton_keeps_exactly_one_of_each_marker(self) -> None:
        for marker in (TITLE_MARKER, CONTENT_MARKER, CSS_MARKER, JS_MARKER):
            with self.subTest(marker=marker):
                self.assertEqual(self.skeleton.count(marker), 1)

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
        # Token-level check: `'none'` only blocks when it is the sole source. A
        # substring assert would pass `connect-src 'none' https://evil.com`, so
        # require the directive value to be exactly {'none'}.
        for directive in ("default-src", "connect-src"):
            m = re.search(rf"{directive} ([^;]*)", csp)
            self.assertIsNotNone(m, f"CSP has no {directive} directive")
            self.assertEqual(
                set(m.group(1).split()),
                {"'none'"},
                f"{directive} must be exactly 'none' (no extra/remote source)",
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
        self.assertIn("image/webp", self.html, "WebP export target is missing")
        self.assertIn("htmlLabels: false", self.html, "htmlLabels:false (export-safe SVG) is missing")


@unittest.skipUnless(shutil.which("node"), "node not available")
class HtmlDocumentRenderTests(unittest.TestCase):
    def run_render(
        self,
        source: Path,
        output: Path,
        *,
        title: str = "A & B < C \"quote\" 'single'",
        overwrite: bool = False,
        render_js: Path = RENDER_JS,
        cwd: Optional[Path] = None,
    ) -> subprocess.CompletedProcess[bytes]:
        command = [
            "node",
            str(render_js),
            "--source",
            str(source),
            "--output",
            str(output),
            "--title",
            title,
        ]
        if overwrite:
            command.append("--overwrite")
        return subprocess.run(command, cwd=cwd, capture_output=True)

    def test_renders_fragment_assets_and_escaped_title_from_any_cwd(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source $ fragment.html"
            output = root / "output $ document.html"
            fragment = '<header class="doc-header"><h1>本文</h1></header>'
            source.write_text(fragment, encoding="utf-8")
            result = self.run_render(source, output, cwd=root)

            self.assertEqual(result.returncode, 0, result.stderr.decode())
            html = output.read_text(encoding="utf-8")
            self.assertIn(fragment, html)
            self.assertIn("<title>A &amp; B &lt; C &quot;quote&quot; &#39;single&#39;</title>", html)
            self.assertIn("--content-width: 1400px", html)
            self.assertIn("mermaid.initialize", html)
            for marker in ("RENDER:TITLE", "RENDER:CONTENT", "BUILD:INLINE"):
                self.assertNotIn(marker, html)

    def test_existing_output_requires_explicit_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.html"
            output = root / "output.html"
            source.write_text("<section>new</section>", encoding="utf-8")
            output.write_text("sentinel", encoding="utf-8")

            refused = self.run_render(source, output)
            self.assertNotEqual(refused.returncode, 0)
            self.assertEqual(output.read_text(encoding="utf-8"), "sentinel")

            replaced = self.run_render(source, output, overwrite=True)
            self.assertEqual(replaced.returncode, 0, replaced.stderr.decode())
            self.assertIn("<section>new</section>", output.read_text(encoding="utf-8"))

    def test_rejects_same_source_and_output_as_usage_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "same.html"
            source.write_text("<section>content</section>", encoding="utf-8")
            result = self.run_render(source, source)
            self.assertEqual(result.returncode, 2)
            self.assertIn(b"usage:", result.stderr)

    def test_rejects_blank_source_without_creating_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "blank.html"
            output = Path(tmp) / "output.html"
            source.write_text(" \n\t", encoding="utf-8")
            result = self.run_render(source, output)
            self.assertEqual(result.returncode, 1)
            self.assertFalse(output.exists())

    def test_marker_text_inside_fragment_is_inserted_raw(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source.html"
            output = root / "output.html"
            fragment = f"<pre>{TITLE_MARKER} {CONTENT_MARKER} {CSS_MARKER} {JS_MARKER}</pre>"
            source.write_text(fragment, encoding="utf-8")
            result = self.run_render(source, output)
            self.assertEqual(result.returncode, 0, result.stderr.decode())
            self.assertIn(fragment, output.read_text(encoding="utf-8"))

    def test_rejects_each_missing_or_duplicate_shell_marker(self) -> None:
        markers = (TITLE_MARKER, CONTENT_MARKER, CSS_MARKER, JS_MARKER)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for mode in ("missing", "duplicate"):
                for index, marker in enumerate(markers):
                    with self.subTest(mode=mode, marker=marker):
                        copied_skill = root / f"skill-{mode}-{index}"
                        shutil.copytree(SKILL, copied_skill)
                        template = copied_skill / "references" / "document-template.html"
                        text = template.read_text(encoding="utf-8")
                        replacement = "" if mode == "missing" else marker + marker
                        template.write_text(text.replace(marker, replacement), encoding="utf-8")
                        source = root / f"source-{mode}-{index}.html"
                        output = root / f"output-{mode}-{index}.html"
                        source.write_text("<section>content</section>", encoding="utf-8")

                        result = self.run_render(
                            source,
                            output,
                            render_js=copied_skill / "scripts" / "render.js",
                        )
                        self.assertEqual(result.returncode, 1)
                        self.assertFalse(output.exists())

    def test_usage_errors_return_two(self) -> None:
        cases = [
            [],
            ["--source"],
            ["--unknown", "value"],
            ["--source", "a", "--source", "b", "--output", "c", "--title", "d"],
            ["--source", "a", "--output", "b", "--title", "   "],
            ["--source", "a", "--output", "b", "--title", "c", "--overwrite", "--overwrite"],
        ]
        for arguments in cases:
            with self.subTest(arguments=arguments):
                result = subprocess.run(["node", str(RENDER_JS), *arguments], capture_output=True)
                self.assertEqual(result.returncode, 2)
                self.assertIn(b"usage:", result.stderr)


if __name__ == "__main__":
    unittest.main()
