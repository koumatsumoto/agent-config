#!/usr/bin/env node
'use strict';
/*
 * 本文入りHTMLへCSSとJavaScriptを挿入し、単一ファイルにまとめる。
 * 本文作成時にCSSとJavaScriptを読み込む必要はない。
 *
 * 使い方:
 *     node build.js <html-path> [output-path]
 * output-path を省略すると入力を上書きする。
 */

const fs = require('node:fs');
const path = require('node:path');

const HERE = __dirname;
const CSS_MARKER = '/* BUILD:INLINE document-template.css */';
const JS_MARKER = '/* BUILD:INLINE document-template.js */';

// マーカーをCSSとJavaScriptへ置き換える。タグ単位で照合し、本文中の同じ文字列は変更しない。
// split/joinを使い、JavaScript内の$を特殊な置換として解釈しない。
function build(html, css, js) {
  const cssTag = `<style>${CSS_MARKER}</style>`;
  const jsTag = `<script>${JS_MARKER}</script>`;
  if (!html.includes(cssTag)) throw new Error(`CSS placeholder not found: ${cssTag}`);
  if (!html.includes(jsTag)) throw new Error(`JS placeholder not found: ${jsTag}`);
  return html.split(cssTag).join(`<style>\n${css}\n</style>`).split(jsTag).join(`<script>\n${js}\n</script>`);
}

function main(argv) {
  if (argv.length < 1 || argv.length > 2) {
    process.stderr.write('usage: node build.js <html-path> [output-path]\n');
    return 2;
  }
  const target = argv[0];
  const output = argv[1] || target;
  const css = fs.readFileSync(path.join(HERE, 'document-template.css'), 'utf8');
  const js = fs.readFileSync(path.join(HERE, 'document-template.js'), 'utf8');
  const result = build(fs.readFileSync(target, 'utf8'), css, js);
  fs.writeFileSync(output, result);
  process.stdout.write(`built single-file HTML: ${output}\n`);
  return 0;
}

if (require.main === module) {
  process.exit(main(process.argv.slice(2)));
}

module.exports = { build, CSS_MARKER, JS_MARKER };
