---
name: km-plan
description: >
  実装計画を設計ブリーフ（背景 / 現在地 / 設計判断とその理由 / 変更 map / 反証可能な完了条件）として作り込み、
  `.plan/YYYYMMDD-<slug>.md` へ書き出す。main が反証・修正したうえで残る planning risk にだけ
  独立レビュア（0〜2 名）を focus 付きで当て、高コストな誤方向だけを `planning-blocker` として止めて
  `READY` / `BLOCKED` を判定し、`READY` を GitHub issue へ全文ミラーする。
  「計画を作って」「issue にして」で起動する。変更差分のレビューは km-review、PR delivery 単体は km-github-workflow。
argument-hint: "[title-or-topic | issue-number]"
---

# Plan

計画は**実装 agent への設計ブリーフ兼ゴール契約**。読み手は会話を知らない別の AI か未来の自分で、issue 単体から「なぜこの方向か・いまどうなっているか・何をどこまで変えるか・どうなれば完了か」を再調査なしに掴める必要がある。

目的は詳細度ではなく**高コストな誤進行の予防**。今詰めるかは detail の細かさでなく、間違えたときの direction-change cost で決める。

## 情報は厚く、拘束は薄く

- **判断に必要な情報は厚く残す** — 背景、現在地、責務、制約、採る方向とその理由、現実的な代替案と不採用理由、trade-off、変更 surface、completion evidence
- **実装方法の拘束は薄くする** — 内部構造、全 edge case、全 test case、逐次手順は固定しない。順序を固定するのは、順序自体が correctness・互換性・安全性・依存の制約であるときだけ

迷ったら **「省くと、能力のある実装者でも調査をやり直す・別の設計方向を選ぶ・制約を見落とすか」**。Yes なら書く。No で repo から実装時に安く導けるなら書かない。

## 進め方

**Clarify → Materialize → Review → Publish → Report。**

### Clarify

要求と repo を計画の規模に見合う深さで調べる。設計方針・scope・feasibility・完了条件を左右する事実は直接確認し、出典（`file:line`・コマンド出力の要点）を残す。

ユーザに聞くのは次に該当するものだけ。選択肢と推奨案を添えて聞く。

- ゴール・scope・完了条件が変わる
- one-way door の選択
- ユーザが所有する material trade-off（コスト・優先度・対外的影響）
- repo と一次情報から確定できず、外すと高コストになる feasibility 前提

それ以外の可逆な分岐は、既存 pattern と最小の方針を自分で選ぶ。repo・コード・一次情報で答えの出る事実は聞く前に確認する。不慣れな領域では「何を知らないか」を 1 パス洗い出し、上に該当するものだけ質問へ上げる。

着手前に、理解した問題・採る方向・実装者へ残す自由度・実装時確認事項へ送る未決を数行で宣言して進む（返答は待たない）。**上に該当する未決を宣言で代替しない** — 妥当な前提を置けるものだけ宣言する。

### Materialize

`references/goal-contract.md` を読み、本文を組み立ててから `.plan/YYYYMMDD-<slug>.md` へ書き出す。背景・現在地・判断理由・変更 map は削減対象ではない。手順の列挙より what / why / 制約 / 影響 / 変更 surface を優先する。

- 書き出す前に `.plan/` が git に追跡されないことを確かめる。未追跡かつ未 ignore なら `.gitignore` に `.plan/` を足す。すでに追跡済みなら repo 方針と衝突するので、勝手に直さずユーザに確認して止まる
- 書き出す前に goal-contract.md の lint を本文へ当てる

### Review

著者は自分の計画を「正しい」と読む。**main が先に反証・修正し、その最終候補に残る planning risk にだけ独立レビュアを 0〜2 名使う。**

1. **反証する** — ゴール・scope・完了条件を固定し、current state と設計方針の対応、one-way door、load-bearing な事実を崩しにいく
2. **直す** — 情報不足と過剰な手順固定を直し、変更 map・実装 slice・判断理由を整える
3. **残存 risk を言語化する** — 修正後の候補に残る、高コストな誤方向につながりうる未検証の risk
4. **0〜2 名を選ぶ** — 下の routing。計画の長さ・docs-only・規模では決めない
5. **起動する** — `references/reviewer.md` と計画ファイルを**絶対パス**で渡し、割り当てた focus と選択理由を添える。main の所見・修正履歴・暫定判定・他レビュアの報告は渡さない。読めないファイルがあれば憶測せずパスを報告して終えさせる
6. **統合して判定する** — main が materiality gate を再検証して最終分類する。レビュアの判定保留は `rejected` にせず main が repo・一次情報で検証し、決着できず load-bearing なら blocker として扱う

#### 独立レビュアを 0〜2 名選ぶ

