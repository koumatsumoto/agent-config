import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";

const REPOSITORY_ROOT = path.resolve(import.meta.dirname, "../..");
const HELPER = path.join(
  REPOSITORY_ROOT,
  "templates/skills/km-plan/scripts/prepare-plan.js",
);
const SKILL = path.join(REPOSITORY_ROOT, "templates/skills/km-plan/SKILL.md");

function runHelper(options = {}) {
  return spawnSync(process.execPath, [HELPER], {
    encoding: "utf8",
    shell: false,
    ...options,
  });
}

test("creates a unique empty plan.md and preserves the first file", (t) => {
  const first = runHelper();
  assert.equal(first.status, 0, first.stderr);
  assert.equal(first.stderr, "");
  assert.equal(first.stdout.split(/\r?\n/).filter(Boolean).length, 1);

  const firstPath = first.stdout.trim();
  assert.equal(path.isAbsolute(firstPath), true);
  assert.equal(path.basename(firstPath), "plan.md");
  assert.equal(fs.readFileSync(firstPath, "utf8"), "");
  t.after(() => fs.rmSync(path.dirname(firstPath), { recursive: true, force: true }));

  fs.writeFileSync(firstPath, "keep me", "utf8");
  const second = runHelper();
  assert.equal(second.status, 0, second.stderr);
  const secondPath = second.stdout.trim();
  assert.notEqual(secondPath, firstPath);
  assert.equal(fs.readFileSync(firstPath, "utf8"), "keep me");
  assert.equal(fs.readFileSync(secondPath, "utf8"), "");
  t.after(() => fs.rmSync(path.dirname(secondPath), { recursive: true, force: true }));
});

test("reports temp directory creation failure without a success path", (t) => {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "prepare-plan-test-"));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const invalidTempBase = path.join(root, "not-a-directory");
  fs.writeFileSync(invalidTempBase, "file", "utf8");

  const result = runHelper({
    env: {
      ...process.env,
      TMPDIR: invalidTempBase,
      TMP: invalidTempBase,
      TEMP: invalidTempBase,
    },
  });
  assert.notEqual(result.status, 0);
  assert.equal(result.stdout, "");
  assert.match(result.stderr, /^prepare-plan: /);
});

test("SKILL.md uses prepare-plan.js as its entrypoint", () => {
  const skill = fs.readFileSync(SKILL, "utf8");
  assert.match(skill, /node "<skill-directory>\/scripts\/prepare-plan\.js"/);
});
