---
name: code-review
description: Use when reviewing uncommitted changes for security, regressions, and maintainability before commit.
disable-model-invocation: true
---

# Code Review

未コミット変更を対象に、重大な問題を優先してレビューする。

## Use When

- 実装後にコミット前レビューをしたい
- セキュリティや回帰リスクを先に潰したい

## Workflow

1. 変更ファイルを収集する（`git diff --name-only`）
2. 重大度順で問題を抽出する
3. 各問題に再現条件・影響・修正案を付ける
4. `CRITICAL/HIGH` があればコミットをブロックする

## Severity Guide

- `CRITICAL`: 認証/認可欠如、機密漏えい、注入脆弱性
- `HIGH`: 明確なバグ、仕様回帰、主要な例外処理欠如
- `MEDIUM`: 保守性低下、テスト不足、設計の不整合
- `LOW`: スタイルや微小改善

## Output Format

- 重大度
- 位置（ファイル + 行）
- 問題の説明
- 推奨修正

## References

- `../../rules/coding-style.md` - 品質基準の具体値
