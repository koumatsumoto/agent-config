---
name: km-plan
description: Materializes implementation plans into `.plan/YYYYMMDD-<slug>.md` and, on a GitHub-managed repo, mirrors the final plan body to a GitHub issue as the canonical reference. The materialize-and-issue flow fires on explicit materialize / issue triggers — e.g. "issue にして", "計画を issue にして", "Issueで計画して", "issue に実装計画を作って", ".plan に出して", "計画レビューしてから issue 化". Lighter "計画を作って" / "実装計画を作成して" / "まず計画だけ" stays in draft-only — `<proposed_plan>` only, no disk write, no issue. Bare "PR にして" / "最後は PR" is km-github-workflow; "レビューして" on diffs is km-review. For "計画を作って PR まで" or "計画を issue にして PR にして", km-plan runs first then hands off to km-github-workflow with the issue number.
argument-hint: "[title-or-topic]"
---

# Plan

実装前に計画を作り込み、`.plan/YYYYMMDD-<slug>.md` へ書き出し、第三者レビューで精度を上げ、GitHub issue へ全文ミラーする。Clarify / Materialize / Review / Mirror / Report の 5 phase。

計画 issue は実装 agent への**ゴール契約**である: 達成すべきもの（Goal / Non-goal / 反証可能な DoD）、依拠する事実（出典付き）、守るべき制約・設計判断、合否の証明方法（検証）を規定し、実装経路の詳細は制約が要る場合を除き実装 agent に委ねる。本文の組み立て方は `references/plan-template.md`。

## Context

- Repo: !`git rev-parse --is-inside-work-tree 2>/dev/null || echo "(not a git repo)"`
- Branch: !`git branch --show-current 2>/dev/null`
- `.plan/` tracked?: !`git ls-files -- .plan .plan/ 2>/dev/null | head -1 || echo "(none)"`
- `.plan/` ignored?: !`git check-ignore -q .plan/ 2>/dev/null && echo "yes" || echo "no"`

Context はロード時のスナップショット。gate 判定は Phase 2 / 4 の実行時に取り直す。

## Success Criteria

- 計画の骨子（Goal / Non-goal / 合否判定できる DoD、主要トレードオフ）の未決を解消してから materialize し、goal を計画冒頭の anchor に固定してある
- plan 本文が issue 単体で読め、実装 agent が再分解せず最初の作業単位から着手できる
- 第三者レビューが収束している（未解決 `CRITICAL` / `HIGH` ゼロ。収束しなければ issue 化しない）
- レビュー往復・採否経緯が本文に残っていない（残るのは最終計画・受け入れ済みリスク・実装時確認事項だけ）

## Routing

**Entry mode**（最初に 1 つ決める。Plan Mode か判別できなければ安全側の `draft-only` に倒す）:

| mode | 条件 | 進み方 |
| --- | --- | --- |
| `draft-only` | Plan Mode 中、または materialize / issue 化の明示が無い計画作成依頼 | Phase 1 で `<proposed_plan>` 提示まで → **停止**（書き込み・issue 化なし）。進むには ".plan に出して" / "計画を issue にして" と依頼するよう案内する |
| `materialize-existing-plan` | Plan Mode 外で、直近の合意済み計画を会話から復元でき、materialize / issue 化が依頼された | 合意済み内容は再設計せず詳細化する。骨子の未決のみ確認して Phase 2 へ。復元できなければ推測で書き出さず計画内容を再確認する |
| `full-normal-mode` | Plan Mode 外で、`.plan/` 出力 / 計画 issue 化が明示された | Phase 1 から順に |

境界: PR delivery が主目的なら `km-github-workflow`、変更差分のレビューは `km-review`。ブランチ / PR 作成・push は `km-github-workflow` の責務で、本スキルは PR 分割の設計までを扱う。「計画を作って PR まで」は km-plan で issue 化まで行い、issue 番号を渡して `km-github-workflow` へ handoff する（issue を作れず停止した場合は handoff せず理由を報告して判断を委ねる）。計画コンテキストの無い ad-hoc issue + PR は km-github-workflow に委ねる。materialize 後の要求差分・外部レビュー反映の依頼は「計画の更新」節へ。

## Phase 1: Clarify

1. 依頼と repo を把握する（`$ARGUMENTS` は計画タイトル / 既存 issue 番号のヒント）。関連コード・制約は計画の規模に見合う深さで調査し（影響範囲が広ければ並行 Explore subagent、軽量なら最小限）、得た事実は出典（`file:line` 等）付きで計画の前提に残す
2. **Clarify Gate**（materialize に進む mode のみ）: 要件を取り違えていないか・浅い理解のまま進んでいないかを確かめ、本質を引き出して固めてから進む。骨子（Goal / Non-goal / DoD / 主要トレードオフ）を左右する未決だけを確認する。妥当な前提で進められるものは聞かず、確認は選択肢 + 推奨案つきでまとめて 1 回にする。計画を左右する品質特性（性能・サイズ・保守性など非機能の合否基準）も、争点になるならここで固める。未解消のまま Phase 2 に進まない
3. **前提宣言**（materialize 直前、非ブロッキング）: 置いた前提・スコープ判断を 3〜6 行で宣言し、返答を待たず進む。宣言でよいのは「どの妥当な解を選んでも DoD が変わらない前提」だけで、DoD / スコープ / 主要トレードオフを左右する不確実性は step 2 の質問（ブロッキング）へ格上げする。自動連鎖・headless 実行では宣言を読む人が居ないため、この格上げを特に守る

