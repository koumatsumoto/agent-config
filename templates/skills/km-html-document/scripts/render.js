#!/usr/bin/env node
'use strict';

const fs = require('node:fs');
const path = require('node:path');

const SKILL_DIR = path.resolve(__dirname, '..');
const REFERENCES_DIR = path.join(SKILL_DIR, 'references');
const TEMPLATE_PATH = path.join(REFERENCES_DIR, 'document-template.html');
const CSS_PATH = path.join(REFERENCES_DIR, 'document-template.css');
const JS_PATH = path.join(REFERENCES_DIR, 'document-template.js');

const TITLE_MARKER = '<!-- RENDER:TITLE -->';
const CONTENT_MARKER = '<!-- RENDER:CONTENT -->';
const CSS_TAG = '<style>/* BUILD:INLINE document-template.css */</style>';
const JS_TAG = '<script>/* BUILD:INLINE document-template.js */</script>';
const USAGE = 'usage: node render.js --source <fragment.html> --output <document.html> --title <text> [--overwrite]\n';

class UsageError extends Error {}

function parseArgs(argv) {
  const options = new Map();
  let overwrite = false;
  for (let index = 0; index < argv.length; index += 1) {
    const option = argv[index];
    if (option === '--overwrite') {
      if (overwrite) throw new UsageError('duplicate option: --overwrite');
      overwrite = true;
      continue;
    }
    if (!['--source', '--output', '--title'].includes(option)) {
      throw new UsageError(`unknown option: ${option}`);
    }
    if (options.has(option)) throw new UsageError(`duplicate option: ${option}`);
    if (index + 1 >= argv.length || argv[index + 1].startsWith('--')) {
      throw new UsageError(`missing value for ${option}`);
    }
    options.set(option, argv[index + 1]);
    index += 1;
  }
  for (const option of ['--source', '--output', '--title']) {
    if (!options.has(option)) throw new UsageError(`missing required option: ${option}`);
  }
  if (options.get('--title').trim() === '') throw new UsageError('--title must not be blank');

  const source = path.resolve(options.get('--source'));
  const output = path.resolve(options.get('--output'));
  if (source === output) throw new UsageError('--source and --output must differ');
  return { source, output, title: options.get('--title'), overwrite };
}

function countOccurrences(text, needle) {
  let count = 0;
  let offset = 0;
  while ((offset = text.indexOf(needle, offset)) !== -1) {
    count += 1;
    offset += needle.length;
  }
  return count;
}

function requireExactlyOne(text, marker, label) {
  const count = countOccurrences(text, marker);
  if (count !== 1) throw new Error(`${label} marker must appear exactly once; found ${count}`);
}

function escapeHtml(text) {
  return text
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

function render(template, css, js, source, title) {
  const markers = [
    [TITLE_MARKER, 'title'],
    [CONTENT_MARKER, 'content'],
    [CSS_TAG, 'CSS'],
    [JS_TAG, 'JavaScript'],
  ];
  for (const [marker, label] of markers) requireExactlyOne(template, marker, label);

  return template
    .replace(TITLE_MARKER, () => escapeHtml(title))
    .replace(CSS_TAG, () => `<style>\n${css}\n</style>`)
    .replace(JS_TAG, () => `<script>\n${js}\n</script>`)
    .replace(CONTENT_MARKER, () => source);
}

function publish(output, contents, overwrite) {
  const parent = path.dirname(output);
  const parentStat = fs.statSync(parent);
  if (!parentStat.isDirectory()) throw new Error(`output parent is not a directory: ${parent}`);
  if (!overwrite && fs.existsSync(output)) throw new Error(`output already exists: ${output}`);

  const temporary = path.join(parent, `.${path.basename(output)}.${process.pid}.${Date.now()}.tmp`);
  try {
    fs.writeFileSync(temporary, contents, { encoding: 'utf8', flag: 'wx' });
    if (!overwrite && fs.existsSync(output)) throw new Error(`output already exists: ${output}`);
    fs.renameSync(temporary, output);
  } finally {
    try {
      fs.unlinkSync(temporary);
    } catch (error) {
      if (error.code !== 'ENOENT') process.stderr.write(`warning: could not remove temporary file: ${error.message}\n`);
    }
  }
}

function main(argv) {
  let options;
  try {
    options = parseArgs(argv);
  } catch (error) {
    process.stderr.write(`${error.message}\n${USAGE}`);
    return 2;
  }

  try {
    const template = fs.readFileSync(TEMPLATE_PATH, 'utf8');
    const css = fs.readFileSync(CSS_PATH, 'utf8');
    const js = fs.readFileSync(JS_PATH, 'utf8');
    const source = fs.readFileSync(options.source, 'utf8');
    if (source.trim() === '') throw new Error('source fragment must not be blank');
    const result = render(template, css, js, source, options.title);
    publish(options.output, result, options.overwrite);
    process.stdout.write(`rendered single-file HTML: ${options.output}\n`);
    return 0;
  } catch (error) {
    process.stderr.write(`render error: ${error.message}\n`);
    return 1;
  }
}

if (require.main === module) process.exit(main(process.argv.slice(2)));

module.exports = { CONTENT_MARKER, CSS_TAG, JS_TAG, TITLE_MARKER, countOccurrences, escapeHtml, parseArgs, render };
