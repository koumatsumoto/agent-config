---
name: km:code-review
description: Reviews uncommitted code changes for design issues, bugs, and project-rule drift. Use for targeted code review when the orchestrator is not the right entry point.
disable-model-invocation: true
---

# Code Review

未コミット変更を対象に、設計・実装・規約準拠の観点でレビューする。要件充足は `/km:intent-review`、品質特性は `/km:quality-review` の責務。

## Success Criteria

- diff から裏づけられる設計問題とバグを優先して拾う
- lint や formatter に任せるだけの指摘を減らす
- プロジェクト固有ルールと既存コメントの重要な制約を見落とさない

## Workflow

1. 変更を把握してレビュー深度を決める
2. 設計・実装を確認する
3. 規約・コメント・可読性を確認する
4. 偽陽性を落として報告する

## Phase 1: 変更把握

`git diff --name-only` で変更ファイルを集める。docs-only なら本スキルは使わない。

|変更タイプ|レビュー深度|
|---|---|
|feat|Full|
|fix|Focused|
|refactor|Full|
|test|Quick|
|config / chore|Quick|

## Phase 2: 設計・実装

関数、モジュール、システム境界の順に確認する。重点は以下:

- 型・null 安全性、境界条件、エラーパス
- 責務分離、依存方向、公開 API の漏れ
- 信頼境界を跨ぐ入力検証とレイヤー境界の破れ
- 明確な回帰や off-by-one、共有状態の誤用

## Phase 3: 規約・可読性

以下に限定して確認する:

- `CLAUDE.md` や repo ルールに書かれた実質的な制約
- 変更対象ファイル内の既存コメントや TODO の重要な指示
- 意図が伝わる命名、過度なネスト、不要な複雑性

純粋な好み、機械的に直せるスタイル、未変更行への一般論は優先しない。

## Phase 4: 偽陽性フィルタリング

以下は原則除外する:

- 今回の差分で入っていない既存問題
- linter、型チェッカー、formatter が拾うべきだけの問題
- 合意済みの設計判断
- 未変更行だけに対する指摘
- シニアレビューとして弱い、些末な指摘

## 判定

- `CRITICAL`: 即時悪用可能な欠陥
- `HIGH`: 明確なバグ、仕様回帰、危険な入力検証不足
- `MEDIUM`: 設計不整合、保守性低下、テスト不足
- `LOW`: 小さな改善

`CRITICAL` または `HIGH` があればコミットをブロックする。出力形式は `report-format.md` を参照。
