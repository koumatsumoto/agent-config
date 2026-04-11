---
name: km:github-workflow
description: Runs the branch-review-commit-push-PR workflow for a GitHub repository. Use when the user asks for a branch, a PR, or end-to-end GitHub delivery.
---

# GitHub Workflow

GitHub 管理リポジトリで、ブランチ作成から PR 作成までを完了するワークフロー。

## Context

- Branch: !`git branch --show-current`
- Status: !`git status --short`
- Upstream: !`git rev-parse --abbrev-ref @{u} 2>/dev/null || echo "(none)"`
- Unpushed: !`git log --oneline @{u}..HEAD 2>/dev/null`
- Remote: !`git remote -v 2>/dev/null | head -1`

## Success Criteria

- 今回の作業に対応するブランチで作業する
- レビュー結果を反映してからコミットする
- push と PR 作成まで完了し、URL と論点を共有する

## Entry Point

現在状態から開始位置を決める:

|状態|開始位置|
|---|---|
|`main` / `master` 上|Phase 1|
|作業ブランチ + 未コミット変更あり|Phase 2|
|作業ブランチ + 未 push コミットあり|Phase 3|
|push 済みで PR 未作成|Phase 3 の PR 作成|
|push 済みで既存 PR あり|Phase 3 の PR 更新確認|

無関係な未コミット変更や別件ブランチの疑いがあれば、先にユーザーへ確認する。

## Phase 1: ブランチ準備

1. 現在ブランチを確認する
2. `main` / `master` なら `type/short-description` 形式で新ブランチを切る
3. 既存作業ブランチなら、今回のタスク用かをブランチ名と最近のコミットで判断する

## Phase 2: レビューと修正

4. 実装後に `/km:review` を実行する
5. `CRITICAL` は勝手に修正せず、まず共有する
6. それ以外は原則対応するが、大規模修正や仕様変更は先に確認する
7. 修正後にもう一度 `/km:review` を行い、未解決の高重大度がないことを確認する

## Phase 3: 公開

8. `/km:commit` でコミットする
9. ブランチを push する
10. 既存 PR があれば再利用し、なければ GitHub で PR を作成する
11. PR URL、変更要約、見てほしい論点を共有する

## Decision Rules

- まだ議論や追加修正が残るなら Draft PR を使う
- レビュー対応まで済んでいれば通常 PR を使う
- PR タイトルは Conventional Commits 形式に合わせる
- PR 説明は日本語で書く

## Safety Rules

- 認証変更、権限付与、remote 変更は勝手に行わない
- `--force` push はしない
- PR 作成が完了したら主体的な作業は止める
