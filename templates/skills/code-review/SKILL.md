---
name: code-review
description: Review uncommitted code changes for security vulnerabilities, regressions, and maintainability issues before commit. Use this skill whenever the user asks for a code review, quality check, security audit, or says things like "レビューして", "チェックして", "変更を確認して", "問題ないか見て". Also use it proactively after completing code changes as part of the standard workflow.
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

- **セキュリティ**: 認証/認可、入力検証、機密漏えい、注入脆弱性
- **保守性**: 可読性、設計の一貫性、テスト不足
- **正確性**: バグ、仕様回帰、例外処理欠如

## Mandatory Blockers

以下を検出した場合はコミットをブロックする。いずれも本番環境で発生するとユーザーデータの漏洩や不正アクセスにつながり、修復コストが極めて高い問題であるため。

- ハードコードされたシークレット（漏洩時のローテーションコストが甚大）
- 認証・認可の欠如（任意のユーザーがリソースにアクセス可能になる）
- 非検証入力の直接利用 — SQL、テンプレート、コマンド等（注入攻撃の入口になる）
- 重大な機密情報を含むログ/エラー出力（ログ収集経由で機密が拡散する）

## Severity Guide

- `CRITICAL`: 機密漏えい、認可欠如、任意実行など即時悪用可能
- `HIGH`: 明確なバグ、仕様回帰、悪用可能な入力検証不足
- `MEDIUM`: 保守性低下、テスト不足、設計の不整合
- `LOW`: スタイルや微小改善

## Output Format

問題ごとに以下の形式で報告する。

**Example:**

```
## CRITICAL: ハードコードされた API キー

**場所**: src/api/client.ts:42
**問題**: Stripe の API キーが文字列リテラルとして埋め込まれている。リポジトリにアクセスできる全員がキーを取得でき、不正課金に悪用される。
**修正**: 環境変数 `STRIPE_SECRET_KEY` から読み込むように変更する。
```

## References

- `references/security-checklist.md` — セキュリティチェックリスト。レビュー時に参照して漏れを防ぐ。
