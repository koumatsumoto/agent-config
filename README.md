# agent-config

Claude CodeとCodex CLIの共通設定テンプレートを管理する。

## 概要

- 正本は `templates/` 配下
- `scripts/cli.py` で `~/.claude/`、`~/.codex/`、`~/.agents/skills/` に反映 (Linux / macOS / Windows 対応)
- AI共通ガイドラインの正本は`templates/CLAUDE.md`だけである。各ツールが要求するファイル名（`~/.claude/CLAUDE.md`、`~/.codex/AGENTS.md`）へ同じ内容を配布する
- `--claude-dir <dir>` で `CLAUDE_CONFIG_DIR` 用の別プロファイルにも配布できる
- Linux / macOS / Git Bashでは `install.sh` / `clean.sh` などのシェルラッパーから呼び出せる
- `README.md`は説明資料であり、実行時契約の正本は`templates/`に置く

## 正本

- `templates/CLAUDE.md` - Claude Code、Codex CLIに共通するAI共通ガイドライン（唯一の正本）
- `templates/skills/` - Claude / Codex CLI 共用の skills
- `templates/config.toml` - Codex CLI 用設定テンプレート
- `templates/codex/*.config.toml` - Codex CLI用のプロファイルテンプレート（`~/.codex/<profile>.config.toml`）
- `templates/codex-rules/` - Codex CLI 用 exec policy rules
- `templates/statusline.py` - Claude Code 用 status line (リッチ 2 行レイアウト)
- `templates/subagent-statusline.py` - Claude Codeのsubagent status line
- `templates/settings.json` - Claude Code向けの推奨`settings.json`（既存ファイルへは浅くマージ）

履歴メモや検討計画はGitで追跡し、作業中だけ必要なメモはOSまたは実行環境の一時領域に置く。

## ディレクトリ構造

- `templates/` - 配布対象テンプレート
- `scripts/` - Python CLI 本体と補助スクリプト
- `scripts/cli.py` - インストーラ / クリーナ / 検証 / settings マージを束ねる Python CLI
- `scripts/tests/` - `scripts/cli.py` の unittest
- `evals/` - 挙動資産ごとの評価シナリオ集。配布せず、`km-skill-eval`の回帰評価で必要な項目だけ使う
- `.github/workflows/` - GitHub Actions CI 設定
- `.claude/` - このリポジトリ自身の Claude Code 設定

## セットアップ

正規の入口は`scripts/cli.py`である。Pythonコマンド名の違いはシェルラッパーが吸収し、OSごとの差はPython CLI内に閉じ込める。インストール処理本体はLinux、macOS、Windowsで共有し、Linux、macOS、Git Bashにはシェルラッパーも同梱する。

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

要件はPython 3.9以上で、外部パッケージには依存しない。シェルラッパーは`python3`、`python`の順に利用可能な実行環境を探す。特定のOSパッケージマネージャーには依存しない。

Python 3.9は、このリポジトリの互換性とCIの最低基準である。Appleの公式文書ではmacOS 26に付属するPythonの版を確認できないため、macOSの初期状態だけで要件を満たすとはみなさない。（確認日: 2026年8月9日）

> **OSごとのPython実行環境**: LinuxとmacOSの例は`python3`、Windowsの例は`python`と表記する。macOSでは`python`が存在しない場合があるため、`python3`を先に探す。インストーラー自体はmacOS固有のシステムPythonや特定の導入方法に依存しない。

サポート境界は次のとおり。

| OS | 推奨入口 | OS固有の処理 |
| --- | --- | --- |
| Linux | `./install.sh` | POSIX権限の設定とPython 3.9以降の実行環境の探索 |
| macOS | `./install.sh` | Linuxと同じPOSIX処理。標準bashで簡易動作確認 |
| Windows | `python scripts/cli.py install` | NTFSではPOSIXモードを扱わず、status lineはPython実行環境の絶対パスで起動 |

