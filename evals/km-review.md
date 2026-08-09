# km-review 評価シナリオ集

挙動を変えたときに何を測り直すかの対応表と、その題材。実行時には読まない。

## 再走トリガ

| 触った箇所 | 再走する題材 |
| --- | --- |
| description | trigger-pairs |
| 割り当て（人数・観点・セキュリティの必須経路） | minor-main-only / reliability-degradation / security-hard-route / dual-role-max-two |
| 影響度 / 完了を妨げるか / 収束条件 | minor-main-only / blocker-only-recheck |
| 再確認 | blocker-only-recheck |
| 観点 file の責務境界 | reliability-degradation / dual-role-max-two |

## 題材と合否線

- **minor-main-only** — 既存テストが両分岐を直接押さえる軽微差分（文言追加とローカル変数名の変更）。km-reviewを通したうえで0名を選び、根拠を行数や文書だけの変更であることではなく、**局所性・可逆性・重要な変更面が不変であること・直接検証**で説明する。LOWが出ても完了を妨げない指摘として`PASS`とする
- **reliability-degradation** — 無効化のないキャッシュ導入。運用者の設定編集が反映されず（ドキュメント文字列が示す無停止リロードを壊す）、キャッシュ済み dict を参照で返すので呼び出し元の変更が全体へ波及する。`reliability` 1 名を選び security hard route は不成立と判断し、意図的に含めた回帰を捕捉する
- **security-hard-route** — 所有者チェックを通る既存経路の隣に、共有トークンを非空判定するだけの新経路を足す。変更の**意味**で hard route を発火させ `security` を選び、認可迂回を捕捉する。メイン担当が直しても severity 件数から消さない
- **dual-role-max-two** — 秘密を含む payload の新しい永続 sink + 非アトミック書き込み・ロック無し。観点ごとに理由 1 行を付けて 2 名だけ選び、三人目を同一ラウンドへ足さない。**想定した欠陥の観点と選ばれる観点の一致は問わない** — 見るのは修正後に残るリスクで選べているか
- **blocker-only-recheck** — 直前の実行が`BLOCKED`（未解決のHIGHが1件、完了を妨げないMEDIUMが2件）で、HIGHへの修正差分と`integration.md`を渡す。全面的なレビューへ戻らず、新しいレビュア1名で解消判定と修正起因の回帰だけを確認し、MEDIUMのために次ラウンドへ進まず`PASS`とする
- **trigger-pairs** — description 一覧のみから skill を選ばせる。should:「独立した視点で深くレビューして」「セキュリティ観点で徹底的に見て」「typo 直した、確認して」/ should-not:「実装終わったので PR にして」（km-github-workflow へ）「skill の変更効果を A/B で検証して」（km-skill-eval へ）

## 題材構築の落とし穴

- 対象差分は `git apply --check` を通る patch か、実際の git リポジトリの未コミット差分にする。壊れた patch は「根拠が検証不能」と正しく指摘され、評価対象がレビュー能力なのか差分の妥当性なのか判別できなくなる
- 意図的に含めた軽微項目の文字列をリポジトリの実在文言と衝突させない。衝突すると値・契約のずれに関する指摘へ変わり、重大度の期待がずれる
- 評価対象外の差分に本物の欠陥を混ぜない。レビュアはそちらを正しく報告するため、想定した欠陥への期待と観測がずれる
- サブエージェントを起動できないサンドボックスでは独立レビュア層を実行できないため、安全側の `BLOCKED` と判定する。その条件下で見るのは振り分けの判断と言語化まで
