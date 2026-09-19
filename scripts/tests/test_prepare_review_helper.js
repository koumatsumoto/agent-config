import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { pathToFileURL } from "node:url";

import {
  PrepareReviewError,
  createWorkspace,
  isWithin,
  parseArguments,
  parseRange,
  prepareReview,
  resolvePr,
  resolvePreviousIntegration,
  resolveRange,
  resolveRepoTarget,
  resolveRepository,
  resolveTarget,
  runCommand,
} from "../../templates/skills/km-review/scripts/prepare-review.js";

const REPOSITORY_ROOT = path.resolve(import.meta.dirname, "../..");
const HELPER = path.join(
  REPOSITORY_ROOT,
  "templates/skills/km-review/scripts/prepare-review.js",
);

function command(commandName, args, cwd, options = {}) {
  const result = spawnSync(commandName, args, {
    cwd,
    encoding: "utf8",
    shell: false,
    ...options,
  });
  assert.equal(result.error, undefined, result.error?.message);
  assert.equal(result.status, 0, result.stderr);
  return result.stdout.trim();
}

function git(cwd, ...args) {
  return command("git", args, cwd);
}

function createRepository(t) {
  const root = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), "prepare-review-test-")));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  git(root, "init");
  git(root, "config", "user.name", "Test User");
  git(root, "config", "user.email", "test@example.invalid");
  fs.writeFileSync(path.join(root, "tracked.txt"), "first\n");
  git(root, "add", "tracked.txt");
  git(root, "commit", "-m", "initial");
  return root;
}

function repositoryDescriptor(root) {
  return resolveRepository(root, runCommand);
}

function expectPrepareError(callback, exitCode) {
  assert.throws(callback, (error) => {
    assert.ok(error instanceof PrepareReviewError);
    assert.equal(error.exitCode, exitCode);
    return true;
  });
}

test("worktree mode separates clean, changes, ignored files, and status errors", async (t) => {
  const root = createRepository(t);
  const repository = repositoryDescriptor(root);
  const options = parseArguments([]);
  assert.equal(resolveTarget(options, repository).empty, true);

  await t.test("unstaged", () => {
    fs.writeFileSync(path.join(root, "tracked.txt"), "changed\n");
    assert.equal(resolveTarget(options, repository).empty, false);
    git(root, "restore", "tracked.txt");
  });
  await t.test("staged", () => {
    fs.writeFileSync(path.join(root, "tracked.txt"), "staged\n");
    git(root, "add", "tracked.txt");
    assert.equal(resolveTarget(options, repository).empty, false);
    git(root, "restore", "--staged", "tracked.txt");
    git(root, "restore", "tracked.txt");
  });
  await t.test("untracked", () => {
    fs.writeFileSync(path.join(root, "new.txt"), "untracked\n");
    assert.equal(resolveTarget(options, repository).empty, false);
    fs.rmSync(path.join(root, "new.txt"));
  });
  await t.test("ignored only", () => {
    fs.writeFileSync(path.join(root, ".gitignore"), "ignored.txt\n");
    git(root, "add", ".gitignore");
    git(root, "commit", "-m", "ignore fixture");
    fs.writeFileSync(path.join(root, "ignored.txt"), "ignored\n");
    const updatedRepository = repositoryDescriptor(root);
    assert.equal(resolveTarget(options, updatedRepository).empty, true);
  });
  await t.test("status failure is not empty", () => {
    const runner = (name, args) => {
      if (name === "git" && args[0] === "status") return { status: 2, stdout: "", stderr: "bad" };
      return runCommand(name, args, { cwd: root });
    };
    expectPrepareError(() => resolveTarget(options, repositoryDescriptor(root), runner), 4);
  });
});

test("commit resolution uses --end-of-options and never falls back", (t) => {
  const root = createRepository(t);
  const repository = repositoryDescriptor(root);
  const seen = [];
  const recordingRunner = (name, args, options) => {
    seen.push([name, args]);
    return runCommand(name, args, options);
  };
  const result = resolveTarget(parseArguments(["HEAD"]), repository, recordingRunner);
  assert.equal(result.mode, "commit");
  assert.match(result.target.sha, /^[0-9a-f]{40}$/);
  assert.ok(seen.some(([, args]) => args.includes("--end-of-options")));
  expectPrepareError(
    () => resolveTarget(parseArguments(["missing-revision"]), repository, recordingRunner),
    3,
  );
  const spawnFailure = () => ({ status: null, stdout: "", stderr: "", error: new Error("spawn") });
  expectPrepareError(
    () => resolveTarget(parseArguments(["HEAD"]), repository, spawnFailure),
    4,
  );
});