WindowsのGit Bashでは`./install.sh`もサポートし、`python3`がない環境では同じ検出処理で`python`を選ぶ。WSLはLinuxとして扱う。

このコマンドは、次のファイルとディレクトリを配置する。

- `~/.claude/CLAUDE.md` (詳細は後述)
- `~/.claude/skills/`
- `~/.claude/statusline.py`
- `~/.claude/subagent-statusline.py`
- `~/.claude/settings.json`（推奨設定を浅くマージ。詳細は後述）
- `~/.codex/AGENTS.md` (詳細は後述)
- `~/.codex/config.toml`
- `~/.codex/*.config.toml` (Codex プロファイル: `readonly` / `trusted`)
- `~/.codex/rules/`
- `~/.agents/skills/`

`settings.json`以外を置き換える前に、既存内容を`*.bak`へ退避する。バックアップは単一世代である。`settings.json`だけは利用者・runtime固有の値を保持しながらテンプレート管理値をマージする。

`skills/`はテンプレートに合わせ、管理下の不要項目を削除する（`pruned: ...`と出力し、`*.bak`へ退避）。ただし、ツリー直下に利用者が作成したファイルとディレクトリは保持する。

### 別の設定ディレクトリへインストールする (`--claude-dir`)

`CLAUDE_CONFIG_DIR` で `~/.claude` 以外の設定ディレクトリを使うプロファイル (サブアカウント用の起動コマンド等) にも、同じテンプレートを配布できる。

```bash
# Linux / macOS
./install.sh --claude-dir ~/.claude-sub
python3 scripts/cli.py install --claude-dir ~/.claude-sub
```

```powershell
# Windows
python scripts/cli.py install --claude-dir C:/Users/<user>/.claude-sub
```

`CLAUDE_CONFIG_DIR`は`~/.claude`の代替先を示す。このため、ファイルは指定ディレクトリの直下へ配置する。

| Repository Source | Destination (`--claude-dir <dir>`) |
| --- | --- |
| `templates/CLAUDE.md` | `<dir>/CLAUDE.md` |
| `templates/skills/` | `<dir>/skills/` |
| `templates/statusline.py` | `<dir>/statusline.py` |
| `templates/subagent-statusline.py` | `<dir>/subagent-statusline.py` |
| `templates/settings.json` | `<dir>/settings.json` (浅いマージ) |

配布内容は`~/.claude`向けの配布一覧から導出する。`~/.claude`に配るものが増減すれば、指定ディレクトリ側も同じだけ増減する。

- 対象はClaude Codeの設定ディレクトリのみ。Codex（`~/.codex`）と共用スキル（`~/.agents/skills`）は各ツールが自前のパスを参照するため配布しない
- `settings.json` の status line は指定ディレクトリのスクリプトを指すよう書き換える (ホーム配下なら `~/.claude-sub/statusline.py`、ホーム外なら絶対パス)
- 既存ファイルの `*.bak` 退避、不要項目の削除、POSIX permission (`0700` / `0600`) は既定インストールと同じ規律で動く
- `clean` / `verify` も同じオプションを受け取る
- ディレクトリが無ければ `0700` で作成する。ホームディレクトリ自身・ファイルシステムのルート・既存の非ディレクトリは拒否する
- `CLAUDE_CONFIG_DIR` 環境変数は参照しない。それを export したシェルからの `./install.sh` も `~/.claude` を対象にし、配布先の切り替えは常に明示操作にする

### `settings.json` の取り扱い

`templates/settings.json`は**完全に上書きせず、トップレベルだけを浅くマージ**して反映する（`scripts/cli.py`のマージ処理。単体では`python3 scripts/cli.py merge <template> <dest>`で実行できる）。

- 初回インストール時: テンプレート全体を `~/.claude/settings.json` として作成する
- 2回目以降: テンプレートが宣言するトップレベルキーはテンプレート値で上書きし、リポジトリを正本とする。テンプレートが宣言しないキー（例: `theme`、`model`、`enabledPlugins`などのUI・実行時管理値）はユーザー設定を保持する
- マージ後の内容が既存と一致する場合は何もしない (`ok: ...` 出力)。差分が出た場合のみ既存ファイルを `*.bak` へ退避する