**0 名** — 次をすべて満たすときだけ。ゴール・scope・完了条件が明確 / 設計方針が既存 pattern の直接適用で load-bearing な不確実性が残らない / hard route に該当しない / current state・変更 surface・判断理由が実装 handoff に足りる / main review 後に高コストな誤方向へつながる未検証 risk が残らない。

**1 名** — 残存 risk が一つの focus に集約できる。focus の例: outcome / scope、architecture / feasibility、公開契約 / migration、trust boundary / 不可逆操作、decision context / handoff、completion evidence。

**2 名** — 直交する 2 つの risk が具体化し、片方の確認が他方を代替できないときだけ。focus ごとに選択理由を 1 行残す。同じ汎用レビューを二重に走らせない。

**1 ラウンド最大 2 名。** レビュー中に第三の material risk が具体化したら、同じラウンドへ足さず次の targeted round で 1 名を走らせる。

**hard route** — 次を実質的に確定・変更する計画は最低 1 名を通す。公開 API / CLI / protocol / identifier / 長寿命な設定、schema・永続化形式・data ownership、migration・削除・復元不能な変換、認証・認可・tenant / privilege・secret・外部入力から実行への trust boundary、本番権限・課金・送信・公開のような不可逆または高影響の外部副作用、repo 横断で複製される pattern・依存方向・framework 導入。字面でなく**戻しにくさと影響範囲**で判定する。

#### 収束

**formal finding は planning blocker だけ**（gate は `references/reviewer.md`）。満たさないものは分ける。

- `implementation-check` — 実装時に情報が増えてから安く決まる。本文の「実装時確認事項」へ
- `accepted-risk` — material だが、ユーザが理由と再評価条件を了解して残す。**受諾が取れるまでは未解決 blocker のまま扱う**
- `rejected` — 重複・根拠不足・scope 外・一般論・極端な将来仮説・好み

レビュアの候補 finding が gate を満たさなければ main が implementation-check / rejected にしてよい。逆に、**gate を満たす blocker を、判定を通すために implementation-check / rejected / accepted-risk のいずれへも降格させない。**

- `READY` — 必要なレビューが完了し、未解決 planning blocker が無い。implementation-check が残っていてもよい
- `BLOCKED` — 未解決 blocker がある / 必須レビュアが失敗した / hard route の確認を完了できない

`BLOCKED` の間だけ、blocker を直して fresh reviewer 1 名で recheck する。recheck には解消対象の blocker 記述と修正箇所を渡す（手順 5 の非共有はここでは適用しない。main の暫定判定・他の finding・修正の経緯は渡さない）。見るのは blocker の解消と、その修正が持ち込んだ新しい blocker だけ。**non-blocker のために再実行しない。** 収束しなければ未解決の論点と選択肢をユーザへ委ねる。

### Publish

GitHub 管理 repo でだけ実行する。手順と既存 issue の更新規約は `references/issue.md`。明示が無い限り**新規 issue** を作る（類似 open issue の自動探索・再利用はしない）。

### Report

`.plan/` パス、issue URL、レビュア構成と選択理由、`READY` / `BLOCKED`、受け入れ済みリスク、実装時確認事項（どこで消化されるか）、未同期があればその旨。issue はそのまま km-github-workflow の実装タスク列になる。

## 計画を直すとき

要求の変化・外部レビュー・前提の誤りが届いたら、**ゴール（達成すること / やらないこと / 完了条件）が動くか**で分ける。

- **動く** — ゴールを先に改版し、背景・現在地 → 設計方針 → 主要な設計判断 → 変更 map → 実装 slice → 検証 → risk → 実装時確認事項へ順に伝播させる。下流から入れると宙に浮いた完了条件・slice が残る
- **動かない** — 該当する slice・検証への局所反映に留める

どちらも変更範囲へ Review を当て直す。外部レビューの指摘は 1 件 = 1 判断へ分解し、materiality gate で blocker / implementation-check / accepted-risk / rejected へ振り分ける。最終本文には**現在の判断理由だけ**を残し、変更の履歴とレビューの往復は commit / PR / issue comment へ置く。公開済み issue への再同期は `references/issue.md`。

## 不変条件

- **`READY` でだけ公開する**: `BLOCKED` のまま新規 issue を作らず、公開済み issue も更新しない
- **issue body は全文ミラー**: `.plan/` と同じ markdown を `--body-file` で渡す。要約・抜粋・heredoc での再構成・`--body "..."` は不可（backtick / `$(...)` が展開される）
- **`.plan/` は一時作業場**: 共有成果物（issue / PR / comment）から `.plan/` のファイルを参照先として書かない。正本は issue / PR の URL
- **`gh` の失敗を成功扱いしない**: issue 未作成と「作成済みだが URL 未同期」を区別して報告する
