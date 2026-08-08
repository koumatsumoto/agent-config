# km-review scenario bank

routing・収束・独立性の load-bearing 経路を押さえる題材。runtime 規則の正本は skill 本体で、ここは検証用の記憶。

## minor-main-only: 軽微変更を独立レビュア 0 名で閉じる

- 対象層: 常時起動契約・0 名 routing・non-blocking の扱い
- 題材: usage 文字列への説明追加 + ローカル変数のリネーム（既存テストが両分岐を直接押さえている小 repo の未コミット差分）
- 期待品質: km-review を通したうえで 0 名を選ぶ。0 名の根拠を行数や docs-only ではなく**局所性・可逆性・material surface 不変・直接検証**で言語化する。LOW 級の指摘が出ても non-blocking のまま `PASS` にする
- 判定: 期待どおり（2026-08-08, #197）。0 名 + 4 条件の逐一言語化 + LOW 1 件を non-blocking で残した `PASS`。0 名でも `dispatch.md` と `contract.md` を読み込んでいたため、skill 側へ「0 名なら dispatch と role file を読まない」を明示した

## reliability-degradation: 既存の正常挙動のデグレード

- 対象層: role selector（reliability）・main の修正後に残るリスクへの独立性
- 題材: 「毎回 JSON を parse していたのでパス単位のキャッシュを入れた」。無効化が無く、運用者が設定ファイルを編集しても反映されない（docstring が謳う無停止リロードを壊す）。キャッシュ済み dict を参照で返すので呼び出し元の変更が全体へ波及する
- 期待品質: 残存リスクが runtime 挙動に集約されるとして `reliability` 1 名を選び、security hard route は不成立と判断する。仕込んだデグレードを捕捉する
- 判定: 期待どおり（2026-08-08, #197）。両方を HIGH で捕捉して main が修正し、**main の修正自体（deepcopy 版）が元コードより遅いという回帰を独立レビュアが捕捉**した。main の修正後候補を独立に見る順序が効いた実例。blocker 修正後は fresh reliability 1 名で recheck して `PASS`、MEDIUM は non-blocking で残置
- トレードオフ / 注記: レポート出力先を `.km-review/uncommitted/` でなく `.km-review/` 直下へ平坦化した。recheck がセッションをまたいで参照する固定パスなので、skill 側の表記を literal な例示へ変えた

## security-hard-route: trust boundary の変更で security を外さない

- 対象層: security hard route・main が修正した finding の severity 可視化
- 題材: 所有者チェックを通る既存ダウンロード経路の隣に、共有トークンを非空判定するだけの新経路を足す（他人のレポートを取得できる認可迂回）
- 期待品質: 変更の**意味**（テナント別データへの新しい認可経路）で hard route を発火させ `security` を選ぶ。仕込んだ迂回を捕捉する。main が修正しても severity 件数から消さない
- 判定: 期待どおり（2026-08-08, #197）。main が CRITICAL で捕捉・修正し、`resolved` として severity 件数へ残したまま未解決 blocker 0 で `PASS`。独立 security は formal finding 0 件（正常結果）で、判定保留として挙げた `None` 通過を main が検証して LOW で閉じた

## dual-role-max-two: 直交する 2 リスクだけ 2 名

- 対象層: 2 名 routing の例外条件・三人目を足さない上限
- 題材: ジョブキューの永続化。payload（`auth_token` を含むと README が明記）を新しい永続 sink とログへ流し、同時に非アトミック書き込み・ロック無しで既存の投入を失う
- 期待品質: role ごとに 1 行の理由を付けて 2 名だけ選び、三人目を同一ラウンドへ足さない。単一 lane では代替できないことを示す
- 判定: 期待どおり（2026-08-08, #197）。`security`（秘密を含む payload の新しい永続先・env 由来のパス）+ `reliability`（成果が未検証の並行機構に依存）の 2 名で、三人目なし。両者とも main の修正後候補に対して実所見を返した
- トレードオフ / 注記: この走では main の修正で構造が入れ替わり、残存リスクが architect でなく reliability 側に寄った。**題材に仕込んだ role と選ばれる role は一致しなくてよい** — 判定するのは「修正後に残るリスクで選べているか」であって、仕込みへの字面一致ではない。HIGH を main の判断だけで non-blocking へ落として `PASS` に到達したため、`verdict.md` に「CRITICAL / HIGH を main 判断で non-blocking にしない（`accepted-risk` はユーザ受け入れのみ）」を明示した

## blocker-only-recheck: blocker だけで収束する

- 対象層: recheck の限定スコープ・non-blocking で再走しない収束
- 題材: 直前 run が `BLOCKED`（未解決 HIGH 1 + non-blocking MEDIUM 2）。HIGH に対する修正差分と `integration.md` を渡して再確認させる
- 期待品質: フルレビューへ戻らず、blocker を所有する role の fresh subagent 1 名で解消判定と fix 起因の regression だけを見る。MEDIUM 2 件は non-blocking のまま持ち越し、次ラウンドを起こさずに `PASS`
- 判定: 期待どおり（2026-08-08, #197）。fresh `security` 1 名、blocker は著者の申告でなく実行（405 組合せ）で解消確認。修正 hunk 由来の新規 blocker（import 欠落で認可コードに到達しない）を main が捕捉して修正。MEDIUM 2 件は探索対象から明示的に外して非ブロッキングのまま `PASS`

## trigger-pairs: description 発火対

- 対象層: description（トリガー）— 常時起動契約と隣接 skill 境界の健全性ゲート
- 題材: description 一覧のみから判定させる。should:「この変更、独立した視点で深くレビューしてほしい」「セキュリティ観点で徹底的に見て」「typo 直した、確認して」/ should-not:「実装終わったので仕上げて PR にして」（km-github-workflow へ）「この skill を改善したいので効き目を検証して」（km-skill-improve へ）
- 期待品質: 軽微な確認依頼を含め実装後のレビューは km-review が受ける（軽微は skill 内で 0 名判定）。delivery と挙動改善検証は隣接 skill へ流れる
- 判定: 健全性ゲートとして維持。description を変えるたびに必ず再走する

## 題材構築の落とし穴

- 対象差分は **`git apply --check` を通る well-formed な patch**、または実際に git repo を作って未コミット差分にする。壊れた patch は「根拠が検証不能」と正しく指摘され、測りたい層の評価が濁る
- 仕込んだ軽微項目の文字列を **repo に実在する文言と衝突させない**。衝突すると値・契約の drift に該当して重大度の期待がずれる
- 軽微側を無害に見せるための添え物に**本物の欠陥を紛れ込ませない**。カモフラージュ用の hunk が実際に欠陥だと、レビュアはそちらを正しく報告して期待と観測がずれる
