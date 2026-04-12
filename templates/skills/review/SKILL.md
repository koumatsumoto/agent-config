---
name: km:review
description: Reviews uncommitted changes end-to-end with selectable depth. Use when the user says "レビューして", "チェックして", "変更を確認して", "問題ないか見て", or asks to review or check changes, or before commit. Prefer this skill over running review subskills one by one.
---

# Review

未コミット変更を対象に、意図検証・設計実装・品質特性・第三者診断・ドキュメントの観点を統合する review orchestrator。要求されたレビュー強度に応じて `thorough` / `standard` / `quick` を選び、必要な review だけを実行する。

## レビューの目的

開発者は目の前の実装に集中するため、要件との乖離・設計上の問題・品質特性の見落とし・ドキュメントとの不整合が視野外になりやすい。このスキルは複数の review を整理して実行し、コミット前の確認コストと見落としのバランスを調整する。

## Success Criteria

- 変更タイプに応じた review 候補を正しく選ぶ
- 要求されたレベルに応じて review を絞り込む
- 下位 review に同じ仕事を重複させない
- `CRITICAL` / `HIGH`、または intent-review の `HIGH` を見逃さずにブロックする
- レポートは、実行した review とスキップした review の両方が分かる形にする

## Workflow

1. Phase 1: 変更把握とレベル選択
2. Phase 2: intent-review
3. Phase 3: code-review + quality-review + 第三者専門家レビュー
4. Phase 4: doc-review
5. Phase 5: 結果統合とコミット判定

## Phase 1: 変更把握とレベル選択

`git diff --name-only` と `git diff --stat` で変更を把握し、以下を決める:

- 変更タイプ: `feat` / `fix` / `refactor` / `test` / `config` / `chore`
- 構成: `has_code` / `has_docs`
- 会話コンテキスト: この会話内で自分が実装した変更は「自己開発」、会話履歴に実装の経緯がない変更は「他者変更」。判断がつかない場合は自己開発として扱う
- 要求レベル: `thorough` / `standard` / `quick`
- 下位 review の内部深度: `Full` / `Focused` / `Quick`

レベルの決め方:

- `深くレビューして`、`厳しめにレビューして`、`thorough review` など: `thorough`
- `浅くレビューして`、`軽くレビューして`、`quick review` など: `quick`
- 指定がない review 依頼: `standard`

### First-pass routing

まず、変更タイプと変更構成だけで review 候補を決める。

|変更の構成|intent|code|quality|expert|doc|
|---|---|---|---|---|---|
|コード + ドキュメント（自己開発）|実行候補|実行候補|実行候補|実行候補|実行候補|
|コード + ドキュメント（他者変更）|スキップ|実行候補|実行候補|実行候補|実行候補|
|コードのみ（自己開発）|実行候補|実行候補|実行候補|実行候補|更新必要性だけ確認|
|コードのみ（他者変更）|スキップ|実行候補|実行候補|実行候補|更新必要性だけ確認|
|ドキュメントのみ|スキップ|スキップ|スキップ|スキップ|実行候補|
|test / config / chore のみ|スキップ|実行候補|実行候補|スキップ|スキップ|

優先順位ルール:

- 変更タイプ routing が先で、レベルはそれを上書きしない
- レベルは、first-pass で実行候補になった review をさらに絞り込む方向にのみ作用する

代表例:

- docs-only + `standard`: `doc-review` のみ実行
- docs-only + `thorough`: `doc-review` のみ実行
- test/config/chore + `thorough`: expert review は追加しない
- code change + `quick`: `code-review` のみに絞り込む

### Level filter

次に、first-pass の実行候補に対してレベルで絞り込む。

| Level | intent-review | code-review | quality-review | expert review | doc-review |
|---|---|---|---|---|---|
| `thorough` | 条件付き実行 | 実行 | 実行 | 実行 | 条件付き実行 |
| `standard` | 条件付き実行 | 実行 | 実行 | スキップ | 条件付き実行 |
| `quick` | スキップ | 実行 | スキップ | スキップ | 原則スキップ |

補足:

- この表は、変更タイプ routing が code change の通常 path を返した場合の最大有効化セットを示す。docs-only や test/config/chore では、first-pass routing がこの表より狭い集合を返す
- `quick` の `code-review` のみという原則は code change path に対して適用する
- docs-only 変更では `quick` でも `doc-review` を実行する
- 下位 review が起動された場合、その内部深度は従来どおり変更タイプごとの `Full` / `Focused` / `Quick` テーブルに従う。`standard + test/config/chore` の quality-review も `Quick` のままとする

## Phase 2: intent-review

`thorough` と `standard` で、かつ会話履歴から要求を復元できる場合のみ、メインコンテキストで `intent-review/SKILL.md` を Read して実行する。復元できない場合は推測せず、`intent-review skipped: no usable conversation context` と記録する。

intent-review の構造化出力は `intent-review/SKILL.md` の Phase 2 で定義されたフォーマットに従う。この結果は Phase 3 の偽陽性フィルタリングおよび expert review への要求背景共有で使用する。

## Phase 3: code-review + quality-review + 第三者専門家レビュー

