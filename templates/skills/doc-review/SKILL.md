---
name: doc-review
description: Use when reviewing uncommitted document changes for accuracy, consistency, and readability before commit.
disable-model-invocation: true
---

# Document Review

未コミットのドキュメント変更を対象に、正確性・一貫性・可読性をレビューする。

## Use When

- ドキュメント作成・更新後にコミット前レビューをしたい
- 内容の正確性や構成の一貫性を確認したい

## Workflow

1. 変更ファイルを収集する（`git diff --name-only` でドキュメントファイルを抽出）
2. 重大度順で問題を抽出する
3. 各問題に該当箇所・影響・修正案を付ける
4. `CRITICAL/HIGH` があればコミットをブロックする

## Review Criteria

- **正確性**: 事実誤認、古い情報、矛盾する記述がないか
- **一貫性**: 用語・表記・構成が統一されているか
- **可読性**: 構成が論理的で、読み手にとって理解しやすいか
- **完全性**: 必要な情報が欠けていないか、説明が不十分な箇所がないか

## Severity Guide

- `CRITICAL`: 事実誤認、重大な情報の欠落、誤解を招く記述
- `HIGH`: 構成の不整合、重要な用語の不統一、説明不足
- `MEDIUM`: 可読性の低下、冗長な記述、軽微な不統一
- `LOW`: 表現の改善、体裁の微調整

## Output Format

- 重大度
- 位置（ファイル + 該当箇所）
- 問題の説明
- 推奨修正
