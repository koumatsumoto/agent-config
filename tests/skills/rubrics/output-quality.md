# Output Quality Rubric

`km:review` の出力品質を評価する rubric。

## Pass 条件

- 統合サマリーに実行レベル・対象スコープ・変更概要・総検出件数・コミット判定が含まれる
- 重大度サマリーがある
- BLOCKED / PASS 判定が severity と整合する (`CRITICAL` または `HIGH` で BLOCKED)
- 偽陽性を抑える根拠説明がある (確信度ラベル `confirmed` / `likely` / `possible`)
- 修正提案が具体的である (どこを / どう直すかが分かる)
- `templates/skills/review/report-format.md` の形式と大きく矛盾しない
- スキップされた Phase はセクション見出しと「スキップ」が明示されている (省略は不可)
- Phase 4 が `need-check` モードで実行された場合はそのことが分かる表記がある

## Phase ごとの注目点

- **Phase 2 (Code Review generalist)**
  - lint ではなく設計とバグを見ているか
  - 高シグナルの設計リスクを拾えているか
  - 関数 / モジュール / システム境界 の 3 層を網羅しているか
- **Phase 3 (3 専門家並列)**
  - `thorough` 指定時に architect / qa / security の 3 名すべてが起動しているか
  - 3 名が **同一 turn 内に並列発行** されているか (sequential 発行になっていないか)
  - 専門家ごとに severity 件数サマリーがあるか
  - 個別所見に重大度・場所・観点 (担当 ISO 副特性)・確信度が含まれるか
  - **architect**: 長期・横断・非機能視点に集中しているか (Phase 2 の code-level 指摘を蒸し返していないか)
  - **qa**: 異常系・境界・運用品質に集中しているか
  - **security**: 脅威モデル・攻撃面に集中しているか
- **Phase 4 (Doc Review)**
  - 事実誤認だけでなく、構造的な混乱も拾えているか
  - `need-check` モード時に MEDIUM 以下に降格されているか
  - docs-only 変更で Phase 4 full モードのみ実行されているか
- **Phase 5 (統合)**
  - 全 Phase の指摘が重大度ごとに合算されているか
  - 重複指摘の可能性が注記されているか
  - blocking 判定が全 Phase 横断で行われているか

## Fail 条件

- BLOCKED すべきケースを PASS にする
- 重大度が不自然に低い (例: 認証バイパスを MEDIUM にする)
- 未変更行や一般論ばかりを指摘する
- スキップされた Phase のセクションが省略されている (「スキップ」明示なし)
- `thorough` 指定なのに Phase 3 を起動していない
- Phase 3 の 3 専門家が sequential 発行になっている (並列発行されていない)
- Phase 4 を Phase 3 と並走させている (Phase 3 完了後の sequential 実行が原則)
- Phase 2 と Phase 3 architect の指摘が大量に重複している (`scope-alignment.md` の住み分けが守られていない)
- docs update recommendation を出すべきケースで沈黙する
- 接点変更がないのに WCAG 2.2 やブラウザ固有の指摘を出す
- LLM/AI 機能の変更があるのに Security 専門家が prompt injection 観点を見ていない

## km:review-loop 特有

### Pass 条件
- 完了報告に **loop 回数 / 受け入れ済みリスク / 修正サマリー (CRITICAL/HIGH/MEDIUM/LOW 件数)** が含まれる
- Phase C PASS ルートで累積 MEDIUM/LOW を自動修正した後、**km:review 再検証** が走ったことが分かる (修正対象ゼロでスキップした場合はその旨明示)
- ループ上限到達 / 収束しない場合に **判断 3 択 (受け入れ / 再起動 / 中止)** を提示する
- 受け入れ済みリスクは「重大度 / 残す理由 / 後続対応条件」を明示

### Fail 条件
- 自動修正で新規 HIGH を埋め込んだまま PASS と報告する (Phase C 再検証が走っていない)
- ループ上限到達時にユーザ判断を仰がず自動継続する
- 例外条項該当指摘を「受け入れ済みリスク」と明示せずスキップする
- 完了報告の重大度件数がプレースホルダのまま (`<count>` が残る)