test("two-dot and three-dot ranges resolve immutable SHAs and detect emptiness", (t) => {
  const root = createRepository(t);
  const first = git(root, "rev-parse", "HEAD");
  fs.writeFileSync(path.join(root, "tracked.txt"), "second\n");
  git(root, "commit", "-am", "second");
  const second = git(root, "rev-parse", "HEAD");

  const twoDot = resolveRange(`${first}..${second}`, root);
  assert.equal(twoDot.empty, false);
  assert.equal(twoDot.target.diffBaseSha, first);
  assert.equal(twoDot.target.rightSha, second);

  const threeDot = resolveRange(`${first}...${second}`, root);
  assert.equal(threeDot.empty, false);
  assert.equal(threeDot.target.diffBaseSha, first);
  assert.equal(threeDot.target.operator, "...");

  assert.equal(resolveRange(`${second}..${second}`, root).empty, true);
  expectPrepareError(() => parseRange("HEAD....main"), 2);
  expectPrepareError(() => parseRange("..HEAD"), 2);
});

test("PR resolution supports quoted shorthand and same-repository URLs", () => {
  const calls = [];
  let changedFiles = 2;
  const runner = (name, args, options) => {
    calls.push([name, args, options]);
    if (args[0] === "repo") {
      assert.deepEqual(options.unsetEnv, ["GH_REPO"]);
      return { status: 0, stdout: "owner/repo\n", stderr: "" };
    }
    if (args[0] === "api") {
      return {
        status: 0,
        stdout: JSON.stringify({
          number: 123,
          html_url: "https://github.com/owner/repo/pull/123",
          base: { sha: "a".repeat(40) },
          head: { sha: "b".repeat(40) },
          changed_files: changedFiles,
        }),
        stderr: "",
      };
    }
    throw new Error("unexpected command");
  };
  for (const input of ["#123", "https://github.com/owner/repo/pull/123"]) {
    const result = resolvePr(input, "/repo", runner);
    assert.equal(result.mode, "pr");
    assert.equal(result.empty, false);
    assert.equal(result.target.number, 123);
  }
  changedFiles = 0;
  assert.equal(resolvePr("#123", "/repo", runner).empty, true);
  assert.deepEqual(parseArguments(["#123"]).target, "#123");
  expectPrepareError(
    () => resolvePr("https://github.com/elsewhere/repo/pull/123", "/repo", runner),
    3,
  );
  const failingApi = (name, args) => {
    if (args[0] === "repo") return { status: 0, stdout: "owner/repo\n", stderr: "" };
    return { status: 1, stdout: "", stderr: "missing" };
  };
  expectPrepareError(() => resolvePr("#123", "/repo", failingApi), 3);
  assert.ok(calls.some(([name, args]) => name === "gh" && args[0] === "api"));
});

test("runCommand can remove GH_REPO from the child environment", () => {
  const result = runCommand(
    process.execPath,
    ["--eval", "process.stdout.write(process.env.GH_REPO ?? '')"],
    { env: { GH_REPO: "owner/wrong-repository" }, unsetEnv: ["GH_REPO"] },
  );
  assert.equal(result.status, 0, result.stderr);
  assert.equal(result.stdout, "");
});

test("containment rejects Windows cross-drive paths", () => {
  assert.equal(isWithin("C:\\repo\\nested", "C:\\repo", path.win32), true);
  assert.equal(isWithin("C:\\outside", "C:\\repo", path.win32), false);
  assert.equal(isWithin("D:\\outside", "C:\\repo", path.win32), false);
});

test("repo mode preserves the subtree and rejects missing or escaping paths", (t) => {
  const root = createRepository(t);
  const headSha = git(root, "rev-parse", "HEAD");
  fs.mkdirSync(path.join(root, "nested"));
  fs.writeFileSync(path.join(root, "nested", "file.txt"), "content\n");
  assert.equal(resolveRepoTarget(".", root, headSha).target.subtree, ".");
  const nested = resolveRepoTarget("nested/file.txt", root, headSha);
  assert.equal(nested.mode, "repo");
  assert.equal(nested.target.subtree, "nested/file.txt");
  expectPrepareError(() => resolveRepoTarget("missing", root, headSha), 3);
  expectPrepareError(() => resolveRepoTarget("../outside", root, headSha), 3);

  if (process.platform !== "win32") {
    const outside = fs.mkdtempSync(path.join(os.tmpdir(), "prepare-review-outside-"));
    t.after(() => fs.rmSync(outside, { recursive: true, force: true }));
    fs.symlinkSync(outside, path.join(root, "external-link"));
    expectPrepareError(() => resolveRepoTarget("external-link", root, headSha), 3);
  }
});

test("recheck normalizes a regular previous integration file", (t) => {
  const root = createRepository(t);
  const integration = path.join(root, "previous.md");
  fs.writeFileSync(integration, "previous report\n");
  assert.equal(resolvePreviousIntegration("previous.md", true, root), fs.realpathSync(integration));
  assert.equal(resolvePreviousIntegration(null, true, root), null);
  expectPrepareError(() => resolvePreviousIntegration("missing.md", true, root), 3);
  expectPrepareError(() => parseArguments(["--previous-integration", integration]), 2);
});

