# agent-config

Claude CodeとCodex CLIの共通設定テンプレートを管理する。Qwen Codeは任意で追加できる。

## 概要

- 正本は `templates/` 配下
- `scripts/cli.py` で `~/.claude/`、`~/.codex/`、`~/.agents/skills/` に反映 (Linux / macOS / Windows 対応)
- AI共通ガイドラインの正本は`templates/CLAUDE.md`だけである。各ツールが要求するファイル名（`~/.claude/CLAUDE.md`、`~/.codex/AGENTS.md`、`~/.qwen/QWEN.md`）へ同じ内容を配布する
- Qwen Code（`~/.qwen/`）は任意で追加できる。`--qwen`を付けたときだけ配布対象に加わる
- `--claude-dir <dir>` で `CLAUDE_CONFIG_DIR` 用の別プロファイルにも配布できる
- Linux / macOS / Git Bashでは `install.sh` / `clean.sh` などのシェルラッパーから呼び出せる
- `README.md`は説明資料であり、実行時契約の正本は`templates/`に置く

## 正本

- `templates/CLAUDE.md` - Claude Code、Codex CLI、Qwen Codeに共通するAI共通ガイドライン（唯一の正本）
- `templates/skills/` - Claude / Codex / Qwen Code 共用の skills
- `templates/output-styles/` - Claude Code 向け custom output styles (モデル切替時の行動規範。`fable-like` 同梱)
- `templates/config.toml` - Codex CLI 用設定テンプレート
- `templates/codex/*.config.toml` - Codex CLI用のプロファイルテンプレート（`~/.codex/<profile>.config.toml`）
- `templates/codex-rules/` - Codex CLI 用 exec policy rules
- `templates/statusline.py` - Claude Code 用 status line (リッチ 2 行レイアウト)
- `templates/subagent-statusline.py` - Claude Codeのsubagent status line
- `templates/settings.json` - Claude Code向けの推奨`settings.json`（既存ファイルへは浅くマージ）
- `templates/qwen-settings.json` - Qwen Code向けの推奨`settings.json`（`--qwen`指定時のみ利用。既存ファイルへは浅くマージ）

履歴メモや検討計画はGitで追跡し、作業中の計画メモが必要な場合はリポジトリ直下の`.plan/`に置く。

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
- `~/.claude/output-styles/`
- `~/.claude/statusline.py`
- `~/.claude/subagent-statusline.py`
- `~/.claude/settings.json`（推奨設定を浅くマージ。詳細は後述）
- `~/.codex/AGENTS.md` (詳細は後述)
- `~/.codex/config.toml`
- `~/.codex/*.config.toml` (Codex プロファイル: `readonly` / `trusted`)
- `~/.codex/rules/`
- `~/.agents/skills/`

`~/.qwen/` は対象外。Qwen Code を配布したい場合は `--qwen` を付ける (後述)。

`settings.json`と`~/.codex/config.toml`以外を置き換える前に、既存内容を`*.bak`へ退避する。バックアップは単一世代である。両設定ファイルは利用者・runtime固有の値を保持しながらテンプレート管理値をマージする。

`skills/`はテンプレートに合わせ、管理下の不要項目を削除する（`pruned: ...`と出力し、`*.bak`へ退避）。ただし、ツリー直下に利用者が作成したファイルとディレクトリは保持する。

配布を終了した組み込みskillと改名前の旧名は一覧で管理する。skillの読み込み処理による誤検出を防ぐため、インストーラーは該当する現行ディレクトリと同名バックアップを`skills/`から削除する。既存の同階層にある`retired-skills/`も削除し、新旧または退役済みのskillを検出対象の近くに残さない。

`km-kaizen` の退役時、リポジトリ内の `.kaizen/` は自動収集しない。外部 issue の作成や他のリポジトリの削除をインストーラーの副作用にしないため、残存項目は利用者が確認し、後続対応の価値を説明できるものだけ後続 issue へ移して残りを削除する。

### Qwen Codeを追加する（`--qwen`）

Qwen Code向けの配布は任意で追加できる。`--qwen`はQwen Codeだけを選ぶ指定ではない。通常の配布対象にQwen Codeを追加し、`install`、`verify`、`clean`のどれでも同じ意味を持つ。

