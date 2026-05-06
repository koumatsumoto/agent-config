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
| `review-routing-code-only` | code-only path keeps intent/code/quality |
| `review-routing-docs-only` | docs-only path narrows to doc-review |
| `review-routing-config-chore` | config/chore path keeps Quick depth without expert review |
| `review-routing-no-conversation-context` | no context skips intent-review explicitly |
| `review-routing-code-and-docs-thorough` | thorough code+docs path preserves the full review set |
| `workflow-existing-pr` | existing PR is reused |
| `workflow-issue-ambiguous-candidates` | ambiguous issue candidates stop for clarification |
| `workflow-body-file-only` | issue / PR body submission stays on the body-file path |
| `workflow-non-github-repo-stop` | non-GitHub repos stop before side effects |
| `plan-mode-no-mutation` | Plan Mode stays draft-only |
| `plan-output-tracked-plan-needs-confirmation` | tracked `.plan` stops before write |
| `plan-existing-issue-explicit-update-without-marker-needs-confirmation` | unmanaged issue overwrite needs confirmation |

## Retired Cases

| Retired Group | Destination |
| --- | --- |
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
