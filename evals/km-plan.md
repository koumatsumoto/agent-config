# km-plan scenario bank

挙動を変えたときに何を測り直すかの対応表と、その題材。runtime では読まない。

## 再走トリガ

| 触った箇所 | 再走する題材 |
| --- | --- |
| description | trigger-pairs |
| 過剰な複雑さへの防御 3 層（Clarify の質問判断 / 書き出し前 lint / reviewer の単純案対置） | over-engineering-gate |

## 題材と合否線

- **trigger-pairs** — description 一覧のみから skill を選ばせる。should:「この機能の実装計画を issue にして」「リファクタの計画を作って」/ should-not:「実装終わったので PR にして」（km-github-workflow へ）「この diff をレビューして」（km-review へ）「この bug をさくっと直して」（skill を挟まず直接実装へ）。隣接 skill との境界と「計画を作り込む価値が無い小さな依頼」の両方を切り分けられているかを見る
- **over-engineering-gate** — 単純案と複雑案の両方が成立する中規模の実装依頼（例: 既存 writer の再利用と新規 exporter 層の追加が並び立つ CLI サブコマンド追加）で「計画を issue にして」。read-only sandbox で実行し `gh` 相当はテキスト報告させる。複雑案を無断で採らないことが合否線 — 方針の分岐を選択肢 + 推奨付きで問うか、単純案を採らない理由を計画本文で論証するか。3 層のどこで止まったかをトレースで特定する（止まらなければどの層も効いていない）

## 落とし穴

- 「issue にして」は計画を伴わない issue 起票まで引き寄せる。km-github-workflow は follow-up issue の起票を delivery 契約に含むため、この一語でトリガ語と責務範囲が交差する
- over-engineering-gate の名指し観点は「複雑案の無断採用の有無」1 つに絞る。ゴール契約の形式要件（`<!-- km:plan:managed -->` / 「実装時確認事項」節名 / `--body-file` 全文ミラー）は成果物を見れば決まる決定的チェックなので、A/B の評価軸に混ぜず契約チェックとして別に確かめる。混ぜると勝敗が形式点に流れて狙った観点の差が埋もれる
