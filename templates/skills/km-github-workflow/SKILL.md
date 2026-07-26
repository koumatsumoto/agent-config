---
name: km-github-workflow
description: GitHub 管理 repo で変更を PR として届けるワークフローと、その delivery 契約（ブランチ・commit・PR・issue 連携・follow-up issue・完了報告）。「PR にして」「PR まで仕上げて」で起動する。計画の作り込みは km-plan、独立レビューは km-review、コミットは km-commit へ委ねる。
argument-hint: "[issue-number]"
---

# GitHub Workflow

**Plan → Develop → Verify → Report。** 流れ自体は repo の guideline と共有し、本 skill は **delivery 固有の契約** — 何を守れば変更が PR として安全に届くか — を持つ。計画の作り込みは km-plan、独立レビューは km-review、コミットは km-commit。

## Context

- Repo / base: !`gh repo view --json nameWithOwner,defaultBranchRef -q '.nameWithOwner + " (base: " + .defaultBranchRef.name + ")"' 2>/dev/null || echo "NOT-A-GITHUB-REPO"`
- Branch: !`git branch --show-current`
- Status: !`git status --short`
- 現ブランチの PR: !`gh pr view --json number,state,url -q '"#" + (.number|tostring) + " " + .state + " " + .url' 2>/dev/null || echo "(none)"`

`NOT-A-GITHUB-REPO` は GitHub 管理 repo でないか `gh` を使えない状態を意味する。**何も変更せず停止する。** Context が展開されていなければ同じコマンドを自分で走らせてから判断する。base は `defaultBranchRef`。`$ARGUMENTS` の issue 番号は今回の対象 issue。

## Plan

- **base へ直接コミット・push しない。** 変更は必ずブランチを切って PR で届ける。ブランチは base から切る
- issue と PR はセット。ユーザーが「issue 不要・PR だけ」と明示したときだけ issue を作らない
- 論点が少なくクリアなら本 skill で簡易 issue（目的・完了条件を最小限）を作る。設計判断が多く計画を作り込むべきなら km-plan へ委ねる

## Develop

- ブランチを切る前に作業ツリーの状態を見て、**無関係な未コミット変更を持ち込まない**。混在していれば分離を確認する
- 作業中に見つけた今回の成果物に関係する欠陥は、**記録を修正の代わりにせず**同じ PR で直す
- スコープ外の発見は、後続対応の価値を説明できるものだけ follow-up issue にする。一時的なもの・価値を説明できないものは残さない

## Verify

- **完了確認は常時メインが行う。** 完了条件・差分・テスト / 検証結果を照合し、無関係変更が混入していないことを確かめる
- **km-review を起動する条件**: 高影響領域に触れる、ユーザーが明示的にレビューを依頼した、重要な不確実性が残る。高影響かは**影響の性質**（不可逆性・攻撃面・信頼境界・波及範囲）で判定する — 領域名の一覧に字面で一致するかではない。迷ったら起動する
- 起動を省いたときは、**低リスク判定の根拠を報告に 1 行残す**
- `BLOCKED` の間は指摘に対応して再レビューを `PASS` まで繰り返す。収束しなければユーザーに委ねる

## Report

- km-commit でコミットし、ブランチを push し、PR を作成する（既存があれば更新する）
- issue には PR 本文の**独立行** `Closes #<num>` で連携する。複数 PR に分けるなら最終だけ `Closes`、中間は `Refs`
- PR 本文には最終差分を理解するのに必要な背景・判断を書く。**内部タスク ID・逐次の作業ログ・レビュー反映の往復履歴は書かない**
- 対象 issue が km-plan 管理（本文に `<!-- km:plan:managed -->`）で「実装時確認事項」節を持つなら、各項目の消化結果（検証に紐付く確認結果 / 対応しないなら残す理由）を PR 本文と報告に含め、silent drop させない
- CI / checks は見られれば確認して結果を報告に含める
- follow-up issue を作ったら URL と要旨を報告する。該当する発見が無ければ「改善点なし」のような定型報告はしない

## 安全規約

- **`--force` push しない**
- **issue / PR 本文は公開前に抽象化する** — credential / token、実在の個人パス、非公開 repo 名、個人環境の識別子を含まない形にする。issue も PR も等しく公開面
- issue / PR 本文は `gh ... --body-file - <<'EOF'` で渡す。`--body "..."` や非クォートの heredoc は backtick / `$(...)` が展開されて事故る
- branch 作成 / push / PR 作成の要求が曖昧なら、先にユーザーに確認する
