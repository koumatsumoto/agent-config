# agent-config

Claude Code / Codex CLI の共通設定テンプレートを管理するリポジトリ。

## 概要

- 正本は `templates/` 配下
- `scripts/cli.py` で `~/.claude/`、`~/.codex/`、`~/.agents/skills/` に反映 (Linux / macOS / Windows 対応)
- Linux / macOS / Git Bash では `install.sh` / `clean.sh` などのシェルラッパーから呼び出せる
- リポジトリ内の `README.md` と `docs/` は説明用。runtime contract は `templates/` 側を正とする

## Source Of Truth

- `templates/AGENTS.md` - Codex CLI 向け共通方針
- `templates/CLAUDE.md` - Claude Code 向け共通方針
- `templates/rules/` - Claude Code 向け markdown rules
- `templates/skills/` - Claude / Codex 共用の skills
- `templates/output-styles/` - Claude Code 向け custom output styles (モデル切替時の行動規範。`fable-like` 同梱)
- `templates/config.toml` - Codex CLI 用設定テンプレート
- `templates/codex/*.config.toml` - Codex CLI 用 profile テンプレート (`~/.codex/<profile>.config.toml`)
- `templates/codex-rules/` - Codex CLI 用 exec policy rules
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

正規のエントリポイントは `scripts/cli.py` のサブコマンド呼び出し。Python コマンド名の差は bash ラッパーの resolver に、filesystem / process の差は Python CLI の POSIX / native Windows 分岐に閉じ込め、インストール処理本体は 3 OS で共有する。Linux / macOS / Git Bash には bash ラッパーも同梱する。

Linux / macOS:

```bash
./install.sh
# または同等
python3 scripts/cli.py install
```

Windows (PowerShell / cmd):

```powershell
python scripts/cli.py install
```

要件: Python 3.12+ (stdlib のみで動作。外部依存なし)。bash ラッパーは `python3`、`python` の順に PATH を探索し、要件を満たす interpreter を使う。

> **OS ごとの Python**: Linux / macOS の例は `python3`、Windows の例は `python` と表記する。macOS 12.3 以降は従来の `python` (Python 2.7) が削除されており、素の macOS に Python 3.12+ があるとは限らない。`python3 --version` が要件を満たさない場合は Python 3.12+ を別途インストールする。installer 自体は macOS 固有の system Python に依存しない。

サポート境界は次のとおり。

| OS | 推奨入口 | platform 固有処理 |
| --- | --- | --- |
| Linux | `./install.sh` | POSIX permission と `python3` / `python` 探索 |
| macOS | `./install.sh` | Linux と同じ POSIX 処理。標準 bash で smoke test |
| Windows | `python scripts/cli.py install` | NTFS では POSIX mode を扱わず、status line は interpreter の絶対パスで起動 |

Windows の Git Bash では `./install.sh` もサポートし、`python3` が無い環境では同じ resolver が `python` を選ぶ。WSL は Linux として扱う。

このコマンドは以下を反映する。

- `~/.claude/CLAUDE.md` (詳細は後述)
- `~/.claude/rules/`
- `~/.claude/skills/`
- `~/.claude/output-styles/`
- `~/.claude/statusline.py`
- `~/.claude/subagent-statusline.py`
- `~/.claude/settings.json` (推奨ベースラインを shallow merge。詳細は後述)
- `~/.codex/AGENTS.md` (詳細は後述)
- `~/.codex/config.toml`
- `~/.codex/*.config.toml` (Codex profile: `readonly` / `full`)
- `~/.codex/rules/`
- `~/.agents/skills/`

`settings.json` 以外の既存ファイルは上書き前に `*.bak` へ退避される。バックアップは単一世代。

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

> **status line の `command` は OS 別に書き換わる**: テンプレートの `~/.claude/statusline.py` は POSIX シェル（Linux / macOS / Git Bash / WSL2）向け。ネイティブ Windows（`cmd.exe`）は `~` 展開も `.py` 直接実行もできないため、Python CLI がインストール時の Python を明示した `"C:/.../python.exe" "C:/Users/.../.claude/statusline.py"` 形式へ書き換える。POSIX では `~` パスのまま（shebang + 実行ビットで起動）。

### `CLAUDE.md` / `AGENTS.md` の取り扱い

`templates/CLAUDE.md`（Claude 向け）と `templates/AGENTS.md`（Codex 向け）は全プロジェクト共通の AI Agent 動作指針で、テンプレートを source of truth として毎回上書きする。repo 側の更新がそのまま各マシンへ伝播する。指針を変えたい場合は `templates/` 側を編集して再 install する。

マシン固有・個人ローカルなルールはこれらのファイルに書かない（次の install で失われる）。プロジェクト単位のローカル上書きは各リポジトリ直下の `CLAUDE.local.md`（git 管理外）に置く。ユーザレベルの `~/.claude/CLAUDE.local.md` は自動読み込みされない。

### Output Styles の取り扱い

`templates/output-styles/` は Claude Code の custom output style を `~/.claude/output-styles/` へ配布する。同梱の `fable-like` は、モデルを Opus / Sonnet に切り替えたセッションでも Fable 5 相当の行動様式（結論先行の報告・即行動・検証の実証・スコープ規律）を system prompt 末尾に注入する（`keep-coding-instructions: true` により組み込みのソフトウェアエンジニアリング指示は保持する）。

