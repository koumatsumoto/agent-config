# km-plan scenario bank

## trigger-pairs: description 発火対

- 対象層: description（トリガー）— 発火境界の健全性ゲート
- 題材: description 一覧のみを与えて skill を選ばせる。should:「この機能の実装計画を issue にして」「リファクタの計画を作って」/ should-not:「実装終わったので PR にして」（km-github-workflow へ）「この diff をレビューして」（km-review へ）「この bug をさくっと直して」（skill を挟まず直接実装へ）
- 期待品質: should の 2 件で km-plan が選ばれ、should-not の 3 件では選ばれない。トリガ語を 2 つに絞った description が、隣接 skill（km-github-workflow / km-review）との境界と「計画を作り込む価値が無い小さな依頼」の両方を切り分けられているか
- 判定: 健全性ゲートとして確立（2026-07-26, #183 後の実走）。should 2 件・should-not 3 件すべて期待どおりに分岐し、トリガ語を 2 つへ絞った description でも under-trigger は起きなかった。description を変えるたびに必ず再走する
- トレードオフ / 注記: 「issue にして」が計画を伴わない issue 起票まで引き寄せる。km-github-workflow は follow-up issue の起票を自分の delivery 契約に含むため、トリガ語と責務範囲がこの一語で交差する。誤射の実害が観測されたら「計画を issue にして」へ絞ることを検討する

## over-engineering-gate: 過剰に複雑な設計方針を無断で採らないか

- 対象層: 過剰な複雑さへの防御 3 層（Clarify の質問判断 / 書き出し前 lint の「より単純な方針」/ reviewer の単純案対置）
- 題材: 単純案と複雑案の両方が成立する中規模の実装依頼（例: 既存 writer を再利用する案と、新規 exporter 層を挟む案が並び立つ CLI サブコマンド追加）で「計画を issue にして」。read-only sandbox で実行し、`gh` 相当のコマンドはテキストとして報告させる
- 期待品質: 複雑案を無断で採らない。方針の分岐を選択肢 + 推奨付きでユーザに問うか、単純案を採らない理由を計画本文で論証するか、どちらか。3 層のどこで止まったかをトレースで特定する（止まらなければどの層も効いていない）
- 判定: 新設・未走。初回の運用テスト結果をここに記録する
- トレードオフ / 注記: 名指し観点は「複雑案の無断採用の有無」1 つに絞る。ゴール契約の形式要件（`<!-- km:plan:managed -->` / 「実装時確認事項」節名 / `--body-file` 全文ミラー）は成果物を見れば決まる決定的チェックなので、A/B の評価軸に混ぜず契約チェックとして別に確かめる。混ぜると勝敗が形式点に流れて、狙った観点の差が埋もれる
