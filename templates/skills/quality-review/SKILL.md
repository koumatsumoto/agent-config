---
name: km:quality-review
description: Reviews uncommitted changes against ISO/IEC 25010:2023 quality characteristics. Use for targeted security, reliability, performance, or maintainability review when the orchestrator is not the right entry point.
disable-model-invocation: true
---

# Quality Review

未コミット変更を対象に、ISO/IEC 25010:2023 の品質特性でレビューする。diff から直接裏づけられる問題を優先し、根拠の弱い推測は扱わない。

## Success Criteria

- セキュリティ、信頼性、性能、保守性の実害を伴う問題を優先する
- 変更タイプに応じて見る特性を絞り、過剰レビューを避ける
- diff から根拠が見える問題だけを報告する

## Workflow

1. 変更を分類してレビュー深度を決める
2. `quality-patterns.md` を読み、該当する特性だけ確認する
3. 偽陽性を落として報告する

## Phase 1: 変更把握

`git diff --name-only` で変更ファイルを集める。docs-only なら本スキルは使わない。

|変更タイプ|Tier 1|Tier 2|
|---|---|---|
|feat|Full|Full|
|fix|Focused|Focused|
|refactor|Focused|Focused|
|test|Quick|Quick|
|config / chore|Quick|Quick|

Quick の優先観点:

- `test`: 保守性、信頼性、危険な緩和
- `config / chore`: セキュリティ、信頼性、性能、互換性、安全性、柔軟性

## Phase 2: 品質特性レビュー

開始前に必ず `quality-patterns.md` を読む。そこに詳細な確認パターンがある。

確認の優先順位:

1. Tier 1: 常に確認
   - セキュリティ
   - 信頼性
   - 性能効率性
   - 保守性
2. Tier 2: 変更タイプと変更内容に応じて確認
   - 互換性
   - 安全性
   - 機能適合性
   - 柔軟性
3. Tier 3: 接点変更があるときだけ確認
   - インタラクション能力

特性ごとの判断は次の原則に従う:

- 変更差分に直接現れているか
- 同一変更セットから裏づけできるか
- 今回の修正で実害が生じるか

## Phase 3: 偽陽性フィルタリング

以下は除外する:

- 既存問題
- linter や型チェッカーで閉じる問題
- 合意済みの設計判断
- 未変更行だけに対する指摘
- diff から裏づけられない推測
- 些末な改善論

## 判定

- `CRITICAL`: 即時悪用可能、または重大インシデントに直結
- `HIGH`: 明確なバグ、仕様回帰、危険な入力検証不足
- `MEDIUM`: 保守性低下、設計不整合、不十分なエラー処理
- `LOW`: 小さな改善

`CRITICAL` または `HIGH` があればコミットをブロックする。出力形式は `report-format.md` を参照。