- **有効化**: `/config` → Output style で `fable-like` を選ぶ（選択は local レベル = プロジェクトの `.claude/settings.local.json` に保存）か、`.claude/settings.local.json` に `"outputStyle": "fable-like"` を直接書く。反映は `/clear` または新セッション（style は session 開始時にのみ読み込まれる）
- **運用注意**: user レベル `~/.claude/settings.json` の `outputStyle` はテンプレート宣言キー（既定 `Explanatory`）で、install 再実行のたびに repo の値へ戻る。そのため fable-like は user レベルでなく**プロジェクトレベル**（`.claude/settings.local.json` 等）で有効化する
- **無効化 (Fable に戻す)**: `/config` で outputStyle を元に戻すか、`.claude/settings.local.json` の `outputStyle` を削除する。反映は同じく `/clear` または新セッション

## 検証

インストール結果の確認:

```bash
# Linux / macOS
bash scripts/verify-install.sh
python3 scripts/cli.py verify
```

```powershell
# Windows
python scripts/cli.py verify
```

`scripts/cli.py` の unittest (Linux / macOS / Windows で実行可能):

```bash
# Linux / macOS
python3 -m unittest discover -s scripts/tests -t scripts -v
```

```powershell
# Windows
python -m unittest discover -s scripts/tests -t scripts -v
```

GitHub Actions (`.github/workflows/tests.yml`) は `ubuntu-latest` / `macos-latest` / `windows-latest` の Python 3.12 / 3.13 マトリクスで unittest と bash wrapper の smoke test を実行する。

## クリーンアップ

```bash
# Linux / macOS
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
| `templates/CLAUDE.md` | `~/.claude/CLAUDE.md` |
| `templates/AGENTS.md` | `~/.codex/AGENTS.md` |
| `templates/rules/` | `~/.claude/rules/` |
| `templates/skills/` | `~/.claude/skills/` |
| `templates/output-styles/` | `~/.claude/output-styles/` |
| `templates/statusline.py` | `~/.claude/statusline.py` |
| `templates/subagent-statusline.py` | `~/.claude/subagent-statusline.py` |
| `templates/settings.json` | `~/.claude/settings.json` (shallow merge) |
| `templates/config.toml` | `~/.codex/config.toml` |
| `templates/codex/*.config.toml` | `~/.codex/*.config.toml` |
| `templates/codex-rules/` | `~/.codex/rules/` |
| `templates/skills/` | `~/.agents/skills/` |

注記: `templates/rules/` は Claude Code 向け markdown rules を指す。Codex CLI の exec policy rules は `templates/codex-rules/` から `~/.codex/rules/` へ配布する。

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
  - Advanced Config: `https://developers.openai.com/codex/config`
  - Rules: `https://developers.openai.com/codex/rules`
  - Hooks: `https://developers.openai.com/codex/hooks`
  - AGENTS.md: `https://developers.openai.com/codex/guides/agents-md`
  - Skills: `https://developers.openai.com/codex/skills`

## Codex 設計メモ

- default model は `gpt-5.6-sol`、reasoning effort は `high`、personality は `pragmatic`、verbosity は `low` にして、複雑な実装を簡潔に報告する
- 管理する reasoning effort は default / Plan mode の `high` と full の `xhigh` に絞り、`low` / `ultra` は使わない
- `web_search = "cached"` を明示し、通常調査はキャッシュ検索を使う。最新確認が必要な場合は live web を明示して使う
- `plan_mode_reasoning_effort = "high"` を明示し、Plan mode でも reasoning effort を `high` に保つ
- `check_for_update_on_startup = true` を明示し、更新確認をローカル設定で無効化しない前提にしている
- stable な機能のうち platform 差分が小さいものだけを `[features]` で明示し、将来の既定値変更で挙動がぶれにくいようにしている
- TUI は `alternate_screen = "never"` を使い、端末 scrollback を保持する
- default は `workspace-write + on-request + approvals_reviewer = "auto_review"` を前提にする。通常の workspace 内読み取り・編集・安全なコマンドは自律的に進め、sandbox 外実行・shell network・外部書き込みは承認経路へ送る
- `sandbox_workspace_write.network_access = false` を明示し、`gh` / package manager / curl などの shell network は default では sandbox 内で直接動かさない。必要な場合は目的と影響を説明して承認経路に送る
- Codex profile は `~/.codex/<profile>.config.toml` として配布する。管理対象は `readonly` と `full` だけに絞る
- `approval_policy = "never"` は `full` のみに置く。通常の自律運用は承認待ちを消すのではなく、workspace sandbox と auto review で安全な範囲を自律化する
- `~/.codex/rules/` は sandbox 外へ出る承認要求に対して、force push、hard reset、外部 recursive delete、GitHub 書き込みなどを prompt へ寄せる。workspace sandbox 内で実行できる Bash を強制遮断するものではないため、危険な in-sandbox コマンドの抑止は `AGENTS.md` の行動規範で扱う
- 読み取り専用で探索したい場合は `readonly` profile、sandbox も外した完全信頼運用にしたい場合は `full` profile を使う
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
