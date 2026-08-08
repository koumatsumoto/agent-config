---
name: km-review
description: >
  変更レビューの標準ワークフロー（未コミット差分 / コミット範囲 / PR / サブツリー）。main が対象全体を反証・修正・再検証し、
  残った material risk にだけ独立レビュア（architect / product / reliability / security から 0〜2 名）を割り当てて
  `PASS` / `BLOCKED` を判定する。実装後のレビューは軽微な変更でもここを通す（軽微なら独立レビュア 0 名と判定する）。
  「レビューして」「PR をレビューして」「セキュリティ観点で見て」や、他 skill の Verify から起動する。
  計画づくりは km-plan、PR delivery は km-github-workflow、挙動改善の効き目検証は km-skill-improve。
argument-hint: "[target]"
---

# Review

**main が先に反証・修正・再検証し、その最終候補に残る material risk にだけ独立レビュアを 0〜2 名使う。** 独立性は同じ差分を二重に読むためではなく、main の認知枠から漏れた見落としを別コンテキストで拾うために使う。

呼び出し元の完了確認（完了条件・差分・テストの照合）は本 skill の前段であって、レビューの代わりではない。**完了確認を済ませたことを理由に本 skill を省略しない。** 軽微な変更は「独立レビュア 0 名」としてここで閉じる。

判定は `PASS` / `BLOCKED` / `NOOP`。

## 対象を決める

| 引数 | 対象 |
| --- | --- |
| なし（既定） | 未コミット差分 `git diff` → 無ければ current branch の `gh pr diff` → それも無ければ `NOOP` |
| `pr` / `pr:<n>` | `gh pr diff [<n>]`（失敗時は別スコープの指定を促す） |
| `<base>..<head>` / `<sha>` | `git diff <base>..<head>` / `git show <sha>`（解決できなければエラー終了） |
| `--repo <subtree>` | diff でなく現状コード全体。`git ls-files <subtree>` で列挙して読む。既存問題・未変更行を除外しない |
| `--recheck` | `BLOCKED` 後の限定再確認（`references/recheck.md`） |
| `quick` / `standard` / `thorough` | 読む深さのユーザヒント。**レビュア人数へ写像しない。** `quick` でも security hard route と blocker の検証は省略しない |

裸の数字（`42`）は km-github-workflow の issue 番号引数と紛らわしいので、警告して `pr:42` の明示を求める。`--repo` は他モードおよび `--recheck` と併用しない。`--repo` の対象（binary / lockfile / generated を除く）がレビュアの context に収まらない規模なら、進まずサブツリーを絞るよう促す。

## Review anchor を固定する

開始時に短く固定する。既存の issue・完了条件・ユーザ指示を基準点として信頼し、要件を再導出・拡張しない。

- **intent / expected outcome** — 何を達成する変更か
- **scope / non-goals** — 今回変えるもの / 変えないもの
- **primary user / operator** — 結果を使う・運用する主体
- **changed surfaces** — 挙動・公開契約・データ・権限・運用・挙動資産のどこが動くか

**挙動資産**（skill / rule / `CLAUDE.md` / `AGENTS.md` / command / output-style など、agent に読み込まれて挙動を規定する prompt 定義）は `.md` でも code-equivalent として扱い、docs-only に落とさない。人間向けの README・runbook・設計 doc・CHANGELOG は、それ自体が agent 挙動を規定しない限り挙動資産ではない。迷ったらコード側に倒す。

## main review

main は独立レビュアではなく、変更を統合するレビュー責任者。

1. **反証する** — 差分内で正しいと仮定しない。判定に必要な呼び出し元・定義元・契約・既存テスト・類似実装を開き、intent と変更全体の対応を崩しにいく
2. **直す** — writable な通常開発では、明確な in-scope finding を修正し、関連する検証を再実行する
3. **記録する** — 直した finding も ledger に残す（独立レビュー前に消えた欠陥も最終件数へ含める）。載せるのはレビュアと同じ materiality gate — **evidence / 現実的な成立条件 / material impact / 最小の修正方針**を示せるものだけ
4. **routing する** — 修正後の候補に残る不確実性と material risk から独立レビュアを 0〜2 名選ぶ