## Phase 2: Materialize to `.plan/`

1. **`.gitignore` 安全確認**(書き込みより先に): git repo でなければ `.gitignore` に触れず `.plan/` 出力のみ / `.plan` が追跡済みなら repo 方針と衝突するため自動編集せずユーザに確認して停止 / 既に ignore 済みなら編集しない / いずれでもなければ `.gitignore` に `.plan/` を追加する
2. `references/plan-template.md` を読み、本文を**メモリ上で**組み立てる（`<!-- km:plan:managed -->` marker を含む）
3. **pre-write gate**: 組み立てた本文に「Secret Check」節と plan-template.md「DoD の self-lint 基準」を適用する。secret 検出なら書き出さず停止してマスキングを依頼、self-lint 違反なら修正する。修正で本文が変わったら Secret Check を再適用してから書き出す
4. `.plan/YYYYMMDD-<slug>.md` に書き出す。slug は英小文字 kebab-case（50 文字以下目安。作れなければ `plan`）、同日付の既存ファイルと衝突するときだけ `-2`, `-3` を付けて上書きを避ける

## Phase 3: Review (agentic)

書き出した計画を第三者目線でレビューする。観点・重大度・出力形式は `references/plan-review-checklist.md` が正で、最重要の問いは「計画が本質的に満たすべき要件（Goal）を取り違えていないか」。

1. **強度を規模・不可逆性・リスクで選ぶ**（迷ったら一段上へ。subagent 非対応環境は self-review にフォールバック）:
   - **self-review** — 軽量計画（小規模・可逆・低リスク）。メイン agent が著者バイアスを自覚して 2 レンズで critical に読み直す
   - **単一 subagent（既定）** — 中規模以上。著者でない subagent に下のプロンプトでレビューさせる
   - **専門家追加** — 高リスク領域に触れるとき、`references/plan-review-checklist.md`「専門家レンズ」から該当レンズを必要な分だけ足す（対象領域とレンズの対応は同節が正本）
2. **指摘を入力クラス別に反映する**:
   - 重大度付きの指摘: plan 本文へ反映するか、`MEDIUM` / `LOW` に限り受け入れ済みリスクとして記録する。grade 済みの指摘を「実装時確認事項」へ委譲し直さない（reviewer の可逆性トリアージ判断を無効化するため）
   - 重大度なしの「実装時確認事項候補」: 高影響カテゴリ（security / 秘密情報 / 認証・認可 / 不可逆・広範囲 / feasibility・正しさ）に触れないことを確認して plan 本文の「実装時確認事項」へ転記する。触れるなら重大度付き指摘へ戻す
   - 採否判断・反映の往復は本文に書き戻さない（共有したければ issue 化後に issue comments へ）
3. **収束させる**: `CRITICAL` / `HIGH` ゼロまで反復する。初回はフルレビュー、2 回目以降は未解決 `CRITICAL` / `HIGH` の解消確認に絞った差分レビュー。上限 3 周で収束しなければ issue 化を止め、未収束の指摘とともにユーザに委ねる。レビュー結果が空・形式不一致・対象ファイル読取失敗のときは未実施として扱い、原因（多くはパス）を直して再実行するまで issue 化しない

subagent 起動プロンプト（`<plan skill root>` と計画ファイルは `~` を展開した**絶対パス**に置換して渡す。install root: Claude Code は `~/.claude/skills/km-plan/`、Codex CLI は `~/.agents/skills/km-plan/`、Qwen Code は `~/.qwen/skills/km-plan/`）:

```
あなたは km-plan の第三者計画レビュアです。計画の著者ではない独立した視点で、実装計画を critical にレビューしてください。

1. まず `<plan skill root>/references/plan-review-checklist.md` を読む（レンズ・重大度・トリアージ・出力形式はここが正）
2. 計画ファイル <絶対パス> を読み、checklist に従いレビューする
3. 計画の前提の真偽確認に必要なら repo のファイルを Read してよい。出典付き主張のうち設計判断・作業単位の成否を左右する load-bearing なものは直接たどって確認し、その他はサンプル確認、出典の無い主張は「判定保留」とする
4. checklist か計画ファイルが読めなければ、憶測でレビューせず読めなかったパスを報告して終了する
5. 差分レビュー指示があるときは、指定された未解決 CRITICAL / HIGH の解消確認に絞ってよい

出力は checklist の「出力形式」に従い、本文は書き換えず指摘だけを返す。
```

## Phase 4: Mirror to GitHub issue

GitHub 管理 repo でのみ実行する。明示が無い限り**新規 issue** を作る（類似 open issue の自動探索・再利用はしない。誤上書きを避けるため）。

