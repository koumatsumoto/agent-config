---
name: security-review
description: Use when implementing or reviewing authentication, user input, secrets, API endpoints, payments, or other sensitive flows.
---

# Security Review

このスキルは、セキュリティレビューで見るべき論点を絞り込み、重大な問題を優先して検出する。
詳細チェック項目は参照ファイルに分離し、本文は実行フローに限定する。

## Use When

- 認証/認可を追加・変更する
- ユーザー入力やファイルアップロードを扱う
- API エンドポイントを追加する
- シークレットや決済など機密性の高い処理を扱う

## Review Workflow

1. データ分類と信頼境界を特定する
2. `references/web-app-checklist.md` を適用する
3. 指摘を重大度順に整理して報告する

## Severity Policy

- `CRITICAL`: 機密漏えい、認可欠如、任意実行など即時悪用可能
- `HIGH`: 実運用で悪用可能な入力検証不足や防御欠落
- `MEDIUM`: 条件付きで悪用可能、または防御の弱さ
- `LOW`: 改善推奨

## Mandatory Blockers

以下を検出した場合は出荷/コミットをブロックする。

- ハードコードされたシークレット
- 認証・認可の欠如
- 非検証入力の直接利用（SQL、テンプレート、コマンド等）
- 重大な機密情報を含むログ/エラー出力

## Output Format

各指摘に以下を含める。

- 重大度
- 位置（ファイル + 行）
- 悪用シナリオ
- 最小修正案

## References

- `references/web-app-checklist.md` - Web アプリ共通チェック
- `../../rules/security.md` - リポジトリ全体の既定ルール