Phase 2 完了後に、first-pass routing と level filter の結果として必要になった review だけを可能な限り並列で起動する。

### サブエージェントへの共通コンテキスト

全サブエージェントのプロンプトに以下を含める:

- 変更ファイル一覧、変更タイプ、選択レベル、下位 review の内部深度
- Phase 2 の intent-review 結果（実行された場合のみ）— 要求リストと合意事項。サブエージェントはこれを偽陽性フィルタリングの「意図的な変更」判定に使用する

### code-review + quality-review

- `code-review`: `code-review/SKILL.md` と `code-review/report-format.md` を Read してレビューする
- `quality-review`: `quality-review/SKILL.md`、`quality-review/quality-checklist.md`、`quality-review/report-format.md` を Read してレビューする。判断に迷ったら `quality-review/reference/` 配下の該当ファイルを参照する

Phase 1 の変更把握はオーケストレーターが実施済みのため、サブエージェントではスキップする。代わりに、共通コンテキストで提供する変更ファイル一覧・変更タイプ・選択レベル・内部深度を使用する。

- 各下位 review は「重大度ごとの件数サマリー + 個別問題報告」で返させる
- `quality-review` は上記に加えて「品質評価サマリー（9 品質特性ごとの評価テーブル）」も返させる

### 第三者専門家レビュー

expert review は `thorough` でのみ実行する。変更タイプ routing が expert review を候補に含める path では、`fix` を含めてサイズ閾値を無視し常時実行する。変更タイプ routing が expert を候補に含めない path（docs-only、test/config/chore）には影響しない。

目的は、内部レビューの前提知識や慣れに起因する盲点を補うこと。

### 専門家の構成

デフォルトは 2 名のサブエージェントで実施する。専門家は変更内容に応じて追加・変更してもよいが、その場合はサブエージェント起動前にロール定義と重点確認観点を事前に明確にすること。

1. **セキュリティ専門家**: 攻撃者の視点でコードを診断する。認証・認可の抜け穴、インジェクション経路、情報漏えい、暗号の不適切な使用を重点的に確認する
2. **シニア QA アーキテクト**: システムが適切に動作するかの視点で診断する。エッジケース、異常系の振る舞い、状態遷移の整合性、通常見落とされがちな境界条件や競合状態を重点的に確認する

### 専門家サブエージェントの起動

各専門家サブエージェントのプロンプトには以下の 3 要素を必ず含める:

1. **ロール定義**: 専門家の役割と重点確認観点
2. **レビュー対象**: コード差分、変更ファイル一覧、要求背景
3. **出力形式**: `code-review/report-format.md` と同じ形式で報告させる — 重大度ごとの件数サマリー（CRITICAL / HIGH / MEDIUM / LOW）+ 個別所見（重大度 + 場所 + 問題 + 確信度）

### 専門家への提供情報

各専門家には以下を渡す:

- コード差分と変更ファイル一覧
- 要求背景の要約（Phase 2 の intent-review 結果がある場合）
- 既知の設計制約（会話コンテキストから得られる場合）

以下は意図的に提供しない:

- code-review / quality-review の結果
- 会話履歴の詳細

## Phase 4: doc-review

コード change を含む場合は、Phase 3 の全サブエージェント完了後に doc 関連の確認を行う。docs-only 変更では doc-review を main review として扱う。

- ドキュメント変更がある場合: `doc-review/SKILL.md` と `doc-review/report-format.md` を Read してサブエージェントで実行する。必要なら Phase 3 と同様の共通コンテキストも渡す
- コードのみ変更の場合: フル doc-review は実行せず、オーケストレーター自身がメインコンテキストで以下を確認する
  - パブリック API、CLI、設定、インターフェースの変更があるか
  - `README.md`、`CLAUDE.md`、`AGENTS.md`、`docs/` に関連記述があるか
  - 該当する場合は「ドキュメント更新推奨」を統合レポートに含める

## Phase 5: 結果統合

統合時のルール:

1. 統合サマリーに選択レベルを含める
2. 全レビュー（Phase 3 の下位レビュー + expert review）の重大度ごとの件数を合算する。intent-review は CRITICAL を持たないため、合算時の CRITICAL は常に 0 として扱う
3. 同一ファイル・近接行の類似指摘は重複の可能性を注記する
4. いずれかのレビューで `CRITICAL` または `HIGH` があれば `BLOCKED` とする
5. quality-review を実行した場合は、品質評価サマリーをそのまま含める
6. docs 更新推奨がある場合は末尾に独立セクションで追加する
7. ルーティングでスキップされたレビューは、セクション見出しと `（スキップ）` を出力する。セクション自体を省略しない
8. サブエージェントが結果を返さなかった場合は、該当レビューを `（実行失敗）` として記録し、失敗理由を統合レポートに含める

## 指摘対応の方針

検出された指摘は `LOW` を含め原則すべて対応する。以下の場合のみユーザーに判断を委ねる:

- 大規模な修正が必要で影響範囲が広い
- 仕様変更を伴う
- 設計判断のトレードオフがある

出力形式は `report-format.md` を参照。