1. **pre-issue Secret Check**（gate）: レビュー反映後の最終本文と issue title に「Secret Check」節を再適用する。検出したら issue 化せず停止し、ユーザに masking / 再生成を依頼する（`.plan/` の自動削除はしない）
2. `gh` の可用性・認証と GitHub repo であることを確認する。不能なら原因（未インストール / 未認証 / 非 GitHub repo / ネットワーク）を区別して報告し、`.plan/` 出力で停止する
3. `gh issue create --title "<title>" --body-file <plan-file>` で**全文ミラー**する。title は計画タイトルから作り（Conventional Commits 互換だと後続 PR と揃う）、shell 展開される backtick / `$(...)` を含めない
4. **2-step sync**: 返された URL を `.plan/` 本文の placeholder に書き込み、`gh issue edit <number> --body-file <plan-file>` で再同期する

**既存 issue の更新**は、ユーザが issue 番号 / 既存 issue 更新を明示した場合だけ扱う（例: "issue #25 に反映して" / `/km-plan 25`）。`gh issue view` で対象を確認し、body に `<!-- km:plan:managed -->` marker があれば `--body-file` で更新してよい。marker が無ければ km-plan 管理外の可能性があるため全文置換前にユーザに確認する。title は原則触らず、齟齬が大きいときだけ可否を確認してから変える。

## Phase 5: Report

`.plan/` パス、issue URL、受け入れ済みリスク、実装時確認事項（消化先とともに）、未同期があればその旨を報告する。計画は検証可能な作業単位に分解済みなので、issue はそのまま km-github-workflow の実装タスク列として渡る。

## 計画の更新（materialize 後の差分反映）

要求・制約の変化、外部レビュー結果、前提事実の誤りが届いたら、まず**差分が anchor（Goal / Non-goal / DoD）を動かすか**で分岐する:

- **動かす** → 局所パッチせず **anchor-first**: anchor を先に改版し、下流（設計判断 → 作業単位 → 検証 → リスク）へ順に伝播する（下流から入れると宙に浮いた DoD・作業単位が残る）。削除した DoD を参照する作業単位が残っていないか、新 DoD に担当作業単位があるかを点検し、変更範囲に Phase 3 のフルレビューを再適用する
- **動かさない** → 該当作業単位・検証への局所反映と、その範囲の Phase 3 再適用に留める

外部レビュー結果（複数レビュアー・指摘多数がありうる）は「まとめて確認」で漏らさないよう、指摘 1 件 = 1 タスクに分解して個別に採否判断する（似た指摘も出典別に別タスク）。外部指摘は checklist のトリアージを通っていないため、`MEDIUM` / `LOW` 相当には orchestrator が可逆性トリアージ（checklist の 2 軸 + 高影響ガード）を適用し、反映 / 受け入れ済みリスク / 実装時確認事項へ個別に振り分ける。採否の背景を共有したいときは issue comments へ書き、本文には残さない。

反映後は `.plan/` を更新し、**pre-issue Secret Check を通してから**（外部レビュー結果には log・認証情報が混じりやすい）`gh issue edit <number> --body-file <plan-file>` で再同期する。再レビューが未収束のまま公開 issue を更新しない。

## Secret Check

plan 本文は issue に全文ミラーされるため、秘密情報の混入は公開に直結する。Phase 2（pre-write）と Phase 4（pre-issue）の 2 gate で本文を走査する:

- ファイル名 / path: `.env*`, `*.pem`, `*.key`, `*credentials*`, `*.pfx` を参照する行
- 認証情報のキー名（大文字小文字・`=` / `:` 区切りを問わず値が付いている行）: `password`, `secret`, `token`, `api_key` / `apikey`, `credential`, `private_key`
- 値パターン: `AKIA` / `ASIA`, `ghp_` / `github_pat_`, `xox[baprs]-`, `sk-`, `eyJ`（JWT）, `-----BEGIN ... PRIVATE KEY-----`, `Bearer `
- ログ / スタックトレース貼り付けに含まれがちな社内ホスト名・ユーザー名・内部 URL

検出が不確かでも issue 化前にユーザへ確認する。疑わしきは止める。

## 不変条件

- **Plan Mode 中**は `.plan/` / `.gitignore` / GitHub issue を一切変更しない
- **issue body は全文ミラー**: `.plan/` と同じ markdown を `--body-file` で渡す（要約・抜粋・heredoc 再構成・`--body "..."` は不可）
- **`.plan/` は一時作業場**: 共有成果物（issue / PR / comment）から `.plan/` 配下の具体ファイルを source of truth として参照させない。正本は issue / PR の URL
- **Secret Check** は本文が外へ出る全経路の実行前に通す: `.plan/` への書き出し（pre-write）と `gh issue create/edit`（新規・2-step sync・既存更新・更新反映後の再同期）。`.plan/` に秘密情報が入れば後続の全経路がそれを引き継ぐため、issue 経路だけでは足りない
- **gh 失敗**は成功扱いせず、issue 未作成と「作成済みだが URL 未同期」を区別して報告する