つまり、`theme`のような個人設定はユーザー側で書き加えれば、次回のインストールでも消えない。一方、テンプレートが宣言するキー（下表）は実行時に一時変更しても、次回のインストールでリポジトリの値に戻る。恒久的に変える場合は`templates/settings.json`を編集する。

`templates/settings.json` が現時点で配布する推奨キー:

| キー | 値 | 目的 |
| --- | --- | --- |
| `statusLine` | `~/.claude/statusline.py` を実行する command (`refreshInterval: 30`)。OS 別に書き換え (下記) | リポジトリ同梱のリッチ status line を有効化する |
| `subagentStatusLine` | `~/.claude/subagent-statusline.py` を実行する command。OS 別に書き換え (下記) | subagent行を自前描画する |
| `permissions.deny` | `.env` / 秘密鍵 / `secrets/` 等の読み取り禁止 | 秘密情報を持つ可能性が高いファイルをglobal denyで保護する |
| `permissions.ask` | `Bash(npx *)` | Bash経路の`npx`はパッケージを取得・実行し得るため、実行前に確認する |
| `permissions.defaultMode` | `"auto"` | セッションを既定で auto mode で開始する（classifier が安全な操作を自動承認する） |
| `outputStyle` | `"Explanatory"` | Claude Code組み込みの説明スタイルを選択する |
| `language` | `"日本語"` | 応答言語を日本語に固定する |
| `effortLevel` | `"xhigh"` | reasoning effort を xhigh で永続化する |
| `attribution.commit` / `attribution.pr` | 空文字 | コミットおよび PR 説明から Claude の署名を抑止する |
| `fileCheckpointingEnabled` | `true` | 編集前ファイルをスナップショットし `/rewind` で巻き戻せるようにする |
| `tui` | `"fullscreen"` | ちらつきの無い alt-screen レンダラ + 仮想化スクロールバックを有効化する |
| `showTurnDuration` | `true` | アシスタントターンごとの所要時間を表示する |
| `showMessageTimestamps` | `true` | 各メッセージにタイムスタンプを付与する |
| `feedbackSurveyRate` | `0` | セッション品質アンケートを抑止する |

`*.config`や`appsettings.json`のような一般的なアプリ設定はglobal denyに含めない。これらに秘密情報を置くrepositoryでは、`.claude/settings.json`または`.claude/settings.local.json`でdenyを追加する。

> **status line の `command` は OS 別に書き換わる**: テンプレートの `~/.claude/statusline.py` は POSIX シェル（Linux / macOS / Git Bash / WSL2）向け。ネイティブ Windows（`cmd.exe`）は `~` 展開も `.py` 直接実行もできないため、Python CLI がインストール時の Python を明示した `"C:/.../python.exe" "C:/Users/.../.claude/statusline.py"` 形式へ書き換える。POSIXでは `~` パスのまま（shebang + 実行ビットで起動）。

### Codex `config.toml` の取り扱い

`~/.codex/config.toml`はagent-configが完全管理する。installは既存内容をマージせず、`templates/config.toml`とバイト単位で一致する通常のテンプレートファイルとして配置する。

- 初回installはテンプレートから`~/.codex/config.toml`を作成する
- 2回目以降もテンプレート全体を正本とし、既存の未知key、project trust、MCP、apps/plugins等は保持しない
- 内容を置換する場合は既存ファイルを`config.toml.bak`へ退避する
- 再installは同じ内容へ収束し、`verify`はテンプレートとの差分をすべてdriftとして検出する
- マシン固有または一時的な設定は、CLI flagや明示的なprofileなど別の設定経路を使う

### 共通 AI エージェント指針の取り扱い

