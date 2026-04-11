---
name: km:commit
description: Creates a Conventional Commits git commit for the current changes. Use when the user asks to commit, save, or record the work.
argument-hint: "[message]"
---

# Commit

変更内容を確認し、必要なファイルだけを安全にコミットする。

## Context

- Git status: !`git status`
- Changes: !`git diff HEAD`
- Branch: !`git branch --show-current`
- Recent commits: !`git log --oneline -10`

## Success Criteria

- ステージ対象を最小限に絞る
- 明らかな機密情報をステージしない
- Conventional Commits 形式で、背景と判断が分かるメッセージにする

## Workflow

1. Context を読み、`$ARGUMENTS` があればタイトルのヒントとして使う
2. 対象ファイルだけを個別に `git add <file>` でステージする
3. ステージ済み内容を見て、機密情報や誤ステージがないか確認する
4. Conventional Commits 形式でコミットする
5. `git log -1 --stat` で結果を確認する

## Secret Check

以下を検出したらコミットを止めて報告する:

- ファイル名: `.env*`, `*.pem`, `*.key`, `*credentials*`
- 文字列: `AKIA`, `sk-`, `password=`, `secret=`

## Commit Message

- タイトル: `type(scope): description`
- 本文は以下の 3 セクションを含める
  1. 作業背景（ユーザー指示や作業背景。課題・目的・依頼内容がわかる内容）
  2. 作業計画（設計判断や採用したアプローチ、判断理由やその意図を含む）
  3. 作業内容（具体的な変更内容。何を変更し、どう変わったか）

サンプル:

```text
feat(auth): add refresh token flow

**作業背景**
- ログイン状態が短時間で切れる問題の解消を依頼された
- アクセストークンの有効期限が15分で、更新手段がなかった

**作業計画**
- リフレッシュトークン方式を採用し httpOnly cookie で管理する
- アクセストークンの自動更新を middleware で透過的に行う設計を選択

**作業内容**
- lib/auth/refresh.ts を新規作成し、トークン更新ロジックを実装
- middleware.ts にトークン検証・自動更新処理を追加
- 既存のログイン処理にリフレッシュトークン発行を統合
```

## Safety Rules

- `git add -A` / `git add .` は使わない
- `git commit --no-verify` は使わない
- push はこのスキルのスコープ外