```bash
# Linux / macOS
./install.sh                  # Claude + Codex + 共用 skills
./install.sh --qwen           # 上記 + Qwen Code
python3 scripts/cli.py install --qwen
```

```powershell
# Windows
python scripts/cli.py install --qwen
```

`--qwen` を付けたときだけ追加される配布物:

| Repository Source | Destination (`--qwen`) |
| --- | --- |
| `templates/CLAUDE.md` | `~/.qwen/QWEN.md` |
| `templates/skills/` | `~/.qwen/skills/` |
| `templates/qwen-settings.json` | `~/.qwen/settings.json` (浅いマージ) |

- 対象の構成要素は CLI 引数を解釈した時点で確定し、`install` / `verify` / `clean` は同じ選択結果を使う。コマンド間で対象がずれることはない
- `--qwen`を付けない場合、`~/.qwen`は読み書きしない。ディレクトリ作成、skill同期、旧skill削除、設定マージも行わない。`~/.qwen`が既にある場合も内容を変更しない
- `verify` は `--qwen` を付けたときだけ Qwen を検証対象にする。`--qwen` なしでインストールした状態に `verify --qwen` を実行すると、Qwen 側の管理対象ファイルの欠落を通常の検証失敗として報告する
- `clean --qwen`はQwenの管理対象ファイルを`*.bak`へ退避して撤去するが、`~/.qwen/settings.json`はユーザー固有キーを含み得るため、既存のクリーンアップ契約どおり保持する
- `--claude-dir`はClaude Codeの設定を別の基点ディレクトリへ配置し、`--qwen`は`$HOME/.qwen`を対象にする。一つのコマンドで無関係な二つの基点を変更するため、両者は併用できない。併用時はファイルを変更する前に引数エラー（終了コード`2`）で終了する
- Qwen を agent-config の管理下に置き続けたい場合は、以降のコマンドで `--qwen` を指定する。既に `~/.qwen` を持つ環境で `--qwen` 無しのコマンドを実行しても、自動 migration (削除・更新・不要項目の削除) は行わない
- `--qwen` を付け忘れると `~/.qwen` は配布時点の内容で固定され、`verify` (`--qwen` 無し) も検証対象に含めないため drift を検出しない。管理下に置くと決めたら 3 コマンドとも `--qwen` を付ける
- **初めて`--qwen`を指定すると、`~/.qwen/skills/`が管理対象になる**。ツリー直下の利用者独自skillは削除しないが、配布を終了した組み込みskill名（`plan`、`commit`、`review`など）と一致するディレクトリは`*.bak`を残さず削除する。これは`~/.claude/skills/`と`~/.agents/skills/`にも適用する。同名の自作skillがある場合は先に退避する

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
| `templates/output-styles/` | `<dir>/output-styles/` |
| `templates/statusline.py` | `<dir>/statusline.py` |
| `templates/subagent-statusline.py` | `<dir>/subagent-statusline.py` |
| `templates/settings.json` | `<dir>/settings.json` (浅いマージ) |

配布内容は`~/.claude`向けの配布一覧から導出する。`~/.claude`に配るものが増減すれば、指定ディレクトリ側も同じだけ増減する。

- 対象はClaude Codeの設定ディレクトリのみ。Codex（`~/.codex`）、Qwen Code（`~/.qwen`）、共用スキル（`~/.agents/skills`）は各ツールが自前のパスを参照するため配布しない。`--qwen`との併用は引数エラーになる
- `settings.json` の status line は指定ディレクトリのスクリプトを指すよう書き換える (ホーム配下なら `~/.claude-sub/statusline.py`、ホーム外なら絶対パス)
- 既存ファイルの `*.bak` 退避、不要項目の削除、退役 skill の削除、POSIX permission (`0700` / `0600`) は既定インストールと同じ規律で動く
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
| `permissions.deny` | `.env` / 秘密鍵 / `secrets/` 等の読み取り禁止と `Bash(npx *)` | 機密ファイルへのアクセスを既定で遮断する |
| `permissions.defaultMode` | `"auto"` | セッションを既定で auto mode で開始する（classifier が安全な操作を自動承認する） |
| `language` | `"日本語"` | 応答言語を日本語に固定する |
| `effortLevel` | `"xhigh"` | reasoning effort を xhigh で永続化する |
| `attribution.commit` / `attribution.pr` | 空文字 | コミットおよび PR 説明から Claude の署名を抑止する |
| `fileCheckpointingEnabled` | `true` | 編集前ファイルをスナップショットし `/rewind` で巻き戻せるようにする |
| `tui` | `"fullscreen"` | ちらつきの無い alt-screen レンダラ + 仮想化スクロールバックを有効化する |
| `showTurnDuration` | `true` | アシスタントターンごとの所要時間を表示する |
| `showMessageTimestamps` | `true` | 各メッセージにタイムスタンプを付与する |
| `feedbackSurveyRate` | `0` | セッション品質アンケートを抑止する |

