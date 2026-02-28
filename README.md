# agent-config

Claude Code と OpenAI Codex CLI の設定を同じリポジトリで管理するための構成です。

## 対応CLI

- Claude Code
- OpenAI Codex CLI

## 運用ポリシー

- **編集元は Claude-first**: このリポジトリ内の `templates/` 配下 (`CLAUDE.md` / `agents/` / `rules/` / `skills/`) を編集する
- Codex 側の `~/.codex/AGENTS.md` は反映先。**直接編集しない**
- 二重管理を避けるため、インストール時はリンク優先（必要ならコピーへフォールバック）
- サブエージェントは最小構成を維持し、不要になったものは削除する
- 1 タスク 1 主担当を基本にし、独立検証のみ並列化する
- Codex CLI は `agents/` を直接読まないため、`AGENTS.md` / `rules` / `skills` を正とする

## ディレクトリ構造

- `templates/` - デプロイ対象のテンプレート群
  - `CLAUDE.md` - 共通エージェント方針（Claude と Codex AGENTS で共用）
  - `agents/` - Claude 用エージェント定義
  - `rules/` - ルール定義
  - `skills/` - スキル定義（スラッシュコマンド + 参照スキル。Claude / Codex で共用）
  - `config.toml` - Codex CLI 用の最小設定テンプレート
- `install.sh` - `~/` 配下へ反映するインストールスクリプト
- `docs/` - プロジェクトドキュメント
- `.claude/` - プロジェクト固有の Claude 設定

## セットアップ

推奨コマンド:

```bash
bash install.sh
```

このコマンドは以下を反映します:

- `~/.claude/`:
  - `CLAUDE.md`（`templates/CLAUDE.md` から反映）
  - `agents/`（`templates/agents/` から反映）
  - `rules/`（`templates/rules/` から反映）
  - `skills/`（`templates/skills/` から反映）
- `~/.codex/`:
  - `AGENTS.md`（`templates/CLAUDE.md` から反映）
  - `config.toml`（`templates/config.toml` から反映）
- `~/.agents/`:
  - `skills/`（`templates/skills/` から反映）

`install.sh` は引数なしで、Claude/Codex の両方を一括反映します。

## OS別メモ

- Ubuntu/Linux:
  - 通常は symlink で反映される
- Windows (Git Bash):
  - シンボリックリンク権限が不足する環境では自動でコピーへフォールバック

## 反映先マッピング

| Repository Source | Destination |
| --- | --- |
| `templates/CLAUDE.md` | `~/.claude/CLAUDE.md` |
| `templates/agents/` | `~/.claude/agents/` |
| `templates/rules/` | `~/.claude/rules/` |
| `templates/skills/` | `~/.claude/skills/` |
| `templates/CLAUDE.md` | `~/.codex/AGENTS.md` |
| `templates/config.toml` | `~/.codex/config.toml` |
| `templates/skills/` | `~/.agents/skills/` |

## エージェント運用（2026-02 時点）

`templates/agents/` は Claude Code のサブエージェント定義。現在は次の 6 つに集約:

- `planner` - 実装前の計画化
- `architect` - 設計判断とトレードオフ整理
- `build-error-resolver` - ビルド/型エラー復旧
- `code-reviewer` - 差分レビュー
- `security-reviewer` - セキュリティレビュー
- `refactor-cleaner` - 安全なクリーンアップ

運用詳細は `templates/rules/agents.md` を参照。

## 公式仕様（参照元）

- Claude Code
  - Skills: `https://code.claude.com/docs/en/skills`
  - Sub-agents: `https://code.claude.com/docs/en/sub-agents`
  - Memory (`CLAUDE.md`): `https://code.claude.com/docs/en/memory`
  - Settings: `https://code.claude.com/docs/en/settings`
- OpenAI Codex CLI
  - CLI Overview: `https://developers.openai.com/codex/cli`
  - Config Basics: `https://developers.openai.com/codex/config-basic`
  - Config Reference: `https://developers.openai.com/codex/config-reference`
  - Rules: `https://developers.openai.com/codex/rules`
  - AGENTS.md: `https://developers.openai.com/codex/guides/agents-md`
  - Skills: `https://developers.openai.com/codex/skills`

## 既存ファイルの保護

`install.sh` は同名ファイル/ディレクトリが既に存在する場合、
`*.bak.<timestamp>` へ退避してから置換します。

## スキル一覧

### スラッシュコマンド（`disable-model-invocation: true`）

| スキル | 説明 |
| --- | --- |
| `code-review` | セキュリティ/保守性を主軸とした多角的レビュー |
| `commit` | Conventional Commits 形式で git commit |

## ライセンス

MIT License。詳細は `LICENSE` を参照。
