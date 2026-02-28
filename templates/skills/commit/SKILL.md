---
name: commit
description: Use when creating a git commit from current changes with a Conventional Commits message.
argument-hint: "[message]"
---

# Commit

変更内容を確認し、Conventional Commits 形式で安全にコミットする。

## Workflow

1. `git status` で変更状態を確認する
2. `git diff` と `git diff --staged` で差分を確認する
3. 機密情報混入をチェックする
4. 必要ファイルのみ個別に `git add <file>` する
5. `type(scope): description` 形式でコミットする

## Commit Message

Conventional Commits 形式に従う:

- タイトル: 50 文字以内、命令形で記述
- 形式: `type(scope): description`
- 3 行目以降に箇条書きで詳細説明を記載

コミットメッセージの詳細説明には以下の 3 項目を含める:

1. **作業指示内容**: ユーザーから受けた指示の要約。何を依頼されたか
2. **計画とその背景・理由**: 採用したアプローチとその理由。なぜこの方法を選んだか
3. **実際の作業内容**: 具体的に行った変更内容。何をどう変更したか

### サンプル

```text
feat(auth): JWT トークンのリフレッシュ機能を追加

## 作業指示内容
- ログイン状態がすぐ切れる問題の解消を行う
- トークンの自動更新機能が必要

## 作業計画と背景・理由
- リフレッシュトークン方式を採用し、UX を損なわず安全に延長
- httpOnly cookie でリフレッシュトークンを管理し XSS リスクを低減

## 実際の作業内容
- lib/auth/refresh.ts を新規作成
- middleware.ts にトークン検証・更新ロジックを追加
- テスト 12 件を追加（カバレッジ 85%）
```

## Safety Rules

- `git add -A` / `git add .` は使わない
- push はユーザーが明示した場合のみ実行する
- Co-Authored-By は付けない（グローバル設定で無効化済み）