> **status line の `command` は OS 別に書き換わる**: テンプレートの `~/.claude/statusline.py` は POSIX シェル（Linux / macOS / Git Bash / WSL2）向け。ネイティブ Windows（`cmd.exe`）は `~` 展開も `.py` 直接実行もできないため、Python CLI がインストール時の Python を明示した `"C:/.../python.exe" "C:/Users/.../.claude/statusline.py"` 形式へ書き換える。POSIXでは `~` パスのまま（shebang + 実行ビットで起動）。

### Codex `config.toml` の取り扱い

`~/.codex/config.toml`はagent-configとCodex runtime・利用者の共同所有ファイルとして扱う。`templates/config.toml`が宣言するsection/keyはテンプレート値へ更新し、それ以外のkeyとtableは保持する。Codexが保存するproject trust、MCP、apps/plugins、keymap、将来追加される未知の設定をinstallで削除しない。

- 初回installはテンプレートから`~/.codex/config.toml`を作成する
- 2回目以降はmanaged keyだけを更新し、既知section内の未知keyとdestinationだけにあるsubtable/tableを保持する
- managed keyがずれた場合だけ`verify`を失敗させる。runtime固有設定が追加されただけではdriftにしない
- マージで内容が変わる場合は既存ファイルを`config.toml.bak`へ退避する
- `clean`はruntime・利用者固有設定を失わないよう`~/.codex/config.toml`を保持する
- Python 3.9 / stdlib-onlyを維持するため、テンプレート側のmanaged構文は通常tableとbare keyの単一行assignmentに限定する。対応外のmanaged構文は書き込まずエラーにする

### 共通 AI エージェント指針の取り扱い

`templates/CLAUDE.md` は全プロジェクト共通の AI coding agent 動作指針で、リポジトリ内で唯一の正本。ツールごとに読み込むファイル名が違うだけなので、installer が同じ内容を各ツールのファイル名へ配布する。

| Destination | 配布条件 |
| --- | --- |
| `~/.claude/CLAUDE.md` | 常に |
| `~/.codex/AGENTS.md` | 常に |
| `~/.qwen/QWEN.md` | `--qwen` 指定時のみ |

配布後の 3 ファイルは `templates/CLAUDE.md` とバイト単位で一致する。テンプレートを唯一の正本として毎回上書きするため、リポジトリ側の更新がそのまま各マシンへ反映される。指針を変える場合は `templates/CLAUDE.md` を編集し、再インストールする。

内容はツール非依存に保つ。モデル名、推論強度、サンドボックス、承認ポリシーのような実行時設定は、各ツール固有の設定ファイル（`templates/settings.json` / `templates/config.toml` / `templates/qwen-settings.json`）側の責務とし、共通ガイドラインにツール別の分岐を持たせない。再帰削除、ハードリセット、強制プッシュ、権限変更、秘密情報の読み取り、外部サービスへの書き込みといった危険操作は、共通ガイドラインの安全規約でも抑止する。Codexの既定は`workspace-write + on-request + auto_review`で、workspace外とcommand networkへの昇格をapproval reviewへ送る。host全体を開く場合だけ`trusted` profileを明示選択する。

マシン固有・個人ローカルな指示は配布対象の正本へ書かない。Claude Codeでは各リポジトリの`CLAUDE.local.md`（git管理外）へ置く。Codexでは`AGENTS.override.md`が同じdirectoryの`AGENTS.md` / fallbackを置き換えるため、必要な通常指示も含めたlocal overrideとして使う。ユーザーレベルの`~/.claude/CLAUDE.local.md`は自動読み込みされない。

### Output Styles の取り扱い

