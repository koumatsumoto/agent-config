---
name: km:review
description: Comprehensive review orchestrator that coordinates code-review, quality-review, and doc-review based on change type. Use when the user requests any kind of review, says "レビューして", "チェックして", "変更を確認して", "問題ないか見て", or after completing code changes. Runs code review in main context with full conversation history, quality and doc reviews as parallel sub-agents.
---

# Review

未コミット変更を対象に、開発観点・品質特性・ドキュメントの3軸で包括的なレビューを行うオーケストレーター。

変更内容を分析し、code-review / quality-review / doc-review を適切な深度と実行方式で並列に実施する。code-review はメインコンテキストで実行し（会話履歴から要件・意図を把握するため）、quality-review と doc-review はサブエージェントで並列実行してコンテキスト圧迫を防ぐ。

| レビュー | 観点 | 実行方式 |
|---------|------|---------|
| `/km:code-review` | 要件充足・設計・バグ・コード品質 | メインコンテキスト |
| `/km:quality-review` | ISO/IEC 25010 の8品質特性 | サブエージェント（並列） |
| `/km:doc-review` | 構造整合性・横断整合性・正確性 | サブエージェント（並列） |

## Workflow

1. **Phase 0: 変更把握・ルーティング** — 変更を分類し、実行するレビューとその深度を決定する
2. **Phase 1: 並列レビュー実行** — code-review はメイン、quality/doc-review はサブエージェントで並列実行
3. **Phase 2: 結果統合** — 全レビュー結果を統合サマリーにまとめ、コミット判定を行う

## Phase 0: 変更把握・ルーティング

`git diff --name-only` で変更ファイルを収集し、以下を判定する:

1. **変更タイプ**: feat / fix / refactor / test / config（会話履歴と変更内容から判断）
2. **変更の構成**: コード変更あり (`has_code`) / ドキュメント変更あり (`has_docs`)
3. **変更規模**: 変更行数、ファイル数

判定結果に基づき、実行するレビューを決定する:

| 変更の構成 | code-review | quality-review | doc-review | ドキュメント更新チェック |
|---|---|---|---|---|
| コード + ドキュメント | メインで実行 | サブエージェントで実行 | サブエージェントで実行 | — |
| コードのみ | メインで実行 | サブエージェントで実行 | 実行しない | メインで簡易チェック |
| ドキュメントのみ | 実行しない | 実行しない | サブエージェントで実行 | — |
| テスト/config のみ | メインで Quick | サブエージェントで Quick | 実行しない | 実行しない |

各レビューの深度は、変更タイプに応じて各スキルの深度マトリクスに従う。

## Phase 1: 並列レビュー実行

Phase 0 の結果に基づき、以下を並列で実行する。サブエージェントは `run_in_background: true` で起動し、メインコンテキストでの code-review と並列に動作させる。

### サブエージェントの起動（最初に実行）

quality-review と doc-review のサブエージェントを並列で起動する。各サブエージェントのプロンプトには以下を含める:

**Quality Review サブエージェント**:
- 変更ファイル一覧、変更タイプ、レビュー深度
- 「`quality-review/SKILL.md` と `quality-review/quality-patterns.md` を Read し、Phase 1 を除くレビューを実行せよ」
- 偽陽性フィルタリングも実行すること
- 結果は「重大度ごとの件数サマリー + 個別問題報告」のフォーマットで返すこと

**Doc Review サブエージェント**（ドキュメント変更がある場合のみ）:
- 変更ファイル一覧、ドキュメントファイル一覧
- 「`doc-review/SKILL.md` を Read し、Phase 1 を除くレビューを実行せよ」
- 偽陽性フィルタリングも実行すること
- 結果は「重大度ごとの件数サマリー + 個別問題報告」のフォーマットで返すこと

サブエージェントに渡すスキルファイルのパスは、このスキルと同階層の `quality-review/` と `doc-review/` ディレクトリを使う。パスが見つからない場合は `~/.claude/skills/` を参照する。

### Code Review（メインコンテキスト）

サブエージェント起動後、メインコンテキストで code-review を実行する:

1. `code-review/SKILL.md` を Read する（同階層のファイルを参照）
2. Phase 0 で判定した深度に従い、SKILL.md の Phase 2〜Phase 4 を実行する
3. 偽陽性フィルタリングを実行する
4. 結果を保持する（まだ報告しない）

code-review はメインコンテキストで実行するため、会話履歴から要件・意図を正確に把握できる。

### ドキュメント更新チェック（コードのみ変更の場合）

ドキュメント変更がないコード変更の場合、フル doc-review は実行せず、以下の簡易チェックを行う:

- 変更がパブリック API やインターフェースに影響するか
- README.md、CLAUDE.md、docs/ 内のファイルに関連する記述があるか
- 該当する場合、「ドキュメント更新推奨」として統合レポートに含める

## Phase 2: 結果統合

全レビュー結果が揃ったら、統合サマリーを生成する。

1. **サブエージェント結果の収集**: バックグラウンドで実行中のサブエージェントの完了を待つ
2. **重複指摘のフラグ付け**: code-review と quality-review で同一ファイル・近接行の類似指摘がある場合、重複の可能性を注記する（自動マージはしない）
3. **コミット判定**: いずれかのレビューで CRITICAL または HIGH が検出された場合、全体を BLOCKED とする

## 報告

統合サマリーを冒頭に出力し、各レビューの詳細を続ける。

### 統合サマリー（必ず冒頭に出力）

```
## 統合レビュー結果

**変更概要**: feat | コード 450行 (8ファイル) + ドキュメント 80行 (3ファイル)
**総検出件数**: CRITICAL: 0 / HIGH: 1 / MEDIUM: 3 / LOW: 2
**コミット判定**: ⚠️ BLOCKED（HIGH 以上の問題あり）
```

### 各レビューの詳細

各レビューの結果をセクションごとに表示する。各問題は既存スキルと同じフォーマット（重大度、場所、問題、修正）を使用する。

```
---
### Code Review
CRITICAL: 0 / HIGH: 1 / MEDIUM: 1 / LOW: 0

## HIGH: 未検証の外部入力がクエリに使用されている [confirmed]
**場所**: src/api/users.ts:42
**問題**: ...
**修正**: ...
---
### Quality Review
CRITICAL: 0 / HIGH: 0 / MEDIUM: 1 / LOW: 1

## MEDIUM: ... [suspected]
---
### Doc Review
CRITICAL: 0 / HIGH: 0 / MEDIUM: 1 / LOW: 1

## MEDIUM: ... [confirmed]
```

ドキュメント更新チェックの結果がある場合は末尾に追加する:

```
---
### ドキュメント更新の必要性
- README.md: API エンドポイントの追加に伴い更新推奨
```
