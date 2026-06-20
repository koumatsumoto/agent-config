#!/usr/bin/env python3
"""km:html-document の単一ファイルビルド。

本文だけを書いた HTML（document-template.html ベース、BUILD:INLINE マーカー入り）に、
同ディレクトリの document-template.css / document-template.js を機械的に挿入し、単一の
自己完結 HTML を作る。AI は本文だけを書き、CSS/JS をコンテキストに載せずに済む。

使い方:
    python build.py <html-path> [output-path]
output-path を省略すると入力を上書きする。
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CSS_MARKER = "/* BUILD:INLINE document-template.css */"
JS_MARKER = "/* BUILD:INLINE document-template.js */"


def build(html: str, css: str, js: str) -> str:
    """マーカーを CSS / JS 本体で置換した単一 HTML を返す。マーカーが無ければ失敗させる。"""
    if CSS_MARKER not in html:
        raise ValueError(f"CSS marker not found: {CSS_MARKER!r}")
    if JS_MARKER not in html:
        raise ValueError(f"JS marker not found: {JS_MARKER!r}")
    return html.replace(CSS_MARKER, css).replace(JS_MARKER, js)


def main(argv: list[str]) -> int:
    if not 1 <= len(argv) <= 2:
        print(__doc__, file=sys.stderr)
        return 2
    target = Path(argv[0])
    output = Path(argv[1]) if len(argv) == 2 else target
    css = (HERE / "document-template.css").read_text(encoding="utf-8")
    js = (HERE / "document-template.js").read_text(encoding="utf-8")
    result = build(target.read_text(encoding="utf-8"), css, js)
    output.write_text(result, encoding="utf-8")
    print(f"built single-file HTML: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
