---
name: km:review
description: Comprehensive review orchestrator that coordinates intent-review, code-review, quality-review, and doc-review based on change type and context. Use when the user requests any kind of review, says "レビューして", "チェックして", "変更を確認して", "問題ないか見て", or after completing code changes. Runs intent review in main context, then delegates code/quality/doc reviews to parallel sub-agents.
---

# Review

未コミット変更を対象に、意図検証・設計実装・品質特性・ドキュメントの4軸で包括的なレビューを行うオーケストレーター。

intent-review はメインコンテキストで実行し（会話履歴へのアクセスが必要なため）、その結果をサブエージェントに橋渡しして code-review / quality-review / doc-review を並列実行する。

| レビュー | 観点 | 実行方式 |
|---------|------|---------|
| `/km:intent-review` | 要件充足・意図の検証 | メインコンテキスト（条件付き） |
| `/km:code-review` | 設計・バグ・コード品質 | サブエージェント（並列） |
| `/km:quality-review` | ISO/IEC 25010:2023 の9品質特性を Tier 運用で確認 | サブエージェント（並列） |
| `/km:doc-review` | 構造整合性・横断整合性・正確性 | サブエージェント（並列） |

## Workflow

1. **Phase 1: 変更把握・ルーティング** — 変更を分類し、実行するレビューとその深度を決定する
2. **Phase 2: 意図検証** — 会話コンテキストがあれば intent-review をメインで実行する
3. **Phase 3: 並列レビュー実行** — code/quality/doc-review をサブエージェントで並列実行する
4. **Phase 4: 結果統合** — 全レビュー結果を統合サマリーにまとめ、コミット判定を行う

## Phase 1: 変更把握・ルーティング

`git diff --name-only` で変更ファイルを収集し、以下を判定する:

1. **変更タイプ**: feat / fix / refactor / test / config
2. **変更の構成**: コード変更あり (`has_code`) / ドキュメント変更あり (`has_docs`)
3. **コンテキスト有無**: 今回の変更が会話内で開発されたものか（自己レビュー）、外部からのコードか（他者レビュー）
4. **変更規模**: 変更行数、ファイル数

判定結果に基づき、実行するレビューを決定する:

| 変更の構成 | intent-review | code-review | quality-review | doc-review |
|---|---|---|---|---|
| コード + ドキュメント（自己開発） | メインで実行 | サブエージェント | サブエージェント | サブエージェント |
| コード + ドキュメント（他者コード） | スキップ | サブエージェント | サブエージェント | サブエージェント |
| コードのみ（自己開発） | メインで実行 | サブエージェント | サブエージェント | ドキュメント更新チェックのみ |
| コードのみ（他者コード） | スキップ | サブエージェント | サブエージェント | ドキュメント更新チェックのみ |
| ドキュメントのみ | スキップ | 実行しない | 実行しない | サブエージェントで実行 |
| テスト/config のみ | スキップ | サブエージェント(Quick) | サブエージェント(Quick) | 実行しない |

## Phase 2: 意図検証（メインコンテキスト、条件付き）

会話コンテキストが存在する場合（自分が開発した変更のレビュー時）のみ実行する。

1. `intent-review/SKILL.md` を Read する
2. SKILL.md の指示に従い、要求の復元と充足判定を行う
3. 結果を以下の構造化形式で保持する（Phase 3 でサブエージェントに橋渡しするため）:

```
### 要求リスト
1. [明示的] ...
2. [合意] ...

### 合意された設計判断
- ...
```

会話コンテキストがない場合（他者のコードをレビューする場合）は、この Phase をスキップし「コンテキストなし: intent-review スキップ」と記録して Phase 3 に進む。

## Phase 3: 並列レビュー実行

Phase 1 の結果に基づき、サブエージェントを `run_in_background: true` で並列起動する。

### サブエージェントへの共通コンテキスト

全サブエージェントのプロンプトに以下を含める:
- 変更ファイル一覧、変更タイプ、レビュー深度
- Phase 2 の intent-review 結果（実行された場合のみ）— 要求リストと合意事項。サブエージェントはこれを偽陽性フィルタリングの「意図的な変更」判定に使用する

### Code Review サブエージェント

- `code-review/SKILL.md` を Read し、Phase 1 を除くレビューを実行するよう指示
- 結果は「重大度ごとの件数サマリー + 個別問題報告」で返すこと

### Quality Review サブエージェント

- `quality-review/SKILL.md` と `quality-review/quality-patterns.md` を Read し、Phase 1 を除くレビューを実行するよう指示
- 品質特性は ISO/IEC 25010:2023 の 9 特性を前提とし、Tier 1 は常時、Tier 2/3 は変更タイプと変更内容に応じて適用すること
- `Quick` 指定時は quality-review 側で定義された優先観点に絞って確認し、根拠の弱い推測は報告しないこと
- 結果は「重大度ごとの件数サマリー + 個別問題報告」で返すこと

### Doc Review サブエージェント（ドキュメント変更がある場合）

- `doc-review/SKILL.md` を Read し、Phase 1 を除くレビューを実行するよう指示
- 結果は「重大度ごとの件数サマリー + 個別問題報告」で返すこと

### ドキュメント更新チェック（コードのみ変更の場合）

フル doc-review は実行せず、メインコンテキストで簡易チェックを行う:
- 変更がパブリック API やインターフェースに影響するか
- README.md、CLAUDE.md、docs/ 内のファイルに関連する記述があるか
- 該当する場合、「ドキュメント更新推奨」として統合レポートに含める

サブエージェントに渡すスキルファイルのパスは、このスキルと同階層のディレクトリを使う。パスが見つからない場合は `~/.claude/skills/` を参照する。

## Phase 4: 結果統合

全レビュー結果が揃ったら、統合サマリーを生成する。

1. **サブエージェント結果の収集**: バックグラウンドで実行中のサブエージェントの完了を待つ
2. **重複指摘のフラグ付け**: code-review と quality-review で同一ファイル・近接行の類似指摘がある場合、重複の可能性を注記する
3. **コミット判定**: いずれかのレビューで CRITICAL または HIGH が検出された場合、全体を BLOCKED とする

## 報告

### 統合サマリー（必ず冒頭に出力）

```
## 統合レビュー結果

**変更概要**: feat | コード 450行 (8ファイル) + ドキュメント 80行 (3ファイル)
**総検出件数**: CRITICAL: 0 / HIGH: 1 / MEDIUM: 3 / LOW: 2
**コミット判定**: ⚠️ BLOCKED（HIGH 以上の問題あり）
```

### 各レビューの詳細

各レビューの結果をセクションごとに表示する。

```
---
### Intent Review
（スキップ / または結果を表示）
---
### Code Review
CRITICAL: 0 / HIGH: 1 / MEDIUM: 1 / LOW: 0

## HIGH: [問題タイトル] [confirmed]
**場所**: src/api/users.ts:42
**問題**: ...
**修正**: ...
---
### Quality Review
CRITICAL: 0 / HIGH: 0 / MEDIUM: 1 / LOW: 1
---
### Doc Review
CRITICAL: 0 / HIGH: 0 / MEDIUM: 1 / LOW: 1
```

ドキュメント更新チェックの結果がある場合は末尾に追加する:

```
---
### ドキュメント更新の必要性
- README.md: API エンドポイントの追加に伴い更新推奨
```
