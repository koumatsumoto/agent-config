import { spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const GIT_TARGET_ENVIRONMENT = [
  "GIT_DIR",
  "GIT_WORK_TREE",
  "GIT_COMMON_DIR",
  "GIT_INDEX_FILE",
  "GIT_OBJECT_DIRECTORY",
  "GIT_ALTERNATE_OBJECT_DIRECTORIES",
  "GIT_CONFIG",
  "GIT_CONFIG_GLOBAL",
  "GIT_CONFIG_SYSTEM",
  "GIT_CONFIG_COUNT",
];

export class PrepareReviewError extends Error {
  constructor(message, exitCode) {
    super(message);
    this.name = "PrepareReviewError";
    this.exitCode = exitCode;
  }
}

function fail(message, exitCode) {
  throw new PrepareReviewError(message, exitCode);
}

function removeEnvironmentVariable(environment, variable) {
  if (process.platform !== "win32") {
    delete environment[variable];
    return;
  }
  for (const key of Object.keys(environment)) {
    if (key.toUpperCase() === variable.toUpperCase()) delete environment[key];
  }
}

export function runCommand(command, args, options = {}) {
  const environment = { ...process.env, ...options.env };
  for (const variable of options.unsetEnv ?? []) {
    removeEnvironmentVariable(environment, variable);
  }
  if (command === "git") {
    for (const variable of GIT_TARGET_ENVIRONMENT) {
      removeEnvironmentVariable(environment, variable);
    }
    environment.GIT_OPTIONAL_LOCKS = "0";
  }
  return spawnSync(command, args, {
    cwd: options.cwd,
    encoding: "utf8",
    env: environment,
    shell: false,
  });
}

export function parseArguments(args) {
  const result = {
    target: null,
    repo: null,
    recheck: false,
    previousIntegration: null,
  };

  for (let index = 0; index < args.length; index += 1) {
    const argument = args[index];
    if (argument === "--recheck") {
      result.recheck = true;
    } else if (argument === "--repo" || argument === "--previous-integration") {
      const value = args[index + 1];
      if (value === undefined || value.startsWith("--")) {
        fail(`${argument} requires a value`, 2);
      }
      if (argument === "--repo") {
        if (result.repo !== null) fail("--repo may be specified only once", 2);
        result.repo = value;
      } else {
        if (result.previousIntegration !== null) {
          fail("--previous-integration may be specified only once", 2);
        }
        result.previousIntegration = value;
      }
      index += 1;
    } else if (argument.startsWith("--")) {
      fail(`unknown option: ${argument}`, 2);
    } else if (result.target === null) {
      result.target = argument;
    } else {
      fail("only one positional target may be specified", 2);
    }
  }

  if (result.target !== null && result.repo !== null) {
    fail("a positional target cannot be combined with --repo", 2);
  }
  if (result.previousIntegration !== null && !result.recheck) {
    fail("--previous-integration requires --recheck", 2);
  }
  return result;
}

function commandFailure(result, message, nonZeroExitCode) {
  if (result.error || result.status === null) fail(message, 4);
  if (result.status !== 0) fail(message, nonZeroExitCode);
  return result.stdout.trim();
}

export function isWithin(candidate, root, pathApi = path) {
  const relative = pathApi.relative(root, candidate);
  return relative === "" || (
    !pathApi.isAbsolute(relative)
    && !relative.startsWith(`..${pathApi.sep}`)
    && relative !== ".."
  );
}

export function resolveRepository(cwd, runner = runCommand) {
  const rootResult = runner("git", ["rev-parse", "--show-toplevel"], { cwd });
  const rootOutput = commandFailure(rootResult, "not inside a Git repository", 4);
  let repositoryRoot;
  try {
    repositoryRoot = fs.realpathSync(path.resolve(cwd, rootOutput));
  } catch {
    fail("could not normalize the Git repository root", 4);
  }
  const headResult = runner("git", ["rev-parse", "--verify", "HEAD^{commit}"], {
    cwd: repositoryRoot,
  });
  const headSha = commandFailure(headResult, "could not resolve repository HEAD", 4);
  return { repositoryRoot, headSha };
}

function resolveCommitSha(input, repositoryRoot, runner) {
  const result = runner(
    "git",
    ["rev-parse", "--verify", "--end-of-options", `${input}^{commit}`],
    { cwd: repositoryRoot },
  );
  return commandFailure(result, `could not resolve revision: ${input}`, 3);
}

export function parseRange(input) {
  if (input.includes("....")) fail(`invalid range: ${input}`, 2);
  const tripleAt = input.indexOf("...");
  const operator = tripleAt >= 0 ? "..." : "..";
  const separatorAt = tripleAt >= 0 ? tripleAt : input.indexOf("..");
  if (separatorAt < 0) fail(`invalid range: ${input}`, 2);
  const left = input.slice(0, separatorAt);
  const right = input.slice(separatorAt + operator.length);
  if (!left || !right || left.includes("..") || right.includes("..")) {
    fail(`invalid range: ${input}`, 2);
  }
  return { left, right, operator };
}

export function resolveRange(input, repositoryRoot, runner = runCommand) {
  const { left, right, operator } = parseRange(input);
  const leftSha = resolveCommitSha(left, repositoryRoot, runner);
  const rightSha = resolveCommitSha(right, repositoryRoot, runner);
  let diffBaseSha = leftSha;
  if (operator === "...") {
    const mergeBaseResult = runner("git", ["merge-base", leftSha, rightSha], {
      cwd: repositoryRoot,
    });
    diffBaseSha = commandFailure(mergeBaseResult, `could not resolve merge base: ${input}`, 3);
  }
  const diffResult = runner("git", ["diff", "--quiet", diffBaseSha, rightSha, "--"], {
    cwd: repositoryRoot,
  });
  if (diffResult.error || diffResult.status === null || ![0, 1].includes(diffResult.status)) {
    fail(`could not compare range: ${input}`, 4);
  }
  return {
    mode: "range",
    empty: diffResult.status === 0,
    target: {
      input,
      operator,
      leftSha,
      rightSha,
      diffBaseSha,
      resolved: `${diffBaseSha}..${rightSha}`,
    },
  };
}

function parsePrTarget(input) {
  const shorthand = /^#([1-9]\d*)$/.exec(input);
  if (shorthand) return { number: Number(shorthand[1]), repository: null, host: null };
  const url = /^https:\/\/github\.com\/([^/]+)\/([^/]+)\/pull\/([1-9]\d*)\/?$/.exec(input);
  if (!url) return null;
  return { number: Number(url[3]), repository: `${url[1]}/${url[2]}`, host: "github.com" };
}

export function isPrTarget(input) {
  return parsePrTarget(input) !== null;
}

export function resolvePr(input, repositoryRoot, runner = runCommand) {
  const parsed = parsePrTarget(input);
  if (!parsed) fail(`invalid pull request target: ${input}`, 2);
  const identityResult = runner(
    "gh",
    ["repo", "view", "--json", "nameWithOwner,url"],
    { cwd: repositoryRoot, unsetEnv: ["GH_REPO", "GH_HOST"] },
  );
  const identityOutput = commandFailure(
    identityResult,
    "could not determine the local GitHub repository",
    4,
  );
  let repositoryIdentity;
  let repositoryHost;
  try {
    repositoryIdentity = JSON.parse(identityOutput);
    repositoryHost = new URL(repositoryIdentity.url).hostname;
  } catch {
    fail("gh repo view returned invalid repository identity", 4);
  }
  const nameWithOwner = repositoryIdentity.nameWithOwner;
  if (typeof nameWithOwner !== "string" || !nameWithOwner || !repositoryHost) {
    fail("gh repo view returned incomplete repository identity", 4);
  }
  if (parsed.repository && parsed.repository.toLowerCase() !== nameWithOwner.toLowerCase()) {
    fail(`pull request belongs to another repository: ${parsed.repository}`, 3);
  }
  if (parsed.host && parsed.host.toLowerCase() !== repositoryHost.toLowerCase()) {
    fail(`pull request belongs to another GitHub host: ${parsed.host}`, 3);
  }
  const apiResult = runner(
    "gh",
    ["api", "--hostname", repositoryHost, `repos/${nameWithOwner}/pulls/${parsed.number}`],
    { cwd: repositoryRoot, unsetEnv: ["GH_REPO", "GH_HOST"] },
  );
  if (apiResult.error || apiResult.status === null) {
    fail("could not run gh api", 4);
  }
  if (apiResult.status !== 0) {
    fail(`could not resolve pull request: #${parsed.number}`, 3);
  }
  let pullRequest;
  try {
    pullRequest = JSON.parse(apiResult.stdout);
  } catch {
    fail("gh api returned invalid pull request data", 4);
  }
  const required = [
    pullRequest.number,
    pullRequest.html_url,
    pullRequest.base?.sha,
    pullRequest.head?.sha,
    pullRequest.changed_files,
  ];
  if (required.some((value) => value === undefined || value === null)) {
    fail("gh api returned incomplete pull request data", 4);
  }
  return {
    mode: "pr",
    empty: pullRequest.changed_files === 0,
    target: {
      input,
      number: pullRequest.number,
      url: pullRequest.html_url,
      baseSha: pullRequest.base.sha,
      headSha: pullRequest.head.sha,
      changedFiles: pullRequest.changed_files,
      resolved: `${pullRequest.base.sha}...${pullRequest.head.sha}`,
    },
  };
}

export function resolveRepoTarget(input, repositoryRoot, headSha) {
  const lexicalPath = path.resolve(repositoryRoot, input);
  if (!isWithin(lexicalPath, repositoryRoot)) {
    fail(`repository target is outside the repository: ${input}`, 3);
  }
  let resolvedPath;
  try {
    resolvedPath = fs.realpathSync(lexicalPath);
  } catch {
    fail(`repository target does not exist: ${input}`, 3);
  }
  if (!isWithin(resolvedPath, repositoryRoot)) {
    fail(`repository target resolves outside the repository: ${input}`, 3);
  }
  const subtree = path.relative(repositoryRoot, resolvedPath).split(path.sep).join("/") || ".";
  return {
    mode: "repo",
    empty: false,
    target: {
      input,
      subtree,
      resolved: `repo:${subtree}@${headSha}`,
    },
  };
}

export function resolveTarget(options, repository, runner = runCommand) {
  const { repositoryRoot, headSha } = repository;
  if (options.repo !== null) {
    return resolveRepoTarget(options.repo, repositoryRoot, headSha);
  }
  if (options.target === null) {
    const statusResult = runner(
      "git",
      ["status", "--porcelain=v1", "-z", "--untracked-files=all"],
      { cwd: repositoryRoot },
    );
    if (statusResult.error || statusResult.status === null || statusResult.status !== 0) {
      fail("could not inspect uncommitted changes", 4);
    }
    return {
      mode: "worktree",
      empty: statusResult.stdout.length === 0,
      target: { input: null, resolved: `worktree@${headSha}` },
    };
  }
  if (isPrTarget(options.target)) {
    return resolvePr(options.target, repositoryRoot, runner);
  }
  if (options.target.includes("..")) {
    return resolveRange(options.target, repositoryRoot, runner);
  }
  const sha = resolveCommitSha(options.target, repositoryRoot, runner);
  return {
    mode: "commit",
    empty: false,
    target: { input: options.target, sha, resolved: sha },
  };
}

export function resolvePreviousIntegration(input, recheck, cwd) {
  if (input === null) return null;
  if (!recheck) fail("--previous-integration requires --recheck", 2);
  const candidate = path.resolve(cwd, input);
  let stats;
  try {
    stats = fs.statSync(candidate);
  } catch {
    fail(`previous integration file does not exist: ${input}`, 3);
  }
  if (!stats.isFile()) fail(`previous integration is not a regular file: ${input}`, 3);
  return fs.realpathSync(candidate);
}

export function createWorkspace(repositoryRoot, tempDirectory = os.tmpdir()) {
  let tempBase;
  try {
    tempBase = fs.realpathSync(tempDirectory);
  } catch {
    fail("could not normalize the OS temporary directory", 4);
  }
  if (isWithin(tempBase, repositoryRoot)) {
    fail("OS temporary directory must be outside the repository", 4);
  }
  try {
    const workspaceDir = fs.mkdtempSync(path.join(tempBase, "km-review-"));
    return { workspaceDir, integrationPath: path.join(workspaceDir, "integration.md") };
  } catch {
    fail("could not create review workspace", 4);
  }
}

export function prepareReview(args, dependencies = {}) {
  const options = parseArguments(args);
  const cwd = path.resolve(dependencies.cwd ?? process.cwd());
  const runner = dependencies.runner ?? runCommand;
  const repository = resolveRepository(cwd, runner);
  const previousIntegrationPath = resolvePreviousIntegration(
    options.previousIntegration,
    options.recheck,
    cwd,
  );
  const resolution = resolveTarget(options, repository, runner);
  const workspace = createWorkspace(repository.repositoryRoot, dependencies.tempDirectory ?? os.tmpdir());
  return {
    schemaVersion: 1,
    mode: resolution.mode,
    recheck: options.recheck,
    repositoryRoot: repository.repositoryRoot,
    headSha: repository.headSha,
    empty: resolution.empty,
    target: resolution.target,
    workspaceDir: workspace.workspaceDir,
    integrationPath: workspace.integrationPath,
    previousIntegrationPath,
  };
}

export function main(args = process.argv.slice(2)) {
  try {
    process.stdout.write(`${JSON.stringify(prepareReview(args))}\n`);
    return 0;
  } catch (error) {
    const exitCode = error instanceof PrepareReviewError ? error.exitCode : 4;
    const reason = error instanceof Error ? error.message : String(error);
    process.stderr.write(`prepare-review: ${reason.replace(/[\r\n]+/g, " ")}\n`);
    return exitCode;
  }
}

if (
  process.argv[1] &&
  import.meta.filename === fs.realpathSync(process.argv[1])
) {
  process.exitCode = main(process.argv.slice(2));
}
