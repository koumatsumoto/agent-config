---
name: km:github-workflow
description: Reference and orchestrate the basic GitHub PR delivery workflow (precheck, plan, develop, verify, report). Consult for the branch / commit / PR / issue-linkage flow; use directly when the user clearly wants to finish with a PR. Delegates planning to km:plan, independent deep review to km:review, commit to km:commit.
argument-hint: "[issue-number]"
---

# GitHub Workflow

GitHub 管理リポジトリで変更を PR として届けるための基本ワークフロー。流れと委譲先だけを定義し、詳細は各 skill に委ねる（計画: km:plan / 独立レビュー: km:review / コミット: km:commit）。メインが計画・判断・統合・完了確認を所有し、検証・レビューはリスクに比例させる（guideline「オーケストレーション」「リスク比例の検証・レビュー」の適用形）。

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
- **委譲判断**: 分割の利益（並列性・文脈分離）が起動・引き渡し・再統合のコストを上回る場合だけ、入力・期待成果・検証条件を固定した bounded task として実装 worker に切り出す。小さな局所変更・共有文脈が大きい変更・実装中も設計判断が要る変更はメインが直接実装する。worker の成果物はメインが完了条件に照らして検証してから統合する
- 既存コードの様式・責務境界に合わせ、完了条件を満たす最小限の動く変更を実装する
- 気付いた改善点は km:kaizen の capture 規約に従い、その場で `.kaizen/` に 1 行残す（会話 context に留めない）。dest（`pr` / `repo` / `workflow` / `knowledge`）は気づいた時点で付ける

## 3. 検証とレビュー

- **完了確認（常時・メインの責務）**: 完了条件・差分・テスト / 検証結果を照合し、無関係変更の混入がないことを確かめる。低リスク変更はこの確認で閉じる。独立レビューを省いた場合は、その判断根拠（低リスク判定）を報告に 1 行残す
- **独立レビュー（km:review）を起動する条件**:
  - **高影響領域（hard gate・必須）**: security / 認証・認可 / 秘密情報 / データ移行・削除 / 不可逆操作 / 公開契約・スキーマ / 広範囲な設計変更に触れるとき。判定は列挙への字面一致でなく影響の性質（不可逆性・攻撃面・信頼境界・波及範囲）で行い、迷ったら起動側に倒す
  - ユーザーが明示的にレビューを依頼したとき（変更規模によらず）
  - 重要な不確実性が残り、独立視点で確信度が上がるとき
- km:review の判定が BLOCKED の間は、指摘に対応して再レビューを繰り返す（PASS まで）。収束しなければユーザーに委ねる

## 4. 報告

- km:commit でコミットし、ブランチを push し、PR を作成（既存があれば更新）する
- issue があれば PR 本文に独立行で `Closes #<num>` を入れる（複数 PR に分けるなら中間は `Refs #<num>`、最終だけ `Closes #<num>`）
- 対象 issue が **km:plan 管理**（本文に `<!-- km:plan:managed -->` marker）で「実装時確認事項」節を持つ場合、各項目の **消化結果**を PR 本文・報告に含める（該当作業単位の検証に紐付いていればその確認結果、対応しないなら残す理由）。km:plan が「実装後に詰める」として委譲した項目を handoff で silent drop させない（`.kaizen/` の改善点 triage とは別系統。こちらは issue 本文の委譲項目が対象）
- CI / checks は見られれば確認して結果を報告に含める
- `.kaizen/` に記録した改善点を km:kaizen の Report 時 triage で片付ける（`pr` は同 PR で対応済み、`repo` は follow-up issue 化、`workflow` は残置と件数、`knowledge` は fold 先で振り分け）。PR URL・変更要約・検証結果とあわせて、triage の結果を**ユーザー向けの言葉**で報告する（何を直したか / どの issue を立てたか等。`dest`・`sweep` 等の内部機構語は出さない）。改善点がゼロなら「改善点: なし」の類は書かない

## Rules

- `--force` push しない
- issue / PR 本文は `gh ... --body-file - <<'EOF'` で渡す（`--body "..."` や非クォート heredoc は backtick / `$()` が展開され事故るため使わない）
- branch 作成 / push / PR 作成の要求が曖昧なら、先にユーザーに確認する
