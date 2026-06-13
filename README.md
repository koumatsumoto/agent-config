# agent-config

Claude Code / Codex CLI の共通設定テンプレートを管理するリポジトリ。

## 概要

- 正本は `templates/` 配下
- `scripts/cli.py` で `~/.claude/`、`~/.codex/`、`~/.agents/skills/` に反映 (POSIX / Windows 両対応)
- POSIX 環境では `install.sh` / `clean.sh` などのシェルラッパーから呼び出せる
- リポジトリ内の `README.md` と `docs/` は説明用。runtime contract は `templates/` 側を正とする

## Source Of Truth

- `templates/AGENTS.md` - Codex CLI 向け共通方針
- `templates/CLAUDE.md` - Claude Code 向け共通方針
- `templates/rules/` - Claude Code 向け markdown rules
- `templates/skills/` - Claude / Codex 共用の skills
- `templates/config.toml` - Codex CLI 用設定テンプレート
- `templates/statusline.py` - Claude Code 用 status line (リッチ 2 行レイアウト)
- `templates/subagent-statusline.py` - Claude Code サブエージェント行の status line
- `templates/settings.json` - Claude Code 推奨 settings.json ベースライン (既存ファイルへは shallow merge)

`docs/` は参考資料として残す。履歴メモや検討計画は git で追跡し、作業中の計画メモが必要な場合は repo 直下の `.plan/` に置く。

## ディレクトリ構造

- `templates/` - 配布対象テンプレート
- `scripts/` - Python CLI 本体と補助スクリプト
- `scripts/cli.py` - インストーラ / クリーナ / 検証 / settings マージを束ねる Python CLI
- `scripts/tests/` - `scripts/cli.py` の unittest
- `docs/` - 保守対象の参考ドキュメント
- `.github/workflows/` - GitHub Actions CI 設定
- `.claude/` - このリポジトリ自身の Claude Code 設定

## セットアップ

正規のエントリポイントは `scripts/cli.py` のサブコマンド呼び出し。POSIX には bash ラッパーも同梱する。

POSIX (Ubuntu / macOS / WSL):

```bash
bash install.sh
# または同等
python3 scripts/cli.py install
```

Windows (PowerShell / cmd):

```powershell
python scripts/cli.py install
```

要件: Python 3.12+ (stdlib のみで動作。外部依存なし)。

> **コマンド表記**: 本 README では POSIX 向けに `python3` を使う。Windows には `python3` コマンドが存在しない (Microsoft Store / installer はどちらも `python` のみ提供) ため、Windows ユーザは以降の例の `python3` をすべて `python` に読み替えること。

このコマンドは以下を反映する。

- `~/.claude/CLAUDE.md` (既存があれば上書きしない。初回のみ配置。詳細は後述)
- `~/.claude/rules/`
- `~/.claude/skills/`
- `~/.claude/statusline.py`
- `~/.claude/subagent-statusline.py`
- `~/.claude/settings.json` (推奨ベースラインを shallow merge。詳細は後述)
- `~/.codex/AGENTS.md` (既存があれば上書きしない。初回のみ配置。詳細は後述)
- `~/.codex/config.toml`
- `~/.agents/skills/`

`settings.json` / `CLAUDE.md` / `AGENTS.md` 以外の既存ファイルは上書き前に `*.bak` へ退避される。バックアップは単一世代。

`rules` / `skills` ツリーは配備先をテンプレートに一致させる。**管理ディレクトリ内のテンプレートに無いファイル / サブディレクトリは prune する** (`pruned: ...` 出力、`*.bak` へ退避)。ただし **ツリー直下のトップレベルエントリ (テンプレートに無いファイル・ディレクトリ — ユーザが置いた独自 skill 等) は保護され、prune されない**。

### `settings.json` の取り扱い

`templates/settings.json` は **完全な上書きではなく shallow merge** で反映する (`scripts/cli.py` の merge ロジック。単体では `python3 scripts/cli.py merge <template> <dest>` で実行できる)。

- 初回インストール時: テンプレート全体を `~/.claude/settings.json` として作成する
- 2 回目以降: テンプレートが宣言するトップレベルキーはテンプレート値で上書きし (repo を source of truth とする)、テンプレートが宣言しないキー (例: `theme` / `model` / `enabledPlugins` など UI・ランタイム管理値) はユーザ設定を保持する
- マージ後の内容が既存と一致する場合は何もしない (`ok: ...` 出力)。差分が出た場合のみ既存ファイルを `*.bak` へ退避する

