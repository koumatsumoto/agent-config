---
name: orchestrate
description: Use when a complex task needs a multi-agent workflow across planning, implementation, and review.
disable-model-invocation: true
argument-hint: "[workflow-type] [task-description]"
---

# Orchestrate

複雑なタスクを、目的別のエージェント列で実行する。

## Use When

- 複数フェーズ（設計・実装・レビュー）を跨ぐ
- 単一エージェントでは見落としが出やすい

## Preset Workflows

- `feature`: `planner -> code-reviewer -> security-reviewer`
- `bugfix`: `build-error-resolver -> code-reviewer`
- `refactor`: `architect -> code-reviewer`
- `security`: `security-reviewer -> code-reviewer -> architect`

## Execution Rules

1. 前段の出力を以下の構造で要約し次段へ引き継ぐ:
   Context / Findings / Files Modified / Open Questions
2. 独立可能な検証は並列実行する
3. 各段で未解決事項を明示する
4. 最後に統合レポートを返す

## Final Report

- 実行したワークフロー
- 主要判断
- 変更ファイル
- テスト結果
- セキュリティ所見
- 推奨ステータス（SHIP / NEEDS WORK / BLOCKED）
