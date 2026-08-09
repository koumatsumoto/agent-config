# 統合と判定

main の強み（ツール実行・長コンテキスト・自己反証）を「**誤った `PASS` を出さない**」ことに使う。レビュアが付けたラベルを無条件に採用しない。

1. **dedup** — main の ledger とレビュア報告を根本原因単位でまとめる（`(file, ±5 行, 根本原因)`）。同一欠陥の別角度記述（「境界チェック欠落」/「不変条件違反」/「OOB read」）も 1 群にする。最も証拠の濃い 1 件を残し、併合元だけが持っていた情報（シナリオ・波及・再現条件）を注記する
2. **evidence を検証する** — blocker 候補が対象から具体的に裏づくかを確かめる。呼び出し元 / 先の追跡、安全な既存テストの実行、最小再現で確定または棄却する。裏づかないものは `rejected`、確定に届かないが捨てるべきでないものは確認推奨へ移す
3. **severity / blocking / status を確定する** — 下の定義で main が最終決定する
4. **収束を判定する** — 未解決 blocker が無ければ `PASS`

## severity（影響度）

- `CRITICAL` — 現実的な経路で、即時の重大事故・壊滅的損失・即時悪用に直結する
- `HIGH` — primary outcome の不達、明確な重大回帰、脆弱性、データ / 運用事故、長期保守を直撃する設計欠陥
- `MEDIUM` — 意味はあるが限定的な degradation、品質低下、運用リスク、設計不整合、技術負債
- `LOW` — 具体的な改善価値はあるが、primary outcome を material に損なわない

## blocking（進行可否）

「この finding を未解決のまま current task を `PASS` にできるか」。severity とは**別軸**で判定する。

- CRITICAL / HIGH は blocker、MEDIUM / LOW は原則 non-blocking
- severity によらず、**明示された完了条件または primary outcome を満たせない**なら blocker にできる。その場合は該当する完了条件 / outcome を名指しし、なぜ完了できないかを書く。名指しできない MEDIUM / LOW は non-blocking にする — 重要そうだから、では blocker にしない
- **CRITICAL / HIGH を main の判断だけで non-blocking へ落とさない。** 直さずに進めたいなら `BLOCKED` のままユーザへ論点と選択肢を出し、受け入れられたものだけ `accepted-risk` にする。severity を下げて blocker を消すのも同じく禁止 — 判定を通すために影響度を書き換えない
- `possible` 単独では blocker にしない。main が検証して `confirmed` / `likely` へ上げるか、確認推奨へ移す。ただし壊滅的リスクを排除するのに必須の証拠を取得できない場合は、推測の finding を作るのではなく「必要な検証を完了できない」ことを理由に run を `BLOCKED` にできる
- ユーザが理由と条件を明示して受け入れた finding は `accepted-risk` とし、未解決 blocker から外す。severity は変えない

## status

| status | 意味 | severity 件数 | 未解決 blocker 数 |
| --- | --- | --- | --- |
| `resolved` | main または後続の修正で解消した | 含める | 含めない |
| `unresolved` | 根拠が確定し、未修正 | 含める | `blocking: true` のみ含める |
| `accepted-risk` | 理由と条件を明示して残す | 含める | 含めない |
| `rejected` | 重複・偽陽性・根拠不足で棄却 | 含めない | 含めない |

**main が独立レビュー前に修正した finding も `resolved` として severity 件数に残す。** ユーザは「このレビューでどれだけ問題が見つかったか」と「いま何が blocker か」を別々に把握できる必要がある。

non-blocking finding は、in-scope で修正が明確かつ低リスクなら同一 run で直してよいが、義務ではない。**non-blocker を直したことを理由に独立レビューを再実行しない。** 修正が新しい material surface に触れたときだけ通常の routing へ戻す。

## 判定

- `PASS` — 必要なレビューが完了し、未解決 blocker が無い（MEDIUM / LOW の残存は許容する）
- `BLOCKED` — 未解決 blocker がある / 必要なレビュアが失敗・中断した / material risk の必須確認を完了できない
- `NOOP` — レビュー対象が存在しない。対象の解決に失敗した場合は `NOOP` ではなくエラーとして報告する

段階が結果を返さなかったら「実行失敗」として理由とともに記録し、判定は安全側の `BLOCKED` に倒す。完了マーカーの無い報告ファイルは中断された部分報告として、書けた所見まで回収してこの規則へ接続する（全損させない）。

## レポート

`<report dir>/integration.md` に書き出し、同じ内容をユーザへ報告する（recheck とセッション境界の正本）。

- **target / review anchor / 変更概要**（挙動資産ならその旨）
- **構成** — main only か、選んだ role と routing 理由。0 名ならその理由、2 名なら role ごとに 1 行
- **severity 別の dedup 済み総件数と status 内訳** / **未解決 blocker 数** — 別々に表示する
- **finding 本文** — severity / blocking / status / `file:line` / 何が問題か / どう直すか / 対象のどこが根拠か
- **未解決 blocker の最短解消方針**
- **確認推奨** — 確定できなかった懸念を「何が分かれば覆るか」1 行で。重大度なし・非ブロッキング・件数に非算入
- **受け入れ済みリスク** — severity / 残す理由 / 後続対応の条件
- **判定**

該当の無い項目は省いてよい。`NOOP` は 1 行でよい。秘密情報・token・PII は値を引用せず `file:line` と種別だけ書く。

```text
Severity: CRITICAL 0 / HIGH 2 (resolved 1, unresolved 1) / MEDIUM 2 (non-blocking) / LOW 0
Unresolved blockers: 1
Reviewers: main + reliability
Verdict: BLOCKED
```