つまり `theme` のような個人設定はユーザ側で書き加えれば次回 install で消えない。一方、テンプレートが宣言するキー (下表) はランタイムで一時変更しても次回 install で repo の値に戻る。恒久的に変えたい場合は `templates/settings.json` 側を編集する。

`templates/settings.json` が現時点で配布する推奨キー:

| キー | 値 | 目的 |
| --- | --- | --- |
| `statusLine` | `~/.claude/statusline.py` を実行する command (`refreshInterval: 30`)。OS 別に書き換え (下記) | リポジトリ同梱のリッチ status line を有効化する |
| `subagentStatusLine` | `~/.claude/subagent-statusline.py` を実行する command。OS 別に書き換え (下記) | サブエージェント行を自前描画する |
| `permissions.deny` | `.env` / 秘密鍵 / `secrets/` 等の読み取り禁止と `Bash(npx *)` | 機密ファイルへのアクセスを既定で遮断する |
| `permissions.defaultMode` | `"plan"` | セッションを既定で plan mode で開始する |
| `language` | `"日本語"` | 応答言語を日本語に固定する |
| `effortLevel` | `"xhigh"` | reasoning effort を xhigh で永続化する |
| `attribution.commit` / `attribution.pr` | 空文字 | コミットおよび PR 説明から Claude の署名を抑止する |
| `fileCheckpointingEnabled` | `true` | 編集前ファイルをスナップショットし `/rewind` で巻き戻せるようにする |
| `tui` | `"fullscreen"` | ちらつきの無い alt-screen レンダラ + 仮想化スクロールバックを有効化する |
| `showTurnDuration` | `true` | アシスタントターンごとの所要時間を表示する |
| `showMessageTimestamps` | `true` | 各メッセージにタイムスタンプを付与する |
| `feedbackSurveyRate` | `0` | セッション品質アンケートを抑止する |

> **status line の `command` は OS 別に書き換わる**: テンプレートの `~/.claude/statusline.py` は POSIX シェル（Linux / macOS / Git Bash / WSL2）向け。ネイティブ Windows（`cmd.exe`）は `~` 展開も `.py` 直接実行もできないため、`install.sh` がインストール時の Python を明示した `"C:/.../python.exe" "C:/Users/.../.claude/statusline.py"` 形式へ書き換える。POSIX では `~` パスのまま（shebang + 実行ビットで起動）。

### `CLAUDE.md` / `AGENTS.md` の取り扱い

`templates/CLAUDE.md`（Claude 向け）と `templates/AGENTS.md`（Codex 向け）は全プロジェクト共通の AI Agent 動作指針で、**seed-only** で反映する。`~/.claude/CLAUDE.md` / `~/.codex/AGENTS.md` が無い場合のみ初期配置し、既に存在する場合は上書きせずローカル編集を保護する（install は `skip:` を出力）。`settings.json` と同様にユーザ管理ファイル扱いとし、`clean` でも削除せず、`verify` でもテンプレートとの差分（drift）を検査しない。グローバル指針を更新したい場合は配置先を直接編集するか、`templates/` 側を編集したうえで既存ファイルを退避してから再 install する。

## 検証

インストール結果の確認:

```bash
# POSIX
bash scripts/verify-install.sh
python3 scripts/cli.py verify
```

```powershell
# Windows
python scripts/cli.py verify
```

`scripts/cli.py` の unittest (POSIX / Windows どちらでも実行可能):

```bash
# POSIX
python3 -m unittest discover -s scripts/tests -t scripts -v
```

```powershell
# Windows
python -m unittest discover -s scripts/tests -t scripts -v
```

GitHub Actions (`.github/workflows/tests.yml`) は `ubuntu-latest` と `windows-latest` の Python 3.12 / 3.13 マトリクスで unittest を実行する。

## クリーンアップ

```bash
# POSIX
bash clean.sh
python3 scripts/cli.py clean
```

```powershell
# Windows
python scripts/cli.py clean
```

このコマンドは配布済みのテンプレート管理対象を `*.bak` に退避してから削除する。`~/.claude/settings.json` はユーザのカスタマイズが含まれ得るため対象から除外している。

## Maintained Docs

- `docs/claude-code-best-practices-202604.md`
  - Claude Code の `CLAUDE.md`、rules、skills、subagents、hooks、settings 周りの 2026-04 リファレンス
- `docs/python-best-practices-202604.md`
  - Python 3.14 / Pyright / Ruff を前提にした 2026-04 リファレンス
- `docs/typescript-best-practices-202604.md`
  - TypeScript 6.0+ / ESLint flat config / typescript-eslint typed linting を前提にした 2026-04 リファレンス
