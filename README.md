# agent-config

Claude Code / Codex CLI の共通設定テンプレートを管理するリポジトリ。

## 概要

- 正本は `templates/` 配下
- `agent_config` Python パッケージで `~/.claude/`、`~/.codex/`、`~/.agents/skills/` に反映 (POSIX / Windows 両対応)
- POSIX 環境では `install.sh` / `clean.sh` などのシェルラッパーから呼び出せる
- リポジトリ内の `README.md` と `docs/` は説明用。runtime contract は `templates/` 側を正とする

## Source Of Truth

- `templates/AGENTS.md` - Codex CLI 向け共通方針
- `templates/CLAUDE.md` - Claude Code 向け共通方針
- `templates/rules/` - Claude Code 向け markdown rules
- `templates/skills/` - Claude / Codex 共用の skills
- `templates/config.toml` - Codex CLI 用設定テンプレート
- `templates/keybindings.json` - Claude Code 用キーバインド
- `templates/statusline.sh` - Claude Code 用 status line
- `templates/settings.json` - Claude Code 推奨 settings.json ベースライン (既存ファイルへは shallow merge)

`docs/` は参考資料として残す。履歴メモや検討計画は git で追跡し、作業中の計画メモが必要な場合は repo 直下の `.plan/` に置く。

## ディレクトリ構造

- `templates/` - 配布対象テンプレート
- `agent_config/` - インストーラ / クリーナ / 検証の Python パッケージ
- `docs/` - 保守対象の参考ドキュメント
- `scripts/` - 補助スクリプト・後方互換ラッパー
- `tests/agent_config/` - `agent_config` の unittest
- `tests/skills/` - skill 回帰テスト資産
- `.github/workflows/` - GitHub Actions CI 設定
- `.claude/` - このリポジトリ自身の Claude Code 設定

## セットアップ

正規のエントリポイントは Python モジュール呼び出し。POSIX には bash ラッパーも同梱する。

```bash
# POSIX (Ubuntu / macOS / WSL)
bash install.sh
# または cross-platform
python3 -m agent_config.install
```

```powershell
# Windows
python -m agent_config.install
```

要件: Python 3.12+ (stdlib のみで動作。外部依存なし)。

このコマンドは以下を反映する。

- `~/.claude/CLAUDE.md`
- `~/.claude/rules/`
- `~/.claude/skills/`
- `~/.claude/keybindings.json`
- `~/.claude/statusline.sh`
- `~/.claude/settings.json` (推奨ベースラインを shallow merge。詳細は後述)
- `~/.codex/AGENTS.md`
- `~/.codex/config.toml`
- `~/.agents/skills/`

`settings.json` 以外の既存ファイルは上書き前に `*.bak` へ退避される。バックアップは単一世代。

### `settings.json` の取り扱い

`templates/settings.json` は **完全な上書きではなく shallow merge** で反映する (`agent_config.merge_settings`)。

- 初回インストール時: テンプレート全体を `~/.claude/settings.json` として作成する
- 2 回目以降: 既存ファイルに不足しているトップレベルキーだけテンプレートから補い、ユーザが既に設定している値は保持する
- マージ後の内容が既存と一致する場合は何もしない (`ok: ...` 出力)。差分が出た場合のみ既存ファイルを `*.bak` へ退避する

つまり `theme` のような個人設定はユーザ側で書き加えれば次回 install で消えない。逆に推奨ベースライン側の値を上書きしたい場合は、`~/.claude/settings.json` でそのキーを明示的に再定義すれば優先される。

`templates/settings.json` が現時点で配布する推奨キー:

| キー | 値 | 目的 |
| --- | --- | --- |
| `statusLine` | `~/.claude/statusline.sh` を実行する command 設定 | リポジトリ同梱の statusline を有効化する |
| `attribution.commit` / `attribution.pr` | 空文字 | コミットおよび PR 説明から Claude の署名を抑止する |
| `fileCheckpointingEnabled` | `true` | 編集前ファイルをスナップショットし `/rewind` で巻き戻せるようにする |
| `tui` | `"fullscreen"` | ちらつきの無い alt-screen レンダラ + 仮想化スクロールバックを有効化する |
| `showTurnDuration` | `true` | アシスタントターンごとの所要時間を表示する |
| `showMessageTimestamps` | `true` | 各メッセージにタイムスタンプを付与する |
| `feedbackSurveyRate` | `0` | セッション品質アンケートを抑止する |

## 検証