`templates/CLAUDE.md` は全プロジェクト共通の AI coding agent 動作指針で、リポジトリ内で唯一の正本。ツールごとに読み込むファイル名が違うだけなので、installer が同じ内容を各ツールのファイル名へ配布する。

| Destination | 配布条件 |
| --- | --- |
| `~/.claude/CLAUDE.md` | 常に |
| `~/.codex/AGENTS.md` | 常に |

配布後の 2 ファイルは `templates/CLAUDE.md` とバイト単位で一致する。テンプレートを唯一の正本として毎回上書きするため、リポジトリ側の更新がそのまま各マシンへ反映される。指針を変える場合は `templates/CLAUDE.md` を編集し、再インストールする。

内容はツール非依存に保つ。モデル名、推論強度、permission、承認ポリシーのような実行時設定は、各ツール固有の設定ファイル（`templates/settings.json` / `templates/config.toml`）側の責務とし、共通ガイドラインにツール別の分岐を持たせない。再帰削除、ハードリセット、強制プッシュ、権限変更、秘密情報の読み取り、外部サービスへの書き込みといった危険操作は、共通ガイドラインの安全規約でも抑止する。Codexの既定profileは`:workspace + on-request + auto_review`とし、host全体を開く場合だけ`trusted` profileを明示選択する。

マシン固有・個人ローカルな指示は配布対象の正本へ書かない。Claude Codeでは各リポジトリの`CLAUDE.local.md`（git管理外）へ置く。Codexでは`AGENTS.override.md`が同じdirectoryの`AGENTS.md` / fallbackを置き換えるため、必要な通常指示も含めたlocal overrideとして使う。ユーザーレベルの`~/.claude/CLAUDE.local.md`は自動読み込みされない。

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

検証対象はインストール時と同じ構成要素の選択規則に従う。通常はClaude、Codex、共用skillを検証し、`--claude-dir <dir>`を指定すると、そのディレクトリへのインストール結果を検証する。

`scripts/cli.py` の unittest (Linux / macOS / Windows で実行可能):

```bash
# Linux / macOS
python3 -m unittest discover -s scripts/tests -t scripts -v
```

```powershell
# Windows
python -m unittest discover -s scripts/tests -t scripts -v
```

GitHub Actions (`.github/workflows/tests.yml`) は pull request ごとに `ubuntu-latest` の Python 3.9 / 3.12 / 3.13 マトリクスで unittest と bash wrapper の smoke test を実行する。`macos-latest` / `windows-latest` は workflow_dispatch で OS を選択（`all` で全 OS）して手動実行する。

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

このコマンドは配布済みのテンプレート管理対象を `*.bak` に退避してから削除する。利用者・runtime固有値を保持する`~/.claude/settings.json`だけは対象から除外している。`--claude-dir <dir>` を付けると、そのディレクトリへ配布した分を同じ規律で撤去する。

## 反映先マッピング

| Repository Source | Destination |
| --- | --- |
| `templates/CLAUDE.md` | `~/.claude/CLAUDE.md` |
| `templates/CLAUDE.md` | `~/.codex/AGENTS.md` |
| `templates/skills/` | `~/.claude/skills/` |
| `templates/statusline.py` | `~/.claude/statusline.py` |
| `templates/subagent-statusline.py` | `~/.claude/subagent-statusline.py` |
| `templates/settings.json` | `~/.claude/settings.json` (浅いマージ) |
| `templates/config.toml` | `~/.codex/config.toml` (完全管理) |
| `templates/codex/*.config.toml` | `~/.codex/*.config.toml` |
| `templates/codex-rules/agent-config.rules` | `~/.codex/rules/agent-config.rules` |
| `templates/skills/` | `~/.agents/skills/` |

注記: `~/.codex/rules/default.rules`はCodex runtime・利用者側の所有とし、agent-configは変更しない。`--claude-dir <dir>` 指定時の反映先は「別の設定ディレクトリへインストールする」を参照。

## 公式仕様

