---
name: code-review
description: Reviews uncommitted code changes for security vulnerabilities, regressions, and maintainability issues before commit. Triggers on code review, quality check, security audit requests, or phrases like "レビューして", "チェックして", "変更を確認して", "問題ないか見て". Also triggers proactively after completing code changes as part of the standard workflow.
---

# Code Review

未コミット変更を対象に、セキュリティと保守性を主軸とした多角的レビューを行う。

## Workflow

1. `git diff --name-only` で変更ファイルを収集する
2. 信頼境界（外部入力、認証、データ永続化）に触れる変更を優先的に確認する
3. 重大度順で問題を抽出する
4. 各問題に位置・影響・修正案を付ける
5. `CRITICAL/HIGH` があればコミットをブロックする

## Review Perspectives

- **セキュリティ**: 認証/認可、入力検証、機密漏えい、注入脆弱性、依存関係の安全性
- **堅牢性**: 例外処理、エラー伝播、fail-open の防止、境界値
- **保守性**: 可読性、設計の一貫性、テスト不足
- **正確性**: バグ、仕様回帰、データ整合性

## Mandatory Blockers

以下を検出した場合はコミットをブロックする。いずれも本番環境で発生するとユーザーデータの漏洩や不正アクセスにつながり、修復コストが極めて高い問題であるため。

- ハードコードされたシークレット — API キー、パスワード、トークン等（漏洩時のローテーションコストが甚大）
- 認証・認可の欠如（任意のユーザーがリソースにアクセス可能になる）
- 非検証入力の直接利用 — SQL、テンプレート、シェルコマンド、パス結合等（注入攻撃の入口になる）
- 重大な機密情報を含むログ/エラー出力（ログ収集経由で機密が拡散する）
- 例外の握り潰しによる fail-open（認証・認可・決済の try-catch で例外時にアクセスを許可してしまう）

## Severity Guide

- `CRITICAL`: 機密漏えい、認可欠如、任意コード実行、fail-open など即時悪用可能
- `HIGH`: 明確なバグ、仕様回帰、悪用可能な入力検証不足、危険な依存関係
- `MEDIUM`: 保守性低下、テスト不足、設計の不整合、不適切なエラー処理
- `LOW`: スタイルや微小改善

## Security Checklist (OWASP Top 10:2025)

### Secrets Management

- ソースコードにシークレット（API キー、パスワード、トークン）を埋め込まない
- 秘密情報は環境変数またはシークレットストアで管理する
- 環境変数の存在チェックを実装し、未設定時は起動を拒否する
- シークレットをログやエラーメッセージに出力しない

### Input Validation

- すべての外部入力（リクエストパラメータ、ヘッダー、ファイルアップロード）を検証する
- スキーマベースのバリデーション（Zod, JSON Schema 等）を優先する
- サイズ制限・型制限・許可リストを設定する

### Injection Prevention

- SQL は必ずパラメータ化クエリを使う
- テンプレートエンジンにユーザー入力を直接展開しない
- シェルコマンドにユーザー入力を直結しない（引数配列を使う）
- パス結合は正規化してディレクトリトラバーサルを防ぐ

### Authentication / Authorization

- 認証必須ルートを明示し、デフォルトで認証を要求する
- リソースアクセスごとに認可を検証する（IDOR 防止）
- 権限不足時は安全な失敗（403/404）を返す

### Browser Security

- HTML 出力箇所は XSS 対策する（自動エスケープ、CSP）
- CSRF 防御を適用する（トークン、SameSite cookie）
- セキュリティヘッダーを設定する（CSP, X-Content-Type-Options 等）

### Error Handling / Fail-Secure (OWASP A10)

認証・認可・決済などの重要処理で例外を握り潰すと fail-open になる。

- エラーに内部構造・秘密情報を含めない
- セキュリティ関連の try-catch で例外時にデフォルト許可しない
- 予期しない状態では安全側に倒す（deny by default）
- ログは PII の最小化とマスキングを行う

### Supply Chain Security (OWASP A03)

依存関係を経由した攻撃が急増している。

- 依存パッケージのバージョンを固定し、lockfile をコミットする
- CI では再現可能インストール（`npm ci`, `pip install --require-hashes` 等）を使う
- 依存の脆弱性スキャンを定期実行する
- 新規依存の追加時はメンテナンス状況と信頼性を確認する

### Abuse Protection

- 重要 API にレート制限を付与する
- 認証・決済系は監査ログを残す
- 認証失敗の回数制限やアカウントロックを導入する

## Output Format

問題ごとに以下の形式で報告する。

**Example:**

```
## CRITICAL: ハードコードされた API キー

**場所**: src/api/client.ts:42
**問題**: Stripe の API キーが文字列リテラルとして埋め込まれている。リポジトリにアクセスできる全員がキーを取得でき、不正課金に悪用される。
**修正**: 環境変数 `STRIPE_SECRET_KEY` から読み込むように変更する。
```
