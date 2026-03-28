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
  - `rules/` - ルール定義
  - `skills/` - スキル定義（スラッシュコマンド + 参照スキル。Claude / Codex で共用）
  - `keybindings.json` - キーバインド設定（Shift+Enter で改行）
  - `statusline.sh` - ステータスライン表示スクリプト（モデル・コンテキスト・コスト・5hレート制限・ブランチ）
  - `config.toml` - Codex CLI 用の最小設定テンプレート
- `scripts/` - ユーティリティスクリプト（pack-md.sh 等）
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
  - `rules/`（`templates/rules/` から反映）
  - `skills/`（`templates/skills/` から反映）
  - `keybindings.json`（`templates/keybindings.json` から反映）
  - `statusline.sh`（`templates/statusline.sh` から反映、`chmod 700`）
- `~/.codex/`:
  - `AGENTS.md`（`templates/CLAUDE.md` から反映）
  - `config.toml`（`templates/config.toml` から反映）
- `~/.agents/`:
  - `skills/`（`templates/skills/` から反映）

`install.sh` は引数なしで、Claude/Codex の両方を一括反映します。

## ターミナルカスタマイズ

`install.sh` は以下のターミナルカスタマイズ設定も反映します:

- **ステータスライン** (`statusline.sh`): モデル名・コンテキスト使用率（色付きプログレスバー）・セッションコスト・5時間レート制限・Git ブランチを常時表示
- **キーバインド** (`keybindings.json`): `Shift+Enter` で改行

ステータスラインを有効にするには `settings.json` に以下を追加（パスは自分の環境に合わせる）:

```json
{
  "statusLine": {
    "type": "command",
    "command": "/home/<user>/.claude/statusline.sh",
    "padding": 2
  }
}
```

通知フック、Output Styles、permissions のセキュリティハードニング等の詳細は `docs/claude-code-terminal-customization.md` を参照。

## Markdown 軽量化

AI に渡す前の Markdown から余分な空白やテーブルのパディングを減らしたい場合は `scripts/pack-md.sh` を使います。

```bash
./scripts/pack-md.sh README.md > README.llm.md
./scripts/pack-md.sh -i README.md
```

## OS別メモ

- Ubuntu/Linux:
  - 通常は symlink で反映される
- Windows (Git Bash):
  - シンボリックリンク権限が不足する環境では自動でコピーへフォールバック

## 反映先マッピング

| Repository Source | Destination |
| --- | --- |
| `templates/CLAUDE.md` | `~/.claude/CLAUDE.md` |
| `templates/rules/` | `~/.claude/rules/` |
| `templates/skills/` | `~/.claude/skills/` |
| `templates/keybindings.json` | `~/.claude/keybindings.json` |
| `templates/statusline.sh` | `~/.claude/statusline.sh` |
| `templates/CLAUDE.md` | `~/.codex/AGENTS.md` |
| `templates/config.toml` | `~/.codex/config.toml` |
| `templates/skills/` | `~/.agents/skills/` |

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
`*.bak` へ退避してから置換します（単一世代。再実行時は前回のバックアップが上書きされる）。

## スキル一覧

| スキル | 説明 |
| --- | --- |
| `km:review` | 包括的レビューオーケストレーター（intent/code/quality/doc-review を自動判定・並列実行） |
| `km:intent-review` | 会話履歴に基づく要件・意図の充足確認（コンテキストがない場合はスキップ） |
| `km:code-review` | 設計妥当性・バグ検出・コード品質など開発観点のコードレビュー |
| `km:quality-review` | ISO/IEC 25010 の9品質特性を軸とした品質レビュー |
| `km:doc-review` | ドキュメントの構造整合性・横断整合性・一次情報検証レビュー |
| `km:commit` | Conventional Commits 形式で git commit |

## ライセンス

MIT License。詳細は `LICENSE` を参照。
