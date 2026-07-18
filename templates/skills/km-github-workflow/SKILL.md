---
name: km-github-workflow
description: Reference and orchestrate the basic GitHub PR delivery workflow (precheck, plan, develop, verify, report). Consult for the branch / commit / PR / issue-linkage flow; use directly when the user clearly wants to finish with a PR. Delegates planning to km-plan, independent deep review to km-review, commit to km-commit.
argument-hint: "[issue-number]"
---

# GitHub Workflow

GitHub 管理リポジトリで変更を PR として届ける基本ワークフロー。流れとこの workflow 固有の契約だけを定義し、詳細は各 skill に委ねる（計画: km-plan / 独立レビュー: km-review / コミット: km-commit）。

## Context

- Repo / base: !`gh repo view --json nameWithOwner,defaultBranchRef -q '.nameWithOwner + " (base: " + .defaultBranchRef.name + ")"' 2>/dev/null || echo "NOT-A-GITHUB-REPO"`
- Branch: !`git branch --show-current`
- Status: !`git status --short`
- 現ブランチの PR: !`gh pr view --json number,state,url -q '"#" + (.number|tostring) + " " + .state + " " + .url' 2>/dev/null || echo "(none)"`

## 前提

Context だけで機械的に判定する。`gh repo view` が失敗（`NOT-A-GITHUB-REPO`）なら、GitHub 管理 repo でないか `gh` を使えない状態なので、何も変更せず停止する。base は `defaultBranchRef`。`$ARGUMENTS` に issue 番号があれば今回の対象 issue とする。

## 1. 計画

- 変更は必ず PR で届ける（base に直接コミット・push しない）。既定は issue を立てて着手し PR で閉じる（issue と PR はセット）。ユーザーが「issue 不要・PR だけ」と明示したときだけ作らない
- 論点が少なくクリアなら本スキルで簡易 issue（目的・完了条件を最小限）を作る。設計判断が多く計画を作り込むべきなら km-plan に委ねる
- ブランチは base から切るのを基本とする

## 2. 開発

- ブランチを切る前に `git status` を確認し、無関係な未コミット変更を今回のブランチに持ち込まない（混在していれば分離を確認する）
- 作業中に見つけた今回の成果物に関係する欠陥は、記録を修正の代わりにせず同じ PR で直す
- スコープ外の発見は、後続対応の価値を説明できるものだけ報告前に follow-up issue 化する。一時的または価値を説明できないものは残さない

## 3. 検証とレビュー

- 完了確認は常時メインが行う: 完了条件・差分・テスト / 検証結果を照合し、無関係変更の混入がないことを確かめる。独立レビュー（km-review）は guideline ワークフロー 3 の条件（高影響領域・明示依頼・不確実性残存）で起動し、省いた場合は低リスク判定の根拠を報告に 1 行残す
- km-review が BLOCKED の間は、指摘に対応して再レビューを PASS まで繰り返す。収束しなければユーザーに委ねる

## 4. 報告

- km-commit でコミットし、ブランチを push し、PR を作成（既存があれば更新）する。issue には PR 本文の独立行 `Closes #<num>` で連携する（複数 PR に分けるなら最終だけ `Closes`、中間は `Refs`）
- 対象 issue が km-plan 管理（本文に `<!-- km:plan:managed -->` marker）で「実装時確認事項」節を持つ場合、各項目の消化結果（検証に紐付く確認結果 / 対応しないなら残す理由）を PR 本文・報告に含め、silent drop させない
- CI / checks は見られれば確認して結果を報告に含める
- follow-up issue を作成した場合は URL と要旨を報告する。該当する発見が無ければ「改善点なし」のような定型報告はしない

## Rules

- `--force` push しない
- issue 本文は公開前に credential / token、実在の個人パス、非公開 repo 名、個人環境の識別子を含まない形へ抽象化する
- issue / PR 本文は `gh ... --body-file - <<'EOF'` で渡す（`--body "..."` や非クォート heredoc は backtick / `$()` が展開され事故るため使わない）
- branch 作成 / push / PR 作成の要求が曖昧なら、先にユーザーに確認する
