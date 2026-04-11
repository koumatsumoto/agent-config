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
  1. 作業背景
  2. 計画と理由
  3. 作業内容と結果

サンプル:

```text
feat(auth): add refresh token flow

**作業背景**
- セッション維持の改善を依頼された

**計画と理由**
- リフレッシュトークン方式を採用し httpOnly cookie で管理

**作業内容と結果**
- 更新 API と検証ロジックを追加し、既存ログイン処理に統合した
```

## Safety Rules

- `git add -A` / `git add .` は使わない
- `git commit --no-verify` は使わない
- push はこのスキルでは行わない
- `--force` / `-f` push はしない
