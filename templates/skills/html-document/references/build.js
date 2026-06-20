#!/usr/bin/env node
'use strict';
/*
 * km:html-document の単一ファイルビルド。
 *
 * 本文だけを書いた HTML（document-template.html ベース、BUILD:INLINE マーカー入り）に、
 * 同ディレクトリの document-template.css / document-template.js を機械的に挿入し、単一の
 * 自己完結 HTML を作る。AI は本文だけを書き、CSS/JS をコンテキストに載せずに済む。
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

// マーカーを CSS / JS 本体で置換した単一 HTML を返す。プレースホルダが無ければ失敗させる。
// <style>/<script> タグごとアンカーするので、本文に同じコメント文字列が現れても巻き込まない。
// split/join で置換し、$ を含む JS（テンプレートリテラルの ${...}）が特殊置換として解釈されるのを避ける。
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
