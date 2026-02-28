---
name: code-review
description: Use when reviewing uncommitted changes for security, regressions, and maintainability before commit.
disable-model-invocation: true
---

# Code Review

未コミット変更を対象に、セキュリティと保守性を主軸とした多角的レビューを行う。

## Use When

- 実装後にコミット前レビューをしたい
- セキュリティや回帰リスクを先に潰したい

## Workflow

1. 変更ファイルを収集する（`git diff --name-only`）
2. 信頼境界に触れる変更を優先的に確認する
3. 重大度順で問題を抽出する
4. 各問題に位置・影響・修正案を付ける
5. `CRITICAL/HIGH` があればコミットをブロックする

## Review Perspectives

- **セキュリティ**: 認証/認可、入力検証、機密漏えい、注入脆弱性
- **保守性**: 可読性、設計の一貫性、テスト不足
- **正確性**: バグ、仕様回帰、例外処理欠如

## Mandatory Blockers

以下を検出した場合はコミットをブロックする。

- ハードコードされたシークレット
- 認証・認可の欠如
- 非検証入力の直接利用（SQL、テンプレート、コマンド等）
- 重大な機密情報を含むログ/エラー出力

## Severity Guide

- `CRITICAL`: 機密漏えい、認可欠如、任意実行など即時悪用可能
- `HIGH`: 明確なバグ、仕様回帰、悪用可能な入力検証不足
- `MEDIUM`: 保守性低下、テスト不足、設計の不整合
- `LOW`: スタイルや微小改善

## Output Format

- 重大度
- 位置（ファイル + 行）
- 問題の説明（セキュリティ問題は悪用シナリオを含める）
- 推奨修正

## References

- `references/security-checklist.md` - セキュリティチェックリスト
