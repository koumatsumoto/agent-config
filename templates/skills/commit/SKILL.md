---
name: commit
description: Create a git commit with a structured Conventional Commits message. Use when the user requests a commit, says "commit", "コミットして", "変更を保存して".
argument-hint: "[message]"
---

# Commit

変更内容を確認し、Conventional Commits 形式で安全にコミットする。

## Workflow

1. `git status` / `git diff` で変更内容を確認する
2. ユーザーが `$ARGUMENTS` でメッセージを指定した場合、タイトルの参考情報として扱う
3. 必要ファイルのみ個別に `git add <file>` する
4. ステージ済みファイルに機密情報がないか検証する
   - ファイル: `.env*`, `*.pem`, `*.key`, `*credentials*`
   - 文字列: `AKIA`, `sk-`, `password=`, `secret=` 等
   - **検出時はコミットを中止し、ユーザーに報告する**
5. 下記の Commit Message 形式に従ってコミットする
6. `git log -1 --stat` でコミット結果を確認し、ユーザーに報告する

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

**作業背景**
- ログイン状態がすぐ切れる問題の解消を依頼された

**計画と理由**
- リフレッシュトークン方式を採用し httpOnly cookie で管理

**作業内容と結果**
- lib/auth/refresh.ts 新規作成、middleware.ts に検証ロジック追加
```

```text
fix(api): ページネーションのオフセット計算を修正

**作業背景**
- 2ページ目以降で同じデータが表示されるバグ報告

**計画と理由**
- off-by-one エラーが原因。offset 計算式を (page - 1) * limit に修正

**作業内容と結果**
- src/api/pagination.ts の calculateOffset 関数を修正、テスト追加
```

```text
refactor(db): クエリビルダーを repository パターンに移行

**作業背景**
- 各ハンドラに SQL が散在しテスト困難との指摘

**計画と理由**
- repository パターンで DB アクセスを集約しモック可能に

**作業内容と結果**
- UserRepository, OrderRepository を新規作成、既存ハンドラから直接クエリを除去
```

## Safety Rules

- `git add -A` / `git add .` は使わない（必ず個別にファイルを指定する）
- `git commit --no-verify` は使わない（pre-commit hook をバイパスしない）
- push はユーザーが明示した場合のみ実行する
- `--force` / `-f` push はしない（ユーザーが指示しても確認を求める）