- Claude Code
  - Best practices: `https://code.claude.com/docs/en/best-practices`
  - Memory (`CLAUDE.md`): `https://code.claude.com/docs/en/memory`
  - Skills: `https://code.claude.com/docs/en/skills`
  - Sub-agents: `https://code.claude.com/docs/en/sub-agents`
  - Hooks: `https://code.claude.com/docs/en/hooks`
  - Settings: `https://code.claude.com/docs/en/settings`
  - Status line: `https://code.claude.com/docs/en/statusline`
- OpenAI Codex CLI
  - CLI Overview: `https://developers.openai.com/codex/cli`
  - Config Basics: `https://developers.openai.com/codex/config-basic`
  - Config Reference: `https://developers.openai.com/codex/config-reference`
  - Permissions: `https://learn.chatgpt.com/docs/permissions`
  - Auto Review: `https://learn.chatgpt.com/docs/sandboxing/auto-review`
  - Advanced Config: `https://learn.chatgpt.com/docs/config-file/config-advanced`
  - Rules: `https://developers.openai.com/codex/rules`
  - Hooks: `https://developers.openai.com/codex/hooks`
  - AGENTS.md: `https://developers.openai.com/codex/guides/agents-md`
  - Skills: `https://developers.openai.com/codex/skills`
## Codex 設計メモ

> 外部製品の仕様は2026年9月5日に公式文書とCodex CLI 0.153.4で確認した。設定値の正本は`templates/config.toml`と`templates/codex/*.config.toml`である。

- model、reasoning effort、verbosityは固定せず、Codexと選択したmodelのbuilt-in presetに追従する
- `personality = "pragmatic"` はagent-config固有の応答方針として維持する
- `web_search = "live"` を明示し、web検索は常に最新データを取得する
- Memoriesは暗黙に有効化せず、永続的な指示は`AGENTS.md`とSkillsで管理する
- TUI は `alternate_screen = "never"` を使い、端末 scrollback を保持する。ターン完了を通知し、status line はモデル、git、作業ディレクトリ、コンテキスト、利用制限、トークン、変更状態、推定コスト、タスク進捗を表示する
- 新規環境のdefaultは`:workspace + on-request + auto_review`とする。base / readonly / trustedはいずれもPermission Profilesを使い、legacy `sandbox_mode`とは併用しない
- `trusted` profileは`:danger-full-access`を明示選択し、repoと入力を完全に信頼できる作業または外部隔離済み環境だけで使う
- `readonly` profileは`:read-only + approval_policy = "never"`とし、昇格なしで探索する
- `agent-config.rules`は`git push`、`git reset`、`rm`、主要な`gh` write commandの代表的なargv prefixをapproval reviewへ送る補助境界である。global optionや別ツールを含む全同義表現の意味解析は保証せず、workspace sandboxと共通 guidelineを本境界にする
- `~/.codex/rules/default.rules`はCodex runtime・利用者の所有とし、agent-configは別ファイルを配布する
- `project_doc_fallback_filenames = ["CLAUDE.md"]` を設定し、既存リポジトリとの互換を保っている
- 外部エディタ起動はシェルの `VISUAL` / `EDITOR` に委ねている

## スキル一覧

| スキル | 説明 |
| --- | --- |
| `km-japanese-refine` | 日本語の説明・指示文を、意味を保って自然で簡潔に推敲する |
| `km-review` | 実装した変更をレビューして欠陥を洗い出す |
| `km-third-party-oss-security-review` | npm / pip / VS Code extension / GitHub リポジトリの採用前セキュリティレビュー |
| `km-commit` | Conventional Commits 形式で git commit |
| `km-github-workflow` | GitHub管理リポジトリの変更をissue・PRとして提出し、明示された場合はマージまで完了する |
| `km-skill-eval` | 挙動資産の変更効果を、明示依頼に基づいて実シナリオで評価する |
| `km-plan` | 複雑で誤方向の手戻りが大きい変更について、背景と設計判断を含む実装計画を作成し、GitHub issueにする |

## ライセンス

MIT License。詳細は `LICENSE` を参照。
