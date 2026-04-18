# agent-config

Claude Code と OpenAI Codex CLI の共通設定テンプレートを管理するリポジトリです。

## 対応CLI

- Claude Code
- OpenAI Codex CLI

## 運用ポリシー

- 編集元は `templates/` 配下。反映先の `~/.claude/` と `~/.codex/` は直接編集しない
- Codex 側は `AGENTS.md` を正とし、互換のため `CLAUDE.md` も fallback 対象にする
- Claude 側は `CLAUDE.md` を正とし、`templates/CLAUDE.md` は Claude Code 専用方針として保つ
- Clarify 方針は client ごとに分ける。Codex 側は前進優先（不明点は前提を明示して前進）、Claude 側は確認優先（影響が大きい不明点は先に質問）
- ターミナル運用を前提に、共通方針は「差分と検証を重視」「client 標準機能を優先」で揃える
- インストールはテンプレート管理対象のみを同期し、上書き対象ファイルは `*.bak` に退避する

## ディレクトリ構造

- `templates/` - デプロイ対象のテンプレート群
  - `CLAUDE.md` - Claude Code 専用の共通エージェント方針
  - `AGENTS.md` - Codex CLI 向けの共通エージェント方針
  - `rules/` - ルール定義
  - `skills/` - スキル定義（スラッシュコマンド + 参照スキル。Claude / Codex で共用）
  - `keybindings.json` - キーバインド設定（Shift+Enter で改行）
  - `statusline.sh` - ステータスライン表示スクリプト（モデル・コンテキスト・コスト・5h/7dレート制限・ブランチ。jq 推奨、bash fallback 対応）
  - `config.toml` - Codex CLI 用の terminal-first 設定テンプレート
- `scripts/` - ユーティリティスクリプト（pack-md.sh 等）
- `tests/` - 回帰テスト資産
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

`install.sh` は引数なしで、Claude/Codex の両方を一括反映し、最後に `scripts/verify-install.sh` で配置結果を検証します。

`templates/rules/`、`templates/skills/` の同期はテンプレート管理対象パス単位で行います。`~/.claude/rules/`、`~/.claude/skills/`、`~/.agents/skills/` にある追加ローカルファイルは保持されます。

## ターミナルカスタマイズ

`install.sh` は以下のターミナルカスタマイズ設定も反映します:

- **ステータスライン** (`statusline.sh`): モデル名・コンテキスト使用率（色付きプログレスバー）・セッションコスト・5h/7dレート制限・Git ブランチを常時表示。jq 推奨（bash fallback あり）
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

Hooks、Output Styles、permissions のセキュリティハードニング等の詳細は `docs/claude-code-terminal-customization.md` を参照。

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

## Codex 設計メモ

- デフォルトの sandbox / approval は `workspace-write + on-request` としている
- `web_search = "cached"` を明示し、通常調査はキャッシュ検索、最新確認は `research` profile を使い分ける前提にしている
- `plan_mode_reasoning_effort = "high"` を明示し、Plan mode では通常ターンより深く考えさせる
- `check_for_update_on_startup = true` を明示し、更新確認をローカル設定で無効化しない前提にしている
- stable な機能のうち platform 差分が小さいものだけを `[features]` で明示し、`fast_mode = false` を含めて将来の既定値変更で挙動がぶれにくいようにしている
- TUI は `alternate_screen = "never"` を使い、端末 scrollback を保持する
- profile は `deep`、`research`、`review`、`readonly`、`live_web` に絞り、fast tier 前提の profile は配布しない
- status line は組み込み項目のみを使い、モデル・Git・コンテキスト・5h 制限・トークン totals を常時確認できるようにしている
- 5h 制限のリセット時刻は内部イベントでは取得できるが、`codex-cli 0.118.0` の `tui.status_line` には専用表示項目がないため常時表示は未対応
- 起動時の初期モードを Plan mode に固定する安定した公開設定キーは、2026-04-18 時点の OpenAI Codex docs と `codex-cli 0.121.0` では確認できなかったため未設定としている
- `project_doc_fallback_filenames = ["CLAUDE.md"]` を設定し、既存リポジトリとの互換を保っている
- 外部エディタ起動はシェルの `VISUAL` / `EDITOR` に委ねている
- profile の運用方針そのものは `templates/AGENTS.md` を参照

## 検証

インストール結果を単独で確認したい場合は以下を使います。

```bash
bash scripts/verify-install.sh
```

このスクリプトは、テンプレート管理対象のファイル内容とファイルモードが期待どおりかを確認します。追加ローカルファイルは drift 扱いしません。

`bash install.sh` は最後にこの検証を実行し、missing / drift / mode drift が 1 件でもあれば非ゼロ終了します。テンプレート管理対象をローカル変更した場合は `templates/` 側を更新してから再インストールしてください。

既知の制限として、テンプレートから削除された古い skill / rule はインストール先から自動削除されません。不要なファイルは手動で整理してください。

skill 用の回帰テスト資産が壊れていないかは以下で確認できます。

```bash
python3 -c "import yaml"
bash scripts/verify-skill-tests.sh
```

ケース一覧確認や手動 run sheet 生成には以下を使います。

```bash
python3 -c "import yaml"
python3 scripts/run-skill-tests.py list
RUN_FILE=$(python3 scripts/run-skill-tests.py scaffold --label smoke --client Codex --model gpt-5.4)
python3 scripts/run-skill-tests.py summary --run-file "$RUN_FILE"
```

`validate-run` は run sheet 記入後に使います。

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

注記: `templates/rules/` は現時点では Claude Code 向け markdown rules を指す。OpenAI Codex CLI の `.rules` は別機能であり、このリポジトリではまだ配布対象にしていない。

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

`install.sh` は上書きするテンプレート管理対象ファイルごとに `*.bak` へ退避してから置換します。バックアップは単一世代で、再実行時は前回のバックアップが上書きされます。

従来のような `skills/` ディレクトリ全体のスナップショット退避ではなく、バックアップ粒度はファイル単位です。

## クリーンアップ

設定を退避しながら削除したい場合は以下を使います。

```bash
bash clean.sh
```

このスクリプトは以下を `*.bak` に退避してから削除します。

- `~/.claude/CLAUDE.md`
- `~/.claude/rules/`
- `~/.claude/skills/`
- `~/.claude/keybindings.json`
- `~/.claude/statusline.sh`
- `~/.codex/AGENTS.md`
- `~/.codex/config.toml`
- `~/.agents/skills/`

## スキル一覧

| スキル | 説明 |
| --- | --- |
| `km:review` | 未コミット変更を対象にレビュー強度を指定できる統合レビュー |
| `km:intent-review` | 会話履歴に基づいて要件・意図の充足を確認するレビュー |
| `km:code-review` | 設計妥当性・バグ検出・コード品質を確認するレビュー |
| `km:quality-review` | ISO/IEC 25010 を軸に品質特性を確認するレビュー |
| `km:doc-review` | ドキュメントの整合性と正確性を確認するレビュー |
| `km:npm-package-security-review` | 単一 npm package の採用前セキュリティレビュー |
| `km:commit` | Conventional Commits 形式で git commit |
| `km:github-workflow` | issue 連携を含む GitHub delivery ワークフロー |

## ライセンス

MIT License。詳細は `LICENSE` を参照。
