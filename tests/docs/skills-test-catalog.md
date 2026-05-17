# Skills Test Catalog

## Canonical Cases

| Case ID | Boundary |
| --- | --- |
| `trigger-review-default` | generic review request routes through `km:review` |
| `trigger-github-workflow-natural-language` | explicit PR/delivery request uses `km:github-workflow` |
| `trigger-commit-natural-language` | explicit commit intent routes to `km:commit` |
| `trigger-implementation-should-not-trigger-github-workflow` | generic implementation does not steal PR workflow |
| `trigger-third-party-oss-security-review-npm` | explicit OSS intake routes to the specialized skill |
| `trigger-plan-natural-language` | explicit planning request routes to `km:plan` |
| `review-routing-code-only-standard` | code-only path executes Phase 2 + Phase 4 need-check |
| `review-routing-docs-only` | docs-only path skips Phase 2/3 and runs Phase 4 full |
| `review-routing-config-chore` | config/chore path executes Phase 2 only, no Phase 3/4 |
| `review-routing-code-and-docs-thorough` | thorough code+docs path runs Phase 3 with 3 experts in parallel |
| `review-routing-pr-thorough` | PR target with thorough level resolves and runs all phases |
| `review-routing-ambiguous-numeric` | bare numeric argument is rejected as ambiguous |
| `review-routing-quick-code-only` | quick level on code-only triggers Phase 4 need-check mode |
| `review-routing-repo-thorough` | --repo subtree with thorough runs all phases in mixed mode |
| `review-loop-trigger-natural-language` | "レビューを繰り返す" triggers km:review-loop (not km:review) |
| `review-loop-pass-on-first-try` | clean diff completes in loop=1 with cumulative MEDIUM/LOW auto-fix |
| `review-loop-blocked-then-pass` | HIGH detected -> auto-fix -> re-run -> PASS in loop=2 |
| `review-loop-max-loops-exceeded` | max-loops cap triggers user judgment prompt |
| `review-loop-exception-clause` | design tradeoff is recorded as accepted risk, not auto-fixed |
| `workflow-existing-pr` | existing PR is reused |
| `workflow-issue-ambiguous-candidates` | ambiguous issue candidates stop for clarification |
| `workflow-body-file-only` | issue / PR body submission stays on the body-file path |
| `workflow-non-github-repo-stop` | non-GitHub repos stop before side effects |
| `plan-mode-no-mutation` | Plan Mode stays draft-only |
| `plan-output-tracked-plan-needs-confirmation` | tracked `.plan` stops before write |
| `plan-existing-issue-explicit-update-without-marker-needs-confirmation` | unmanaged issue overwrite needs confirmation |

## Retired Cases

| Retired Case / Group | Reason / Destination |
| --- | --- |
| `review-routing-skip-gating` | retired in PR #45 — `--skip-gating` was removed from km:review when iteration moved to km:review-loop |
| detailed review-quality scenarios | `tests/skills/rubrics/output-quality.md` |
| non-canonical routing variations | `tests/skills/rubrics/routing.md` |
| detailed plan file naming / sync permutations | stable contract checks in `verify-skill-tests.sh` plus this catalog |
| detailed workflow issue/base/body permutations | stable contract checks in `verify-skill-tests.sh` plus this catalog |
| duplicate trigger wording variants | removed because they do not add a new decision boundary |

## Canary Samples

| Canary | Expected Failure |
| --- | --- |
| remove the blocking bullet from `templates/skills/review/SKILL.md` `Success Criteria` | `verify-skill-tests.sh` fails the review stable-contract check |
| remove `gh issue edit <number> --body-file <plan-file>` from `templates/skills/plan/SKILL.md` | `verify-skill-tests.sh` fails the plan stable-contract check |
| remove `branch 作成 / push / PR 作成の要求が曖昧な場合は、workflow 開始前にユーザーへ確認する` from `templates/skills/github-workflow/SKILL.md` | `verify-skill-tests.sh` fails the github-workflow stable-contract check |