`templates/output-styles/` は Claude Code の custom output style を `~/.claude/output-styles/` へ配布する。同梱の `fable-like` は、モデルを Opus / Sonnet に切り替えたセッションでも Fable 5 相当の行動様式（結論先行の報告・即行動・検証の実証・スコープ規律）を system prompt 末尾に注入する（`keep-coding-instructions: true` により組み込みのソフトウェアエンジニアリング指示は保持する）。

- **有効化**: `/config` → Output style で `fable-like` を選ぶ（選択は local レベル = プロジェクトの `.claude/settings.local.json` に保存）か、`.claude/settings.local.json` に `"outputStyle": "fable-like"` を直接書く。反映は `/clear` または新セッション（style は session 開始時にのみ読み込まれる）
- **運用上の注意**: ユーザーレベルの`~/.claude/settings.json`にある`outputStyle`はテンプレート宣言キー（既定値は`Explanatory`）で、インストールを再実行するたびにリポジトリの値へ戻る。そのため、fable-likeはユーザーレベルではなく**プロジェクトレベル**（`.claude/settings.local.json`など）で有効化する
- **無効化 (Fable に戻す)**: `/config` で outputStyle を元に戻すか、`.claude/settings.local.json` の `outputStyle` を削除する。反映は同じく `/clear` または新セッション

### Qwen Code `settings.json` の取り扱い

`templates/qwen-settings.json` は Claude Code 用と同様に **浅いマージ** で `~/.qwen/settings.json` へ反映する (`--qwen` 指定時のみ)。

- 初回インストール時: テンプレート全体を `~/.qwen/settings.json` として作成する
- 2 回目以降: テンプレートが宣言するトップレベルキーはテンプレート値で上書きし、テンプレートが宣言しないキー (`env`, `modelProviders`, `model`, `providerMetadata` 等) はユーザー設定を保持する
- `model`キーはテンプレートに含めない。浅いマージはトップレベルキーを丸ごと置換するため、含めると既存の`model.name`と`model.baseUrl`が脱落する。`model.reasoningEffort`はユーザー側で設定する

`templates/qwen-settings.json` が配布する推奨キー:

| キー | 値 | 目的 |
| --- | --- | --- |
| `fastModel` | `"qwen3.6-flash"` | Auto Mode の classifier (stage 1) とバックグラウンド処理に軽量モデルを使う。空欄だと classifier がメインモデルへフォールバックし、重量級モデルでは stage 1 がタイムアウトして手動承認に落ちる |
| `tools.approvalMode` | `"auto"` | LLM classifier が安全な操作を自動承認する (Claude Code の `defaultMode: "auto"` 相当) |
| `permissions.deny` | `.env` / 秘密鍵 / `secrets/` 等の読み取り禁止 | 機密ファイルへのアクセスを既定で遮断する (Claude Code と同等) |
| `general.outputLanguage` | `"日本語"` | 応答言語を日本語に固定する |

`tools.sandbox` は配布しない。Linux / WSLでは Docker/Podman のコンテナ隔離が使われ、ホストのツールや認証情報にアクセスできず日常的な運用を阻害するため。サンドボックスは公式既定どおり無効とし、信頼できないコードを扱うときだけ `qwen -s` または `QWEN_SANDBOX=true` でセッション単位で有効化する。

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

検証対象はインストール時と同じ構成要素の選択規則に従う。`--qwen` を指定しなければ Claude、Codex、共用 skill だけを検証し、`~/.qwen` がなくても成功する。`--qwen` を指定すると Qwen の構成要素も検証対象に加わる。`--claude-dir <dir>` を指定すると、そのディレクトリへのインストール結果を検証する。

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

このコマンドは配布済みのテンプレート管理対象を `*.bak` に退避してから削除する。`~/.claude/settings.json`と`~/.codex/config.toml`はユーザー・runtime固有値が含まれ得るため対象から除外している。`--claude-dir <dir>` を付けると、そのディレクトリへ配布した分を同じ規律で撤去する。

撤去対象もインストール・検証時と同じ構成要素の選択規則に従う。`--qwen` を指定しなければ `~/.qwen` に触れず、以前に配布したファイルが残っていても変更しない。`--qwen` を指定すると Qwen の管理対象ファイルも撤去するが、`~/.qwen/settings.json` は同じ理由で保持する。

## 反映先マッピング

