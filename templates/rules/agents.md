# エージェント運用ルール

## 目的

サブエージェントは「必要なときだけ、明確な責務で」使う。

## 利用可能エージェント

配置場所: `~/.claude/agents/`

| エージェント | 主用途 |
| --- | --- |
| `planner` | 実装前の計画化 |
| `architect` | 設計判断とトレードオフ整理 |
| `build-error-resolver` | ビルド/型エラー復旧 |
| `code-reviewer` | 差分レビュー |
| `security-reviewer` | セキュリティレビュー |
| `refactor-cleaner` | 安全なクリーンアップ |

## 選定ガイド

- 変更前の整理: `planner`
- 設計判断が必要: `architect`
- ビルドが壊れている: `build-error-resolver`
- 実装後の品質確認: `code-reviewer`
- 認証/入力/API を触る: `security-reviewer`
- 未使用コード整理: `refactor-cleaner`

## 実行ルール

1. 1 タスク 1 主担当を基本にする
2. 独立な検証は並列実行を検討する
3. 依存関係がある作業は逐次で行う
4. 出力は「判断根拠」と「次アクション」を明示する
5. 過剰な分割や不要なエージェント起動を避ける

## 補足

Codex CLI 側では `agents/` は直接読まれないため、同等の運用は `skills/` と `AGENTS.md` で行う。