- `docs/claude-code-terminal-customization.md`
  - Claude Code の status line、Output Styles、Hooks の導入参考

Hooks、Output Styles、permissions のセキュリティハードニングなどの詳細は `docs/claude-code-terminal-customization.md` を参照。

## 反映先マッピング

| Repository Source | Destination |
| --- | --- |
| `templates/CLAUDE.md` | `~/.claude/CLAUDE.md` (seed-only: 既存は上書きしない) |
| `templates/AGENTS.md` | `~/.codex/AGENTS.md` (seed-only: 既存は上書きしない) |
| `templates/rules/` | `~/.claude/rules/` |
| `templates/skills/` | `~/.claude/skills/` |
| `templates/statusline.py` | `~/.claude/statusline.py` |
| `templates/subagent-statusline.py` | `~/.claude/subagent-statusline.py` |
| `templates/settings.json` | `~/.claude/settings.json` (shallow merge) |
| `templates/config.toml` | `~/.codex/config.toml` |
| `templates/skills/` | `~/.agents/skills/` |

注記: `templates/rules/` は Claude Code 向け markdown rules を指す。Codex CLI の `rules` 機能とは別物であり、このリポジトリではまだ配布対象にしていない。

## 公式仕様

- Claude Code
  - Best practices: `https://code.claude.com/docs/en/best-practices`
  - Memory (`CLAUDE.md`): `https://code.claude.com/docs/en/memory`
  - Skills: `https://code.claude.com/docs/en/skills`
  - Sub-agents: `https://code.claude.com/docs/en/sub-agents`
  - Hooks: `https://code.claude.com/docs/en/hooks`
  - Settings: `https://code.claude.com/docs/en/settings`
  - Status line: `https://code.claude.com/docs/en/statusline`
  - Output styles: `https://code.claude.com/docs/en/output-styles`
- OpenAI Codex CLI
  - CLI Overview: `https://developers.openai.com/codex/cli`
  - Config Basics: `https://developers.openai.com/codex/config-basic`
  - Config Reference: `https://developers.openai.com/codex/config-reference`
  - Rules: `https://developers.openai.com/codex/rules`
  - AGENTS.md: `https://developers.openai.com/codex/guides/agents-md`
  - Skills: `https://developers.openai.com/codex/skills`

## Codex 設計メモ

- default model は `gpt-5.5`、reasoning effort は `medium`、verbosity も `medium` にして、通常実装の品質と速度のバランスを取っている
- `web_search = "cached"` を明示し、通常調査はキャッシュ検索、最新確認は `research` profile を使い分ける前提にしている
- `plan_mode_reasoning_effort = "high"` を明示し、Plan mode では通常ターンより深く考えさせる
- `check_for_update_on_startup = true` を明示し、更新確認をローカル設定で無効化しない前提にしている
- stable な機能のうち platform 差分が小さいものだけを `[features]` で明示し、将来の既定値変更で挙動がぶれにくいようにしている
- TUI は `alternate_screen = "never"` を使い、端末 scrollback を保持する
- default は `workspace-write + on-request` を前提にし、通常のファイル操作は workspace sandbox に保ちながら、sandbox 外実行が必要な操作だけ確認する
- `sandbox_workspace_write.network_access = true` を明示し、gh / package manager / curl など通常の開発 CLI を default のまま動かす
- 承認待ちを完全に避けたい場合は `autonomous` profile、sandbox も外した完全信頼運用にしたい場合は `full_trust` profile を使う
- `project_doc_fallback_filenames = ["CLAUDE.md"]` を設定し、既存リポジトリとの互換を保っている
- 外部エディタ起動はシェルの `VISUAL` / `EDITOR` に委ねている

## スキル一覧

| スキル | 説明 |
| --- | --- |
| `km:review` | レビュー対象 (未コミット / コミット範囲 / PR / リポジトリ) とレベル (quick / standard / thorough) を指定できる 1 回完結の診断レビュー。Phase 2 (generalist code-review) → Phase 3 (3 専門家: architect / qa / security 並列) → Phase 4 (doc-review) の sequential gating で実行し、CRITICAL/HIGH 検出時はその Phase で停止して報告 |
| `km:third-party-oss-security-review` | npm / pip / VS Code extension / GitHub repo の採用前セキュリティレビュー |
| `km:commit` | Conventional Commits 形式で git commit |
| `km:github-workflow` | branch / commit / PR / issue 連携を含む GitHub delivery 運用ルール |
| `km:plan` | 実装前の計画を作成し、`.plan/` への詳細出力、計画レビュー、GitHub issue 化までを行う |

## ライセンス

MIT License。詳細は `LICENSE` を参照。
