# Output Quality Rubric

レビュー skill の出力品質を評価する rubric。

## Pass 条件

- 重大度サマリーがある
- blocking 判定が severity と整合する
- false positive を抑える説明がある
- 修正提案が具体的である
- report-format と大きく矛盾しない

## 注目点

- `code-review`
  - lint ではなく設計とバグを見ているか
  - 高シグナルの設計リスクを拾えているか
- `quality-review`
  - diff に根拠のある品質問題だけを報告しているか
  - config/chore で safety と flexibility を落としていないか
- `doc-review`
  - 事実誤認だけでなく、構造的な混乱も拾えているか
- `intent-review`
  - 推測と合意事項を混同していないか

## Fail 条件

- blocking すべきケースを PASS にする
- 重大度が不自然に低い
- report-format を無視する
- 未変更行や一般論ばかりを指摘する
- docs update recommendation を出すべきケースで沈黙する