| Repository Source | Destination |
| --- | --- |
| `templates/CLAUDE.md` | `~/.claude/CLAUDE.md` |
| `templates/CLAUDE.md` | `~/.codex/AGENTS.md` |
| `templates/skills/` | `~/.claude/skills/` |
| `templates/output-styles/` | `~/.claude/output-styles/` |
| `templates/statusline.py` | `~/.claude/statusline.py` |
| `templates/subagent-statusline.py` | `~/.claude/subagent-statusline.py` |
| `templates/settings.json` | `~/.claude/settings.json` (浅いマージ) |
| `templates/config.toml` | `~/.codex/config.toml` (managed keyをマージ) |
| `templates/codex/*.config.toml` | `~/.codex/*.config.toml` |
| `templates/codex-rules/agent-config.rules` | `~/.codex/rules/agent-config.rules` |
| `templates/skills/` | `~/.agents/skills/` |

`--qwen` 指定時のみ追加:

| Repository Source | Destination |
| --- | --- |
| `templates/CLAUDE.md` | `~/.qwen/QWEN.md` |
| `templates/skills/` | `~/.qwen/skills/` |
| `templates/qwen-settings.json` | `~/.qwen/settings.json` (浅いマージ) |

注記: `~/.codex/rules/default.rules`はCodex runtime・利用者側の所有とし、agent-configは変更しない。旧版が配布した内容とbyte一致する場合だけ、初回migrationで`default.rules.bak`へ退役する。`--claude-dir <dir>` 指定時の反映先は「別の設定ディレクトリへインストールする」を参照。

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
  - Advanced Config: `https://learn.chatgpt.com/docs/config-file/config-advanced`
  - Memories: `https://learn.chatgpt.com/docs/customization/memories`
  - Rules: `https://developers.openai.com/codex/rules`
  - Hooks: `https://developers.openai.com/codex/hooks`
  - AGENTS.md: `https://developers.openai.com/codex/guides/agents-md`
  - Skills: `https://developers.openai.com/codex/skills`
- Qwen Code
  - Settings: `https://qwenlm.github.io/qwen-code-docs/configuration/settings`
  - Skills: `https://qwenlm.github.io/qwen-code-docs/features/skills`
  - Approval Mode: `https://qwenlm.github.io/qwen-code-docs/features/approval-mode`
  - Extensions: `https://qwenlm.github.io/qwen-code-docs/extension/introduction`

## Codex 設計メモ

> 外部製品の仕様は2026年8月29日に公式文書で確認した。設定値の正本は`templates/config.toml`と`templates/codex/*.config.toml`である。

- default model は `gpt-5.6-sol`、reasoning effort は `medium`、personality は `pragmatic`、verbosity は `low` にして、品質と応答速度を両立しながら簡潔に報告する
- `plan_mode_reasoning_effort = "high"` を明示し、実装前の判断には通常の作業より多くの推論を使う。`low` / `ultra` は管理対象にしない
- `web_search = "live"` を明示し、web検索は常に最新データを取得する
- `check_for_update_on_startup = true` を明示し、更新確認をローカル設定で無効化しない前提にしている
- `[features]` には既定値と異なる項目だけを置き、Codex CLI の標準機能改善を取り込む。ローカルメモリは明示的に有効化する
- ローカルメモリは生成と利用の両方を有効にする。生成物は既定で `~/.codex/memories/` に保存され、チャット単位の制御には `/memories` を使う。必須の指示はメモリだけに依存せず `AGENTS.md` に置く
- TUI は `alternate_screen = "never"` を使い、端末 scrollback を保持する。端末が非フォーカスのときにターン完了を通知し、status line はモデル、git、作業ディレクトリ、コンテキスト、利用制限、トークン、変更状態、推定コスト、タスク進捗を色付きで表示する
- 新規環境のdefaultは `workspace-write + on-request + auto_review` とし、workspace内の通常操作だけを自動実行する。既存の`~/.codex/config.toml`にある`sandbox_mode`は端末ローカルの選択として再installでも保持し、その他の管理キーはテンプレートへ同期する
- `trusted` profileは`danger-full-access`を明示選択し、repoと入力を完全に信頼できる作業または外部隔離済み環境だけで使う
- `readonly` profileは`read-only + approval_policy = "never"`とし、昇格なしで探索する
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
