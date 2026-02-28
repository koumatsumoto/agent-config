---
name: commit
description: Create a git commit with a structured Conventional Commits message. Use when the user requests a commit or after completing a task that needs committing.
argument-hint: "[message]"
---

# Commit

変更内容を確認し、Conventional Commits 形式で安全にコミットする。

## Workflow

1. 変更内容を把握していない場合、`git status` / `git diff` で確認する
2. 機密情報混入をチェックする（.env、credentials、API キー等）
3. 必要ファイルのみ個別に `git add <file>` する
4. 下記の Commit Message 形式に従ってコミットする

## Commit Message

Conventional Commits 形式に従う。将来の開発者が変更の背景を理解できるよう、丁寧に十分な情報を記述すること。

- タイトル: `type(scope): description`（50文字以内、命令形）
- 本体 (3行目以降): 以下の 3 項目を含める

1. **作業背景**: ユーザーから受けた指示や背景。課題・目的・依頼内容がわかる内容
2. **計画と理由**: 採用したアプローチとその理由。なぜこの方法を選んだか
3. **作業内容と結果**: 具体的に行った変更内容。何をどう変更し、どうなったか

### サンプル

```text
feat(auth): JWT トークンのリフレッシュ機能を追加

## 作業背景
- ログイン状態がすぐ切れる問題の解消を依頼された

## 計画と理由
- リフレッシュトークン方式を採用し httpOnly cookie で管理

## 作業内容と結果
- lib/auth/refresh.ts 新規作成、middleware.ts に検証ロジック追加
```

## Safety Rules

- `git add -A` / `git add .` は使わない
- push はユーザーが明示した場合のみ実行する
