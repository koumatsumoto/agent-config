# AI Agent Guideline

全プロジェクト共通の Claude Code 動作指針。プロジェクト固有の設定は各リポジトリの CLAUDE.md で上書きする。

## 主要原則

1. **Agent-First**: 複雑な作業は特化エージェントに委譲
2. **Parallel Execution**: 可能なら複数エージェントを並列実行
3. **Plan Before Execute**: 複雑な作業では Plan Mode
4. **Test-Driven**: 実装前にテスト
5. **Security-First**: セキュリティ妥協なし

## ワークフロー

- ユーザの指示は曖昧であることを前提とする。実装前に要求を分析し、積極的に質問して詳細を詰める
- 複雑な作業では Plan Mode で作業計画を作成してから実装する
- 作業が完了したら、git commit 前に包括的なセルフレビューを行う

## スタイル

- コード、コメント、ドキュメントに絵文字禁止

## Git

- Git Commit 時は `/commit` スキルを使う

## 参照

- @rules/security.md
- @rules/coding-style.md
- @rules/agents.md
