---
name: km:github-workflow
description: >-
  Run the full GitHub dev workflow: branch creation, /km:review, /km:commit,
  push, and PR creation. Use when the user says "PRにして", "PR作って",
  "pr作る", "PRまでやって", "開発して", "実装して", or wants to develop
  features on a GitHub-managed repository.
---

# GitHub Workflow

GitHub で管理されているリポジトリでの開発フロー。
AI がコード変更を行い、PR として人間のレビューに提出する。PR 作成が AI の作業完了地点であり、以降は人間の判断に委ねる。

## Context

- Branch: !`git branch --show-current`
- Status: !`git status --short`
- Upstream: !`git rev-parse --abbrev-ref @{u} 2>/dev/null || echo "(none)"`
- Unpushed: !`git log --oneline @{u}..HEAD 2>/dev/null`
- Remote: !`git remote -v 2>/dev/null | head -1`

## エントリーポイント判定

Context の情報をもとに、現在の状態に応じた Phase から開始する。

| 状態 | 開始位置 |
|------|---------|
| main/master 上 | Phase 1 から |
| 作業ブランチ上で未コミット変更あり | Phase 2 から |
| 作業ブランチ上で変更なし（upstream 未設定または未 push コミットあり） | Phase 3 から |
| push 済みで PR 未作成 | Phase 3 の PR 作成から |
| 作業ブランチ上で変更なし・push 済み・PR 作成済み | Phase 1 のステップ 3 から（ブランチ再利用判断） |

## Phase 1: ブランチ準備

1. 現在のブランチを確認する
2. `main` または `master` なら、新しい作業ブランチを作成してから着手する
   - ブランチ名は `type/short-description` 形式にする（例: `feat/add-jwt-auth`, `fix/login-error`）
   - type は Conventional Commits の type に合わせる
3. すでに作業ブランチ上の場合、ブランチ名や直近のコミットから今回の作業用か判断する
4. 別件の作業ブランチの可能性がある場合は、ユーザーへ確認する
5. 無関係な未コミット変更があり、安全に切り分けできない場合は先にユーザーへ確認する

## Phase 2: レビューと対応

6. 作業が終わったら `/km:review` を実行する
7. CRITICAL が検出された場合は、修正を試みる前にユーザーへ報告し方針を確認する
8. それ以外の指摘は LOW を含め原則対応する
9. ただし大規模修正、影響範囲が大きい修正、仕様変更を伴う修正は対応前にユーザーへ確認する
10. 修正後、再度 `/km:review` を実行し指摘が解消されたことを確認する

## Phase 3: コミットと公開

11. `/km:commit` でコミットする（push は委譲せず、このスキルが行う）
12. 変更を push する。失敗した場合はエラー内容を確認し、認証・権限の問題ならユーザーへ確認する
13. GitHub の PR を作成する。失敗した場合はユーザーへ報告する
14. PR 作成後は URL、変更要約、ユーザーに見てほしい論点を添えてレビューを依頼する

## Decision Rules

- まだ実装やレビュー対応が残っている、または早めに共有したい場合は Draft PR を使う
- レビュー対応まで終わり、ユーザー確認に進める状態なら通常 PR を使う
- PR 作成前に、レビュー結果と最終変更内容が一致していることを確認する
- PR タイトルは Conventional Commits のタイトル形式に合わせる
- PR の説明文は日本語で書く
- ブランチ名は `type/short-description` 形式にする

## Safety Rules

- push や PR 作成に必要な認証や設定が足りない場合は、勝手に補完せずユーザーへ確認する
- 確認なしでは認証変更、権限付与、remote 変更のような副作用の強い操作は行わない
- `--force` push はしない（ユーザーが指示しても確認を求める）
- PR 作成が完了した時点で AI の主体的な作業は終了する。追加の変更は行わない