インストール結果の確認 (POSIX / Windows どちらでも):

```bash
bash scripts/verify-install.sh
# または
python3 -m agent_config.verify_install
```

skill 回帰資産の静的検証 (`pyyaml` が必要):

```bash
python3 -c "import yaml"
bash scripts/verify-skill-tests.sh
```

run sheet の生成・集計:

```bash
python3 scripts/run-skill-tests.py list
RUN_FILE=$(python3 scripts/run-skill-tests.py scaffold --label smoke --client Codex --model gpt-5.4)
python3 scripts/run-skill-tests.py summary --run-file "$RUN_FILE"
```

`validate-run` は run sheet 記入後に使う。

`agent_config` パッケージと `scripts/` 配下ユーティリティの unittest:

```bash
python3 -m unittest discover -v
```

GitHub Actions (`.github/workflows/tests.yml`) は `ubuntu-latest` と `windows-latest` の Python 3.12 / 3.13 マトリクスで上記をすべて実行する。

## クリーンアップ

```bash
bash clean.sh
# または
python3 -m agent_config.clean
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
  - Claude Code の status line、keybindings、Output Styles、Hooks の導入参考

Hooks、Output Styles、permissions のセキュリティハードニングなどの詳細は `docs/claude-code-terminal-customization.md` を参照。

## 反映先マッピング

| Repository Source | Destination |
| --- | --- |
| `templates/CLAUDE.md` | `~/.claude/CLAUDE.md` |
| `templates/AGENTS.md` | `~/.codex/AGENTS.md` |
| `templates/rules/` | `~/.claude/rules/` |
| `templates/skills/` | `~/.claude/skills/` |
| `templates/keybindings.json` | `~/.claude/keybindings.json` |
| `templates/statusline.sh` | `~/.claude/statusline.sh` |
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
  - Keybindings: `https://code.claude.com/docs/en/keybindings`
  - Output styles: `https://code.claude.com/docs/en/output-styles`
- OpenAI Codex CLI
  - CLI Overview: `https://developers.openai.com/codex/cli`
  - Config Basics: `https://developers.openai.com/codex/config-basic`
  - Config Reference: `https://developers.openai.com/codex/config-reference`
  - Rules: `https://developers.openai.com/codex/rules`
  - AGENTS.md: `https://developers.openai.com/codex/guides/agents-md`
  - Skills: `https://developers.openai.com/codex/skills`

## Codex 設計メモ

- `web_search = "cached"` を明示し、通常調査はキャッシュ検索、最新確認は `research` profile を使い分ける前提にしている
- `plan_mode_reasoning_effort = "high"` を明示し、Plan mode では通常ターンより深く考えさせる
- `check_for_update_on_startup = true` を明示し、更新確認をローカル設定で無効化しない前提にしている
- stable な機能のうち platform 差分が小さいものだけを `[features]` で明示し、将来の既定値変更で挙動がぶれにくいようにしている
- TUI は `alternate_screen = "never"` を使い、端末 scrollback を保持する
- default は `workspace-write + never` を前提にし、承認待ちを止めつつファイル操作は workspace sandbox に保つ
- 承認付きの旧来運用に戻したい場合は `interactive` profile、sandbox も外した完全信頼運用にしたい場合は `full_trust` profile を使う
- `project_doc_fallback_filenames = ["CLAUDE.md"]` を設定し、既存リポジトリとの互換を保っている
- 外部エディタ起動はシェルの `VISUAL` / `EDITOR` に委ねている

## スキル一覧

| スキル | 説明 |
| --- | --- |
| `km:review` | 未コミット変更を対象にレビュー強度を指定できる統合レビュー |
| `km:intent-review` | 会話履歴に基づいて要件・意図の充足を確認するレビュー |
| `km:code-review` | 設計妥当性・バグ検出・コード品質を確認するレビュー |
| `km:quality-review` | ISO/IEC 25010 を軸に品質特性を確認するレビュー |
| `km:doc-review` | ドキュメントの整合性と正確性を確認するレビュー |
| `km:third-party-oss-security-review` | npm / pip / VS Code extension / GitHub repo の採用前セキュリティレビュー |
| `km:commit` | Conventional Commits 形式で git commit |
| `km:github-workflow` | issue 連携を含む GitHub delivery ワークフロー |
| `km:plan` | 実装前の計画を作成し、`.plan/` への詳細出力、計画レビュー、GitHub issue 化までを行う |

## ライセンス

MIT License。詳細は `LICENSE` を参照。
