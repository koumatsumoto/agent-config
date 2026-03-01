---
name: doc-review
description: Review uncommitted document changes for accuracy, consistency, and readability before commit. Use this skill when the user asks to review documentation, check docs, or says "ドキュメントを確認して", "READMEをレビューして", "ドキュメントに問題ないか見て". Also use it proactively after creating or updating documentation as part of the standard workflow.
---

# Document Review

未コミットのドキュメント変更を対象に、正確性・一貫性・可読性をレビューする。

## Workflow

1. `git diff --name-only` で変更されたドキュメントファイルを収集する
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

問題ごとに以下の形式で報告する。

**Example:**

```
## HIGH: API エンドポイントの記述が実装と不一致

**場所**: docs/api.md「認証」セクション
**問題**: ドキュメントでは POST /auth/login と記載されているが、実装は POST /api/v1/auth/login。利用者が正しいエンドポイントにアクセスできない。
**修正**: パスを /api/v1/auth/login に更新する。
```
