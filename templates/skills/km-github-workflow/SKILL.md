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

- **base へ直接コミット・push しない。** 変更は必ずブランチを切って PR で届ける。ブランチは base から切り、名前は `<type>/<issue番号>-<slug>`（例: `fix/184-settings-merge-permissions`）。type は commit と同じ Conventional Commits の語（`feat` / `fix` / `refactor` / `docs` など）、slug は英小文字 kebab-case。issue を作らない場合は `<type>/<slug>`
- issue と PR はセット。ユーザーが「issue 不要・PR だけ」と明示したときだけ issue を作らない
- 論点が少なくクリアなら本 skill で簡易 issue（目的・完了条件を最小限）を作る。ゴール / スコープ / 戻せない選択 / 実現可能性を誤ると高くつく、背景・設計理由・変更範囲を別の実装 agent へ引き渡す、複数の変更範囲・PR・移行の方向を先に揃える、のいずれかなら km-plan へ委ねる。設計判断の数だけでは委ねない

## Develop

- ブランチを切る前に作業ツリーの状態を見て、**無関係な未コミット変更を持ち込まない**。混在していれば分離を確認する
- 作業中に見つけた今回の成果物に関係する欠陥は、**記録を修正の代わりにせず**同じ PR で直す
- スコープ外の発見は、後続対応の価値を説明できるものだけ follow-up issue にする。一時的なもの・価値を説明できないものは残さない

## Verify

- **完了確認は常時メインが行う。** 完了条件・差分・テスト / 検証結果を照合し、無関係変更が混入していないことを確かめる
- **完了確認のあと、変更の軽重にかかわらず km-review を通す。** 軽微な変更は km-review 内で「独立レビュア 0 名」と判定して閉じる。完了確認を済ませたことを理由に省略しない
- `BLOCKED` の間だけ、未解決 blocker を直して recheck する。**MEDIUM / LOW や non-blocking な指摘のためにループしない。** 収束しなければユーザーに委ねる

## Report

- km-commit でコミットし、ブランチを push し、PR を作成する（既存があれば更新する）
- issue には PR 本文の**独立行** `Closes #<num>` で連携する。複数 PR に分けるなら最終だけ `Closes`、中間は `Refs`
- PR 本文には最終差分を理解するのに必要な背景・判断を書く。**内部タスク ID・逐次の作業ログ・レビュー反映の往復履歴は書かない**
- 対象 issue が km-plan 管理（本文に `<!-- km:plan:managed -->`）で「実装時確認事項」節を持つなら、各項目が指す消化時点と判断根拠に対応づけて消化結果（確認結果 / 対応しないなら残す理由）を PR 本文と報告に含め、silent drop させない
- CI / checks は見られれば確認して結果を報告に含める
- follow-up issue を作ったら URL と要旨を報告する。該当する発見が無ければ「改善点なし」のような定型報告はしない

## 安全規約

- **`--force` push しない**
- **issue / PR 本文は公開前に抽象化する** — 実在の個人パス・非公開 repo 名・個人環境の識別子を含まない形にする。issue も PR も等しく公開面
- issue / PR 本文は `gh ... --body-file - <<'EOF'` で渡す。`--body "..."` や非クォートの heredoc は backtick / `$(...)` が展開されて事故る
- branch 作成 / push / PR 作成の要求が曖昧なら、先にユーザーに確認する