read-only 実行や外部 PR のレビューでは修正できないが、**順序は変えない**。main review を先に終え、main の所見は渡さずに dispatch し、統合時に dedup する。

## 独立レビュアを 0〜2 名選ぶ

判断材料は**修正後の候補に残るリスク**。変更行数・ラベル・ファイル種別では決めない。

**0 名（main only）** — 次をすべて満たすときだけ。

1. 局所的で容易に戻せる
2. 利用者向け挙動・公開契約・永続データ・権限 / trust boundary・外部副作用・挙動資産の意味を material に変えない
3. 新規経路・非自明な状態遷移・重要な既定値の変更を導入しない
4. 変更を直接確認する検証があり、main review 後に重要な不確実性が残らない

行数が少ない・docs-only・test-only・config-only という**形式だけを理由に 0 名にしない**。0 名なら `references/dispatch.md` も role file も読まない。

**1 名（既定）** — 0 名の条件を満たさず、残存 material risk が一つの主要テーマに集約できる。通常の非自明な変更はここ。

**2 名（例外）** — 異なる 2 role に属する material risk がそれぞれ具体化し、片方のレビューが他方を代替できないときだけ。role ごとに選択理由を 1 行残す。「大規模」「重要」「`thorough`」だけを理由にしない。同じ汎用レビューを二重に走らせない。

**1 ラウンド最大 2 名。** レビュー後に具体的で未検証の第三の material risk が判明したら、同じラウンドへ三人目を足さず、次の targeted round で該当 role 1 名を走らせる。未検証の material risk を残して `PASS` にしない。

| role | 選ぶ残存リスク |
| --- | --- |
| architect | one-way door、公開契約・schema・永続化、依存方向、責務境界、複製される pattern、課題に不釣り合いな複雑性 |
| product | 利用者・運用者・ビジネス成果、problem–solution fit、end-to-end の成立、必須 slice の欠落と価値を薄める過剰 scope |
| reliability | 実挙動、regression / degradation、状態・時間・並行、失敗と回復、rollout・運用。非自明な runtime 挙動の変更で他 role が支配的でないときの既定候補 |
| security | attack surface、trust boundary、権限・tenant・秘密情報、外部入力からの実行、危険な副作用 |

role 選択のために role file を先読みしない。上の 1 行で選び、選んだ file だけを subagent へ渡す。

**security hard route** — main の修正後でも、変更が trust boundary または attack surface を実質的に変えるなら `security` を必ず含める。差分に security という語があるかではなく**変更の意味**で判定する: 認証・認可、tenant / privilege 境界、secret・機密データの流れと出力先、外部入力から query / command / template / tool を実行する経路、CI/CD・本番権限、削除・課金・送信のような高影響副作用。

## 走らせて判定する

- 1 名以上を選んだら `references/dispatch.md` に従って起動する
- 統合・severity / blocking / status の確定・レポートは `references/verdict.md`
- 結果は `<report dir>` = repo root の `.km-review/<scope-slug>/` へ残す（引数なしの slug は常に `uncommitted` なので `.km-review/uncommitted/`。直下へ平坦化しない）。同一スコープの別 run は同じパスを再利用する。**セッションをまたいで発見できる固定パス**であることが recheck の要件。書き込み前に確認する: `.km-review/` が git 追跡済みなら自動書き込みせずユーザへ確認して止まる / `git check-ignore` で無視済みなら何もしない / 未無視なら `.git/info/exclude` に `/.km-review/` を追記する（ephemeral な scratch なので committed `.gitignore` を汚さない）。これらを `git add` しない
- 最終候補が外部から観測される面（挙動・公開契約・設定・コマンド・運用手順）または文書自体を変えるなら、final `PASS` の前に `references/doc-review.md` を main で実施して文書を最終状態へ同期する。`BLOCKED` なら defer してレポートに明記する
- `BLOCKED` 後の再確認は `references/recheck.md`

## 収束

`PASS` の条件は**未解決 blocker が無いこと**。blocker は「未解決のままでは current task を完了にできない finding」で、CRITICAL / HIGH は blocker（`references/verdict.md`）。

MEDIUM / LOW や non-blocking finding が残っていても `PASS` にできる。**non-blocking finding をゼロにするためにレビューを再実行しない。** 未解決 blocker がある間だけ、修正 → targeted recheck を繰り返す。
