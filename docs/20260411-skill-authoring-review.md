# 2026-04 Skill Authoring Review

`templates/skills/` を 2026-04-11 時点の一次情報で見直した記録。対象は Claude Code / Codex 共用スキル。

## 調査対象（2026-04-11 参照）

- Anthropic: [Extend Claude with skills](https://code.claude.com/docs/en/slash-commands)
- Anthropic: [Create custom subagents](https://code.claude.com/docs/en/sub-agents)
- Anthropic: [Be clear, direct, and detailed](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/be-clear-and-direct)
- OpenAI: [Agent Skills – Codex](https://developers.openai.com/codex/skills)
- OpenAI: [Reasoning best practices](https://developers.openai.com/api/docs/guides/reasoning-best-practices)
- OpenAI: [Evaluation best practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices)

## 2026-04-11 時点の評価基準

### 1. Trigger 設計

- `description` は「何をするか」だけでなく「いつ使うか / いつ使わないか」を前方で明示する
- 暗黙起動が不要なワークフローは無効化する
- オーケストレーターとサブスキルが競合しないよう、入口を絞る

### 2. Context 効率

- `SKILL.md` は概要と実行契約に寄せる
- 詳細な例、長い列挙、補助資料は supporting files に分離する
- reference skill と workflow skill を混同しない

### 3. 実行可能性

- 手順は numbered steps で書き、停止条件と成功条件を明示する
- `context: fork` や subagent は、明示的タスクがあるときだけ使う
- side effect のある skill は手動起動前提にする（ただし commit / github-workflow のような workflow skill は例外とし、auto-invocable を維持する）

### 4. 出力契約

- レビュー系は「何を調べるか」だけでなく「何を報告しないか」を書く
- レポート形式、ブロック条件、重複排除ルールを固定する
- 推測ベースの指摘は根拠が弱ければ除外する

### 5. 評価可能性

- skill 自体にも success criteria を持たせる
- edge case と false positive の扱いを明示する
- 自動評価しやすいテンプレートやチェックポイントを優先する

## 現状 skill の主な問題

### 不足していた情報

- manual-only にすべき skill の invocation policy
- `km:review` を優先入口にする設計意図
- 各 review skill の success criteria
- Codex 側での暗黙起動ポリシー

### 過剰だった情報

- 背景説明の重複
- 各 review skill の長い導入文
- 同じ意味の workflow / phase の二重説明
- skill 本体に置く必要の薄い一般論

## 採用した改善方針

1. `km:review` を既定のレビュー入口として残し、下位 review skill は manual-only に寄せる
2. `km:commit` と `km:github-workflow` は自然言語要求から起動しうる workflow skill として維持する
3. review subskill 4 種（code-review, quality-review, doc-review, intent-review）に Codex 向け `agents/openai.yaml` を追加し、Claude 側の `disable-model-invocation` と「暗黙起動を抑える」という目的を揃える。workflow skill（commit, github-workflow）は auto-invocable を維持する
4. 各 skill から背景説明を削り、success criteria / stop conditions / output requirements を前に出す
5. README と共通ガイドラインにも manual-only / orchestrator-first を反映する

## 横並びレビュー後の最終判断

### 維持したもの

- `km:review` の orchestrator 設計
- `km:review` を auto-invocable な既定入口として残す判断
- `quality-review/quality-checklist.md` + `reference/` への詳細委譲
- report-format を skill ごとに持つ構成

### 変更したもの

- review subskills の自動起動
- 各 skill の導入文と workflow 記述
- README / AGENTS / CLAUDE での skill 利用方針

### 今回見送ったもの

- `km:*` 命名の変更
  - 既存 slash command と利用習慣の互換性を壊すため
- review report format の完全共通化
  - 自己完結性が下がる割に、現時点の重複削減効果が限定的なため

## この変更で得るもの

- 自動起動ノイズの削減
- `km:review` へのルーティング一貫性
- skill 本体の可読性向上
- Claude / Codex 間で「暗黙起動を抑える目的」を共有しつつ、実装差異を明示できる

## 実装差異の注意

- Claude の `disable-model-invocation: true` は、モデルからの自動起動を止めるだけでなく、その skill を常時コンテキストから外す
- Codex の `allow_implicit_invocation: false` は、暗黙選択を止める metadata であり、明示起動や skill metadata の扱いは Claude と同一ではない
- そのため両者は「同じ機能」ではなく、「暗黙起動を抑える」という目的が近い設定として扱う
