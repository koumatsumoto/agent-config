# agent-config

Claude Code と OpenAI Codex CLI の共通設定テンプレートを管理するリポジトリです。

## 対応CLI

- Claude Code
- OpenAI Codex CLI

## 運用ポリシー

- 編集元は `templates/` 配下。反映先の `~/.claude/` と `~/.codex/` は直接編集しない
- Codex 側は `AGENTS.md` を正とし、互換のため `CLAUDE.md` も fallback 対象にする
- Claude 側は `CLAUDE.md` を正とし、`templates/CLAUDE.md` は Claude Code 専用方針として保つ
- ターミナル運用を前提に、共通方針は「最小限の確認で前進」「差分と検証を重視」「client 標準機能を優先」で揃える
- インストールはコピー方式で行い、既存ファイルは `*.bak` に退避する

## ディレクトリ構造

- `templates/` - デプロイ対象のテンプレート群
  - `CLAUDE.md` - Claude Code 専用の共通エージェント方針
  - `AGENTS.md` - Codex CLI 向けの共通エージェント方針
  - `rules/` - ルール定義
  - `skills/` - スキル定義（スラッシュコマンド + 参照スキル。Claude / Codex で共用）
  - `keybindings.json` - キーバインド設定（Shift+Enter で改行）
  - `statusline.sh` - ステータスライン表示スクリプト（モデル・コンテキスト・コスト・5hレート制限・ブランチ）
  - `config.toml` - Codex CLI 用の terminal-first 設定テンプレート
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
  - `AGENTS.md`（`templates/AGENTS.md` から反映）
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

### 外部エディタを VS Code にする

Codex CLI / Claude Code の prompt editor を VS Code で開きたい場合は、シェル側で `VISUAL` または `EDITOR` を設定する。`code` コマンドが使える前提で、`--wait` を付ける。

```bash
export VISUAL="code --wait"
export EDITOR="code --wait"
```

永続化する場合は、利用中のシェル設定ファイルに追記する:

- `bash`: `~/.bashrc`
- `zsh`: `~/.zshrc`

反映後はターミナルを開き直すか、設定ファイルを `source` してから CLI を起動する。

## Markdown 軽量化

AI に渡す前の Markdown から余分な空白やテーブルのパディングを減らしたい場合は `scripts/pack-md.sh` を使います。

```bash
./scripts/pack-md.sh README.md > README.llm.md
./scripts/pack-md.sh -i README.md
```

## Codex 設定方針

- デフォルトは `workspace-write + on-request`
- `web_search = "cached"` を明示し、通常調査はキャッシュ検索、最新確認は `live_web` profile へ分離
- TUI は `alternate_screen = "never"` を使い、端末 scrollback を保持する
- profile を分けて `deep`、`readonly`、`live_web`、`fast` を切り替える
- `project_doc_fallback_filenames = ["CLAUDE.md"]` を設定し、既存リポジトリとの互換を保つ
- 外部エディタ起動はシェルの `VISUAL` / `EDITOR` に委ねる

## 反映先マッピング

| Repository Source | Destination |
| --- | --- |
| `templates/CLAUDE.md` | `~/.claude/CLAUDE.md` |
| `templates/AGENTS.md` | `~/.codex/AGENTS.md` |
| `templates/rules/` | `~/.claude/rules/` |
| `templates/skills/` | `~/.claude/skills/` |
| `templates/keybindings.json` | `~/.claude/keybindings.json` |
| `templates/statusline.sh` | `~/.claude/statusline.sh` |
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
