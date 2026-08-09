# km-review scenario bank

挙動を変えたときに何を測り直すかの対応表と、その題材。runtime では読まない。

## 再走トリガ

| 触った箇所 | 再走する題材 |
| --- | --- |
| description | trigger-pairs |
| routing（人数・role・security hard route） | minor-main-only / reliability-degradation / security-hard-route / dual-role-max-two |
| severity / blocking / 収束条件 | minor-main-only / blocker-only-recheck |
| recheck | blocker-only-recheck |
| role file の責務境界 | reliability-degradation / dual-role-max-two |

## 題材と合否線

- **minor-main-only** — 既存テストが両分岐を直接押さえる軽微差分（文言追加 + ローカル変数リネーム）。km-review を通したうえで 0 名を選び、根拠を行数や docs-only でなく**局所性・可逆性・material surface 不変・直接検証**で言語化する。LOW が出ても non-blocking のまま `PASS`
- **reliability-degradation** — 無効化の無いキャッシュ導入。運用者の設定編集が反映されず（docstring が謳う無停止リロードを壊す）、キャッシュ済み dict を参照で返すので呼び出し元の変更が全体へ波及する。`reliability` 1 名を選び security hard route は不成立と判断し、仕込んだデグレードを捕捉する
- **security-hard-route** — 所有者チェックを通る既存経路の隣に、共有トークンを非空判定するだけの新経路を足す。変更の**意味**で hard route を発火させ `security` を選び、認可迂回を捕捉する。main が直しても severity 件数から消さない
- **dual-role-max-two** — 秘密を含む payload の新しい永続 sink + 非アトミック書き込み・ロック無し。role ごとに理由 1 行を付けて 2 名だけ選び、三人目を同一ラウンドへ足さない。**仕込んだ role と選ばれる role の一致は問わない** — 見るのは修正後に残るリスクで選べているか
- **blocker-only-recheck** — 直前 run が `BLOCKED`（未解決 HIGH 1 + non-blocking MEDIUM 2）で、HIGH への修正差分と `integration.md` を渡す。フルレビューへ戻らず fresh 1 名で解消判定と fix 起因の regression だけを見て、MEDIUM のために次ラウンドへ進まず `PASS`
- **trigger-pairs** — description 一覧のみから skill を選ばせる。should:「独立した視点で深くレビューして」「セキュリティ観点で徹底的に見て」「typo 直した、確認して」/ should-not:「実装終わったので PR にして」（km-github-workflow へ）「skill の効き目を検証して」（km-skill-improve へ）

## 題材構築の落とし穴

- 対象差分は `git apply --check` を通る patch か、実際の git repo の未コミット差分にする。壊れた patch は「根拠が検証不能」と正しく指摘され、測りたい層の評価が濁る
- 仕込んだ軽微項目の文字列を repo の実在文言と衝突させない。衝突すると値・契約の drift 指摘に化けて重大度の期待がずれる
- カモフラージュ用の hunk に本物の欠陥を混ぜない。レビュアはそちらを正しく報告するので、仕込みへの期待と観測がずれる
- subagent を起動できないサンドボックスでは独立レビュア層が実行不能になり安全側で `BLOCKED` になる。その条件下で見るのは routing 判断と言語化まで
