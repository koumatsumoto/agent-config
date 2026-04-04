---
name: km:commit
description: Create a git commit with a structured Conventional Commits message. Use when the user requests a commit, says "commit", "コミットして", "変更を保存して".
argument-hint: "[message]"
---

# Commit

変更内容を確認し、Conventional Commits 形式で安全にコミットする。

## Context

- Git status: !`git status`
- Changes: !`git diff HEAD`
- Branch: !`git branch --show-current`
- Recent commits: !`git log --oneline -10`

## Workflow

1. Context を分析する。`$ARGUMENTS` があればタイトルのヒントとして使用する
2. 必要ファイルのみ個別に `git add <file>` でステージする
3. ステージ済みファイルに機密情報がないか検証する
   - ファイル名: `.env*`, `*.pem`, `*.key`, `*credentials*`
   - 文字列パターン: `AKIA`, `sk-`, `password=`, `secret=` 等
   - **検出時はコミットを中止し、ユーザーに報告する**
4. 下記の Commit Message 形式に従ってコミットする
5. `git log -1 --stat` でコミット結果を確認し、ユーザーに報告する

ステージとコミットを可能な限り少ないツール呼び出しで実行すること。複数の `git add` は並列実行可能。

## Commit Message

Conventional Commits 形式に従う。基本は下記の形式に従い、Context の Recent commits はスコープ命名や言語の参考にする。

- タイトル: `type(scope): description`（50文字以内、命令形）
- 本体 (3行目以降): 以下の 3 項目を含める

1. **作業背景**: ユーザーから受けた指示や背景。課題・目的・依頼内容がわかる内容
2. **計画と理由**: 採用したアプローチとその理由。なぜこの方法を選んだか
3. **作業内容と結果**: 具体的に行った変更内容。何をどう変更し、どうなったか

### サンプル

```text
feat(auth): JWT トークンのリフレッシュ機能を追加

**作業背景**
- ログイン状態がすぐ切れる問題の解消を依頼された

**計画と理由**
- リフレッシュトークン方式を採用し httpOnly cookie で管理

**作業内容と結果**
- lib/auth/refresh.ts 新規作成、middleware.ts に検証ロジック追加
```

## Safety Rules

- `git add -A` / `git add .` は使わない（必ず個別にファイルを指定する）
- `git commit --no-verify` は使わない（pre-commit hook をバイパスしない）
- push は他のスキルや明示的な指示で求められた場合のみ実行する
- `--force` / `-f` push はしない（ユーザーが指示しても確認を求める）
