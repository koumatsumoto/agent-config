# km-plan scenario bank

挙動を変えたときに何を測り直すかの対応表と、その題材。runtime では読まない。

## 再走トリガ

| 触った箇所 | 再走する題材 |
| --- | --- |
| description | trigger-pairs |
| Clarify の質問 gate | question-gate |
| 「情報は厚く、拘束は薄く」/ goal-contract.md の入れるもの・lint | decision-handoff / reversible-detail-deferral |
| Review の routing・hard route | reviewer-routing |
| planning materiality gate・READY / BLOCKED・recheck | blocker-convergence |

## 題材と合否線

- **trigger-pairs** — description 一覧のみから skill を選ばせる。should:「この機能の実装計画を issue にして」「この architecture 変更の背景と判断理由を残した計画を作って」/ should-not:「この bug をさくっと直して」（skill を挟まず直接実装へ）「実装が終わったので PR にして」（km-github-workflow へ）「この diff をレビューして」（km-review へ）。隣接 skill との境界と「計画を作り込む価値が無い小さな依頼」の両方を切り分けられているかを見る
- **question-gate** — 可逆な実装分岐（内部データ構造の選択など）と、ユーザ所有の material trade-off（対外互換を切るか維持するか）を同時に含む依頼。可逆な分岐を自分で決め、material trade-off だけを選択肢 + 推奨付きで聞くのが合格。可逆な分岐まで質問へ寄せる走、material trade-off を無断で決める走はどちらも不合格
- **decision-handoff** — 複数 file / component にまたがり、現実的な設計案が 2 つある変更（例: 既存 writer の再利用と新規 exporter 層の追加が並び立つ CLI サブコマンド追加）で「計画を issue にして」。read-only sandbox で実行し `gh` 相当はテキスト報告させる。背景・current state・各 component の責務・採用理由・代替案の不採用理由・trade-off・固定範囲・実装者の自由度が本文に残り、会話を読まない別 AI が調査をやり直さず着手できるかを見る。ゴールと task list だけの本文は不合格
- **reversible-detail-deferral** — 内部 library の細かな挙動・個別 edge case・test 境界が実装中にしか確定しない変更。計画時に全列挙・過剰調査せず、実装時確認事項に 後ろ倒しの理由 / 消化する slice・時点 / 判断に使う evidence が揃うのが合格。edge case を計画本文で網羅した走、blocker 級の未決を実装時確認事項へ落とした走は不合格
- **reviewer-routing** — 3 種を並べて routing だけを見る。(a) 既存 pattern の直接適用で load-bearing な不確実性が無い計画 → 0 名を選び理由を残す。(b) 公開 schema / migration / 認可境界のいずれかを変える計画 → hard route が発火して最低 1 名。(c) 公開契約と trust boundary が独立に material な計画 → focus を分けて 2 名、同一ラウンドに三人目を足さない。**計画の長さ・docs-only・規模で人数が決まった走は不合格**
- **blocker-convergence** — 局所仕様は満たすがユーザの primary outcome を満たさない計画（誤ゴール）と、可逆な改善提案を混ぜる。誤ゴールを planning-blocker として止め minimal resolution が goal / scope の修正を指すこと、可逆な提案を blocker にしないこと、blocker 修正後の recheck が blocker の解消と修正由来の新 blocker だけを見ること、implementation-check が残っていても `READY` にできることを見る

## 落とし穴

- 「issue にして」は計画を伴わない issue 起票まで引き寄せる。km-github-workflow は follow-up issue の起票を delivery 契約に含むため、この一語でトリガ語と責務範囲が交差する
- 本文の情報量は文字数で採点しない。見るのは「再調査を防げているか」と「実装経路を不要に固定していないか」の 2 軸で、長い本文が microtask と教科書的説明で埋まっている走は decision-handoff でも不合格
- 設計ブリーフの形式要件（`<!-- km:plan:managed -->` / 「実装時確認事項」節名 / `--body-file` 全文ミラー）は成果物を見れば決まる決定的チェック。題材の評価軸に混ぜると狙った観点の差が形式点に埋もれるので、契約チェックとして別に確かめる
