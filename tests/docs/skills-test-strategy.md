# Skills Test Strategy

`tests/skills/` は skill の全文仕様を fixture 化する場所ではない。ここで守るのは、壊れると運用事故や trigger 誤判定につながる static contract と canonical decision boundary だけ。

## Goals

- 入口 skill の誤判定を早く見つける
- `review` / `github-workflow` / `plan` の安全な workflow contract を守る
- `AGENTS.md` / `CLAUDE.md` / skill metadata の drift を静的に見つける
- 新しい skill 追加時の test 追従を最小化する

## Non-Goals

- 実モデルの応答品質を自動採点すること
- 全ての wording variation を回帰 fixture にすること
- rubric だけで判断できる品質期待を YAML case に残し続けること

## Three Tiers

### Tier 1: Static Contracts

機械的に壊れると困る契約を検査する。

- manifest / scenario 整合
- `SKILL.md` frontmatter
  - `name`, `description` の存在
  - `description` と `when_to_use` の合算長
  - 本文行数上限
- supporting file の実在
- `AGENTS.md` / `CLAUDE.md` の主要原則、ワークフロー、運用ルール参照の一致
- high-risk skill の stable contract
  - 既存 `Success Criteria`
  - 必要な `Safety Rules`

### Tier 2: Canonical Decision Cases

新しい decision boundary が増えたときだけ増やす。

- trigger
  - `commit` を含む workflow trigger
- review routing
- workflow safety
- plan safety

case 数の目安は 15-18。網羅ではなく代表性を優先する。

### Tier 3: Human Guidance

rubric や docs に残す。

- 出力品質の期待
- 長い routing 例
- retired case の理由
- canary sample

## Manual-Only / Auto-Invocable Boundary

この repo では境界を 2 層に分けて扱う。

### Claude Code side

- `disable-model-invocation: true`
  - Claude から自動起動させたくない skill の frontmatter 契約

### Codex side

- `templates/skills/<name>/agents/openai.yaml`
  - `policy.allow_implicit_invocation: false`
  - Codex 側の manual-only 契約

現状の verify では **Codex 側を機械検証の正** としつつ、Claude Code 側 frontmatter も確認する。両側が完全に同じ集合であることまでは前提にしない。

## Stable Contract Policy

新しい `contract` heading は作らない。既存の以下を stable contract として扱う。

- `## Success Criteria`
- high-risk workflow skill における `## Safety Rules`

対象は次の 3 skill。

- `templates/skills/review/SKILL.md`
- `templates/skills/github-workflow/SKILL.md`
- `templates/skills/plan/SKILL.md`

## Add / Remove Rules

### Add a new canonical case only if

- 新しい入口優先度が増える
- 新しい副作用 safety rule が増える
- 既存 routing table にない分岐が増える
- repo-wide documentation contract が増える

### Do not add a case if

- 説明を詳しくしただけ
- 例を増やしただけ
- rubric を詳しくしただけ
- 既存境界の wording variation だけ

## Tier 3 Destinations

- 出力品質期待: `tests/skills/rubrics/output-quality.md`
- routing の長尺例: `tests/skills/rubrics/routing.md`
- retired case 一覧と canary: `tests/docs/skills-test-catalog.md`

manifest から外した scenario は残置しない。知識を残す場合は rubric か docs に移してから YAML を削除する。
