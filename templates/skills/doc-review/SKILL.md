---
name: km:doc-review
description: Reviews uncommitted documentation changes for structure, cross-document consistency, and factual accuracy. Use for docs-focused review when the orchestrator is not the right entry point.
disable-model-invocation: true
---

# Document Review

未コミットのドキュメント変更を対象に、構造、横断整合性、正確性をレビューする。

## Success Criteria

- 変更された文書だけでなく、その周辺文書との整合を確認する
- 事実関係は一次情報まで戻って確認する
- 読者を迷わせる構造上の欠陥と更新漏れを優先して拾う

## Workflow

1. 変更を把握して深度を決める
2. ドキュメント内整合性を確認する
3. 関連文書との整合性を確認する
4. 一次情報で正確性を検証する
5. 偽陽性を落として報告する

## Phase 1: 変更把握

`git diff --name-only` で変更ファイルを集める。コードのみ変更なら本スキルは使わない。

|ドキュメントタイプ|Phase 2|Phase 3|Phase 4|
|---|---|---|---|
|README / ガイドライン / ルール|Full|Full|Full|
|要件ドキュメント|Full|Full|Focused|
|仕様書|Focused|Focused|Full|
|アーキテクチャ / 設計書|Full|Full|Focused|
|設定ドキュメント / 手順書|Quick|Focused|Full|

## Phase 2: ドキュメント内整合性

差分だけでなく、変更された文書全体を読む。重点は以下:

- セクション構成と論理の流れ
- 見出し、目次、本文の対応
- 用語と表記の統一
- 前提条件、警告、手順の抜け漏れ
- ゼロベースの読者にとっての明瞭性

## Phase 3: ドキュメント間整合性

関連する README、ルール、docs 配下を探し、以下を確認する:

- 重複管理による矛盾
- 一方だけ更新された古い説明
- 内部リンク、相対パス、アンカーの破綻
- 用語定義や手順のズレ

## Phase 4: 一次情報による正確性検証

まず repo 内の実装、設定、ヘルプ出力を確認し、それで足りない場合だけ外部一次情報を当たる。重点は以下:

- API や実装コードと説明が一致しているか
- コマンドや設定値が現行仕様と一致しているか
- 非推奨や期限切れ表現が残っていないか
- 外部リンク先が有効で、内容が矛盾していないか

## Phase 5: 偽陽性フィルタリング

以下は除外する:

- 今回の変更で導入されていない既存問題
- 単なる文体の好み
- 読者層に合わせた意図的な簡略化
- 自動生成コンテンツだけの差分
- 未変更セクションだけに対する指摘

## 判定

- `CRITICAL`: 危険な手順や破壊的な誤情報
- `HIGH`: 明確な事実誤認、一次情報との不一致、構造破綻
- `MEDIUM`: 整合性不足、曖昧さ、更新漏れ
- `LOW`: 微小改善

明確な事実誤認ではなくても、構造上の違和感や読者を迷わせる構成問題が実害を持つ場合は `MEDIUM` として報告する。

`CRITICAL` または `HIGH` があればコミットをブロックする。出力形式は `report-format.md` を参照。
