# Output Quality Rubric

レビュー skill の出力品質を評価する rubric。

## Pass 条件

- 重大度サマリーがある
- blocking 判定が severity と整合する
- false positive を抑える説明がある
- 修正提案が具体的である
- report-format と大きく矛盾しない
- 品質評価サマリー（9 品質特性テーブル）が出力に含まれる、または `（スキップ）` と明示される（quality-review 実行時 / 非実行時）
- 第三者専門家レビューのセクションが存在し、実行時は severity 形式（CRITICAL / HIGH / MEDIUM / LOW）で報告され、非実行時は `（スキップ）` と明示される
- スキップされたレビューはセクション見出しと「スキップ」が明示されている（省略は不可）

## 注目点

- `code-review`
  - lint ではなく設計とバグを見ているか
  - 高シグナルの設計リスクを拾えているか
- `quality-review`
  - diff に根拠のある品質問題だけを報告しているか
  - config/chore で safety と flexibility を落としていないか
  - `standard` / `thorough` の code change path で 9 品質特性ごとの評価（PASS / WARN / FAIL / SKIP）が出力されているか
  - `quick` や docs-only path では `（スキップ）` が妥当か
- `doc-review`
  - 事実誤認だけでなく、構造的な混乱も拾えているか
- `intent-review`
  - 推測と合意事項を混同していないか
- `第三者専門家レビュー`
  - 専門家ごとに severity 件数サマリーがあるか
  - 個別所見に重大度・場所・確信度が含まれるか
  - 専門家の所見が統合サマリーの件数合算と blocking 判定に反映されているか

## Fail 条件

- blocking すべきケースを PASS にする
- 重大度が不自然に低い
- report-format を無視する
- 未変更行や一般論ばかりを指摘する
- docs update recommendation を出すべきケースで沈黙する
- 品質評価サマリー（9 特性テーブル）が欠落している（quality-review 実行時）
- 第三者専門家レビューのセクションが欠落している、または severity 形式でない（expert review 実行時）
- 専門家の HIGH / CRITICAL が統合サマリーの blocking 判定に反映されていない
- スキップされたレビューのセクションが省略されている（「スキップ」明示なし）
