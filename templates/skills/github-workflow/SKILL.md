---
name: km:github-workflow
description: Reference and orchestrate the basic GitHub PR delivery workflow (precheck, plan, develop, review, report). Consult for the branch / commit / PR / issue-linkage flow; use directly when the user clearly wants to finish with a PR. Delegates planning to km:plan, review to km:review, commit to km:commit.
argument-hint: "[issue-number]"
---

# GitHub Workflow

GitHub 管理リポジトリで変更を PR として届けるための基本ワークフロー。流れと委譲先だけを定義し、詳細は各 skill に委ねる（計画: km:plan / レビュー: km:review / コミット: km:commit）。

## Context

- Repo / base: !`gh repo view --json nameWithOwner,defaultBranchRef -q '.nameWithOwner + " (base: " + .defaultBranchRef.name + ")"' 2>/dev/null || echo "NOT-A-GITHUB-REPO"`
- Branch: !`git branch --show-current`
- Status: !`git status --short`
- 現ブランチの PR: !`gh pr view --json number,state,url -q '"#" + (.number|tostring) + " " + .state + " " + .url' 2>/dev/null || echo "(none)"`

## 前提

Context だけで機械的に判定する。`gh repo view` が失敗（`NOT-A-GITHUB-REPO`）なら、GitHub 管理 repo でないか `gh` を使えない状態なので、何も変更せず停止する。base は `defaultBranchRef`。`$ARGUMENTS` に issue 番号があれば今回の対象 issue とする。

## 1. 計画

- 変更は必ず PR で届ける（base に直接コミット・push しない）
- 既定は issue を立てて着手し、PR で issue を閉じる（issue と PR はセット）。ユーザーが「issue は不要・PR だけ」と明示したときだけ issue を作らない
- 論点が少なくクリアなら本スキルで簡易 issue を作る。設計判断が多く計画を作り込むべきなら km:plan に委ねる
- 簡易 issue には目的と完了条件を最小限残す
- ブランチは base から切るのを基本とし、状況により別の作業ブランチから切ってもよい

## 2. 開発

- ブランチを切る前に `git status` を見て、無関係な未コミット変更を今回のブランチに持ち込まない。混在していれば分離を確認する
- 既存コードの様式・責務境界に合わせ、完了条件を満たす最小限の動く変更を実装する
- 気付いた改善点は km:kaizen の capture 規約に従い、その場で `.kaizen/` に 1 行残す（会話 context に留めない）。dest（`pr` / `repo` / `workflow` / `knowledge`）は気づいた時点で付ける

## 3. レビュー

- km:review でレビューする
- km:review の判定が BLOCKED の間は、指摘に対応して再レビューを繰り返す（PASS まで）。収束しなければユーザーに委ねる

## 4. 報告

- km:commit でコミットし、ブランチを push し、PR を作成（既存があれば更新）する
- issue があれば PR 本文に独立行で `Closes #<num>` を入れる（複数 PR に分けるなら中間は `Refs #<num>`、最終だけ `Closes #<num>`）
- CI / checks は見られれば確認して結果を報告に含める
- `.kaizen/` に記録した改善点を km:kaizen の Report 時 triage で片付ける（`pr` は同 PR で対応済み、`repo` は follow-up issue 化、`workflow` は残置と件数、`knowledge` は fold 先で振り分け）。PR URL・変更要約・検証結果とあわせて、triage の結果を**ユーザー向けの言葉**で報告する（何を直したか / どの issue を立てたか等。`dest`・`sweep` 等の内部機構語は出さない）。改善点がゼロなら「改善点: なし」の類は書かない

## Rules

- `--force` push しない
- issue / PR 本文は `gh ... --body-file - <<'EOF'` で渡す（`--body "..."` や非クォート heredoc は backtick / `$()` が展開され事故るため使わない）
- branch 作成 / push / PR 作成の要求が曖昧なら、先にユーザーに確認する