test("workspace paths are unique, outside the repository, and created only after validation", (t) => {
  const root = createRepository(t);
  const tempBase = fs.mkdtempSync(path.join(os.tmpdir(), "prepare-review-workspaces-"));
  t.after(() => fs.rmSync(tempBase, { recursive: true, force: true }));
  const first = createWorkspace(root, tempBase);
  const second = createWorkspace(root, tempBase);
  assert.notEqual(first.workspaceDir, second.workspaceDir);
  assert.equal(path.dirname(first.workspaceDir), fs.realpathSync(tempBase));
  assert.equal(first.integrationPath, path.join(first.workspaceDir, "integration.md"));
  assert.equal(fs.existsSync(first.integrationPath), false);

  const insideTemp = path.join(root, "temp");
  fs.mkdirSync(insideTemp);
  expectPrepareError(() => createWorkspace(root, insideTemp), 4);
  assert.deepEqual(fs.readdirSync(insideTemp), []);
});

test("helper does not copy secret content or modify repository metadata", (t) => {
  const root = createRepository(t);
  const tempBase = fs.mkdtempSync(path.join(os.tmpdir(), "prepare-review-secret-test-"));
  t.after(() => fs.rmSync(tempBase, { recursive: true, force: true }));
  const secret = "TOP_SECRET_VALUE_123";
  fs.writeFileSync(path.join(root, "untracked-secret.txt"), secret);
  const trackedBefore = fs.readFileSync(path.join(root, "tracked.txt"), "utf8");
  const ignoreBefore = fs.existsSync(path.join(root, ".gitignore"))
    ? fs.readFileSync(path.join(root, ".gitignore"), "utf8")
    : null;
  const excludePath = path.join(root, ".git", "info", "exclude");
  const excludeBefore = fs.readFileSync(excludePath, "utf8");

  const descriptor = prepareReview([], { cwd: root, tempDirectory: tempBase });
  assert.equal(descriptor.empty, false);
  assert.doesNotMatch(JSON.stringify(descriptor), new RegExp(secret));
  assert.deepEqual(fs.readdirSync(descriptor.workspaceDir), []);
  assert.equal(fs.readFileSync(path.join(root, "tracked.txt"), "utf8"), trackedBefore);
  assert.equal(
    fs.existsSync(path.join(root, ".gitignore"))
      ? fs.readFileSync(path.join(root, ".gitignore"), "utf8")
      : null,
    ignoreBefore,
  );
  assert.equal(fs.readFileSync(excludePath, "utf8"), excludeBefore);
});

test("CLI emits exactly one JSON object on success and stderr-only errors", (t) => {
  const root = createRepository(t);
  const success = spawnSync(process.execPath, [HELPER], {
    cwd: root,
    encoding: "utf8",
    shell: false,
  });
  assert.equal(success.status, 0, success.stderr);
  assert.equal(success.stderr, "");
  const lines = success.stdout.trimEnd().split("\n");
  assert.equal(lines.length, 1);
  const descriptor = JSON.parse(lines[0]);
  assert.equal(descriptor.schemaVersion, 1);
  t.after(() => fs.rmSync(descriptor.workspaceDir, { recursive: true, force: true }));

  const usageError = spawnSync(process.execPath, [HELPER, "--repo"], {
    cwd: root,
    encoding: "utf8",
    shell: false,
  });
  assert.equal(usageError.status, 2);
  assert.equal(usageError.stdout, "");
  assert.match(usageError.stderr, /^prepare-review: .+\n$/);

  const resolutionError = spawnSync(process.execPath, [HELPER, "missing-revision"], {
    cwd: root,
    encoding: "utf8",
    shell: false,
  });
  assert.equal(resolutionError.status, 3);
  assert.equal(resolutionError.stdout, "");
});

test("importing the ES module does not execute the CLI entry point", (t) => {
  const root = createRepository(t);
  const before = fs.readdirSync(os.tmpdir()).filter((name) => name.startsWith("km-review-")).sort();
  const imported = spawnSync(
    process.execPath,
    ["--input-type=module", "--eval", `await import(${JSON.stringify(pathToFileURL(HELPER).href)})`],
    { cwd: root, encoding: "utf8", shell: false },
  );
  assert.equal(imported.status, 0, imported.stderr);
  assert.equal(imported.stdout, "");
  assert.equal(imported.stderr, "");
  const after = fs.readdirSync(os.tmpdir()).filter((name) => name.startsWith("km-review-")).sort();
  assert.deepEqual(after, before);

  const source = fs.readFileSync(HELPER, "utf8");
  assert.match(source, /^import /m);
  assert.match(source, /^export /m);
  assert.doesNotMatch(source, /\brequire\s*\(|module\.exports|\bexports\./);
});

test("Skill invokes the Node helper directly and keeps target quoting", () => {
  const skillPath = path.join(REPOSITORY_ROOT, "templates/skills/km-review/SKILL.md");
  const skill = fs.readFileSync(skillPath, "utf8");
  assert.equal(fs.existsSync(HELPER), true);
  assert.match(skill, /node "<skill-directory>\/scripts\/prepare-review\.js" "<target>"/);
  assert.equal((skill.match(/node "<skill-directory>\/scripts\/prepare-review\.js"/g) ?? []).length, 1);
  assert.doesNotMatch(skill, /run-python\.sh|\bpython3?\b/);
});
