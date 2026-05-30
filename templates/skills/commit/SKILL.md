---
name: km:commit
description: Creates a Conventional Commits git commit for the current staged/unstaged changes. Use whenever the user says "commit" / "コミットして" or otherwise asks to commit the current work.
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
- Conventional Commits 形式で、背景と判断が分かるメッセージにする
- 複数の独立した作業がまとまっている場合、明確に分割できるならコミットを分ける

## Workflow

1. Context を読み、`$ARGUMENTS` があればタイトルのヒントとして使う
2. 対象ファイルだけを個別に `git add <file>` でステージする
3. ステージ済み内容を見て誤ステージがないか確認する
4. Conventional Commits 形式でコミットする
5. `git log -1 --stat` で結果を確認する

変更が複数の独立した作業を含み、明確に分割できる場合のみ作業単位ごとに 1–5 を繰り返す。迷ったら分けない。

## Commit Message

- タイトル: `type(scope): description`
- 本文は以下の 3 セクションを含める
  1. 作業背景（課題・目的・制約・依頼内容。逐次の作業ログやレビュー反映履歴は除く）
  2. 作業計画（設計判断や採用したアプローチ、判断理由やその意図を含む）
  3. 作業内容（具体的な変更内容。何を変更し、どう変わったか）
- レビュー 1 ラウンド目で A、2 ラウンド目で B のような作業経緯ではなく、最終差分を理解するための背景・判断・変更内容を書く

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
