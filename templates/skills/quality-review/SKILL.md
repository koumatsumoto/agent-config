---
name: km:quality-review
description: Reviews uncommitted changes against ISO/IEC 25010:2023 quality characteristics. Use for targeted security, reliability, performance, or maintainability review when the orchestrator is not the right entry point.
disable-model-invocation: true
---

# Quality Review

未コミット変更を対象に、ISO/IEC 25010:2023 の品質モデルに基づく品質レビューを行う。

## レビューの目的

開発者は「仕様どおりに動くか」に集中しがちで、品質特性（セキュリティ・信頼性・性能効率性・保守性・機能適合性など）は視野外になりやすい。本スキルはこれらを体系的かつ徹底的に確認する。diff から直接検出可能な観点を重視しつつ、同一変更セットから合理的に裏づけられる問題も見逃さない。

## ファイル構成

- `quality-checklist.md`: レビュー実行時に使用するチェックシート。Tier 1/2/3 の重みづけでチェック項目を定義する。レビューはこのチェックシートをベースに進め、結果を報告する
- `reference/`: 品質特性ごとの網羅的リファレンス（9 ファイル）。副特性ごとにアンチパターンと確認観点を詳述する。チェックシートの判断に迷ったときに参照する

## Success Criteria

- セキュリティ、信頼性、性能、保守性を中心に実害を伴う問題を網羅的に検出する
- チェックシートをベースに観点漏れなくレビューする
- diff と同一変更セットから裏づけられる問題を報告する。根拠の弱い推測は除外する
- 9 品質特性ごとの評価サマリーを出力し、品質の健全性に関するインサイトを提供する

## Workflow

1. 変更を分類してレビュー深度を決める
2. **必ず `quality-checklist.md` を Read する**（レビューはチェックシートをベースに進める。Read せずに Phase 2 に進んではならない）
3. チェックシートに沿って品質特性をレビューする。判断に迷ったら `reference/` 配下の該当ファイルを Read する
4. 偽陽性を落として報告する

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

- `test`: 保守性（試験性）、信頼性（失敗パス・時刻依存・モック境界）、セキュリティ（危険な緩和）
- `config / chore`: セキュリティ、信頼性、性能、互換性、安全性、柔軟性

## Phase 2: 品質特性レビュー

`quality-checklist.md` のチェック項目を順に確認する。

- **Tier 1**（セキュリティ, 信頼性, 性能効率性, 保守性）: 常に全項目を確認する
- **Tier 2**（互換性, 安全性, 機能適合性, 柔軟性）: 変更内容に応じて確認する。以下の条件で SKIP とする:
  - 互換性: 公開 API・CLI・DB スキーマ・設定フォーマットの変更がない場合
  - 安全性: ユーザー入力処理・外部システム連携・破壊的操作の変更がない場合
  - 機能適合性: 機能の追加・変更がない場合（純粋なリファクタリングなど）
  - 柔軟性: 環境依存・デプロイ・設定・外部依存の変更がない場合
- **Tier 3**（インタラクション能力）: ユーザー/運用者接点の変更があるときだけ確認する

チェック項目の判断に迷ったら、`reference/` 配下の該当ファイルを Read して詳細パターンを確認する:

| 特性 | リファレンスファイル |
|------|---------------------|
| 機能適合性 | `reference/1-functional-suitability.md` |
| 性能効率性 | `reference/2-performance-efficiency.md` |
| 互換性 | `reference/3-compatibility.md` |
| インタラクション能力 | `reference/4-interaction-capability.md` |
| 信頼性 | `reference/5-reliability.md` |
| セキュリティ | `reference/6-security.md` |
| 保守性 | `reference/7-maintainability.md` |
| 柔軟性 | `reference/8-flexibility.md` |
| 安全性 | `reference/9-safety.md` |

特性ごとの判断は次の原則に従う:

- 変更差分に直接現れているか
- 同一変更セットから裏づけできるか
- 今回の修正で実害が生じるか

## Phase 3: 偽陽性フィルタリング

以下は除外する:

- 既存問題（今回の変更で導入されたものではない）
- linter や型チェッカーで閉じる問題
- 合意済みの設計判断
- 未変更行だけに対する指摘
- diff から裏づけられない推測

## 判定

- `CRITICAL`: 即時悪用可能、または重大インシデントに直結
- `HIGH`: 明確なバグ、仕様回帰、危険な入力検証不足
- `MEDIUM`: 保守性低下、設計不整合、不十分なエラー処理
- `LOW`: 小さな改善

`CRITICAL` または `HIGH` があればコミットをブロックする。検出された指摘は `LOW` を含め原則すべて対応する。影響が大きい修正のみユーザーに判断を委ねる。

## 品質評価サマリー

通常のレポート（HIGH/MEDIUM/LOW の個別問題報告）に加えて、**9 品質特性ごとの評価サマリー**を必ず出力する。これは問題が検出されなかった特性も含む。目的は、人間がこの変更の品質健全性を俯瞰的に把握するためのインサイトを提供すること。

形式:

| 特性 | 評価 | 所見 |
|------|------|------|
| 機能適合性 | PASS / WARN / FAIL / SKIP | 2-3 文の定性評価 |
| 性能効率性 | PASS / WARN / FAIL | |
| 互換性 | PASS / WARN / FAIL / SKIP | |
| インタラクション能力 | PASS / WARN / FAIL / SKIP | |
| 信頼性 | PASS / WARN / FAIL | |
| セキュリティ | PASS / WARN / FAIL | |
| 保守性 | PASS / WARN / FAIL | |
| 柔軟性 | PASS / WARN / FAIL / SKIP | |
| 安全性 | PASS / WARN / FAIL / SKIP | |

- **PASS**: 問題なし。確認した範囲で品質は健全
- **WARN**: MEDIUM 以下の問題あり。改善の余地がある
- **FAIL**: HIGH 以上の問題あり。対応が必要
- **SKIP**: 変更タイプに応じてレビュー対象外

出力形式の詳細は `report-format.md` を参照。
