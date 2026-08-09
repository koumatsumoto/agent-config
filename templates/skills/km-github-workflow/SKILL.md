---
name: km-github-workflow
description: GitHubリポジトリの変更を、issue・ブランチ・コミット・PRまで一貫して提出する。「PRにして」などの依頼で使う。
argument-hint: "[issue-number]"
---

# GitHub Workflow

**計画、開発、検証、報告の順に進める。** 流れ自体はリポジトリのガイドラインと共有し、本skillはPR作成・提出に固有の契約を持つ。計画の作り込みは`km-plan`、独立レビューは`km-review`、コミットは`km-commit`へ委ねる。

## Context

- リポジトリ / 基点ブランチ: !`gh repo view --json nameWithOwner,defaultBranchRef -q '.nameWithOwner + " (base: " + .defaultBranchRef.name + ")"' 2>/dev/null || echo "NOT-A-GITHUB-REPO"`
- Branch: !`git branch --show-current`
- Status: !`git status --short`
- 現ブランチの PR: !`gh pr view --json number,state,url -q '"#" + (.number|tostring) + " " + .state + " " + .url' 2>/dev/null || echo "(none)"`

`NOT-A-GITHUB-REPO`はGitHub管理リポジトリでないか、`gh`を使えない状態を意味する。**何も変更せず停止する。** コンテキストが展開されていなければ、同じコマンドを実行してから判断する。基点ブランチは`defaultBranchRef`である。`$ARGUMENTS`のissue番号は今回の対象issueを示す。

## Plan

- **基点ブランチへ直接コミット・プッシュしない。** 変更は必ずブランチを切ってPRで届ける。ブランチは基点ブランチから切り、名前は`<type>/<issue番号>-<slug>`（例: `fix/184-settings-merge-permissions`）とする。typeはコミットと同じConventional Commitsの語（`feat` / `fix` / `refactor` / `docs`など）、slugは英小文字のkebab-caseとする。issueを作らない場合は`<type>/<slug>`とする
- issueとPRはセット。ユーザーが「issue不要・PRだけ」と明示したときだけissueを作らない
- 論点が少なくクリアなら本 skill で簡易 issue（目的・完了条件を最小限）を作る。次のいずれかなら km-plan へ委ねる。**設計判断の数だけでは委ねない**
  - 複雑で手戻りが大きい
  - 設計判断を別の実装担当へ引き継ぐ
  - 複数PRや移行方針を先にそろえる

## Develop

- ブランチを切る前に作業ツリーの状態を見て、**無関係な未コミット変更を持ち込まない**。混在していれば分離を確認する
- 作業中に見つけた今回の成果物に関係する欠陥は、**記録を修正の代わりにせず**同じ PR で直す
- 今回の範囲で直さない重要な問題は、後続issueとして記録する。一時的なものや価値を説明できないものは残さない

## Verify

- **完了確認は常時メインが行う。** 完了条件・差分・テスト / 検証結果を照合し、無関係変更が混入していないことを確かめる
- **完了確認のあと、変更の軽重にかかわらず km-review を通す。** 軽微な変更は km-review 内で「独立レビュア 0 名」と判定して閉じる。完了確認を済ませたことを理由に省略しない
- `BLOCKED`の間だけ、未解決の完了阻害要因を直して再確認する。**MEDIUM / LOWや、完了を妨げない指摘のために繰り返さない。** 収束しなければユーザーに委ねる

## Report

- km-commit でコミットし、ブランチを push し、PR を作成する（既存があれば更新する）
- issue には PR 本文の**独立行** `Closes #<num>` で連携する。複数 PR に分けるなら最終だけ `Closes`、中間は `Refs`
- PR 本文には最終差分を理解するのに必要な背景・判断を書く。**内部タスク ID・逐次の作業ログ・レビュー反映の往復履歴は書かない**
- 対象issueがkm-plan管理（本文に`<!-- km:plan:managed -->`）で「実装時確認事項」節を持つ場合は、各項目の確認結果または対応しない理由をPR本文と報告に含める
- 取得できるCIと検査結果を確認し、未確認ならその理由を報告する
- 後続issue を作ったら URL と要旨を報告する。該当する発見が無ければ「改善点なし」のような定型報告はしない

## 安全規約

- **`--force` push しない**
- **issue / PR 本文は公開前に抽象化する** — 実在の個人パス・非公開 repo 名・個人環境の識別子を含まない形にする。issue も PR も等しく公開面
- issue / PR 本文は `gh ... --body-file - <<'EOF'` で渡す。`--body "..."` や非クォートのヒアドキュメントは backtick / `$(...)` が展開されて事故る
- ユーザーがPRやissueの作成を明示し、対象と範囲が明確な場合は追加確認せず実行する。要求が曖昧な場合だけ先に確認する
