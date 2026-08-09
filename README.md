# agent-config

Claude Code / Codex CLI / Qwen Code の共通設定テンプレートを管理するリポジトリ。

## 概要

- 正本は `templates/` 配下
- `scripts/cli.py` で `~/.claude/`、`~/.codex/`、`~/.agents/skills/` に反映 (Linux / macOS / Windows 対応)
- 共通 agent guideline の正本は `templates/CLAUDE.md` 1 ファイル。各ツールが要求するファイル名 (`~/.claude/CLAUDE.md` / `~/.codex/AGENTS.md` / `~/.qwen/QWEN.md`) へ同じ内容を配布する
- Qwen Code (`~/.qwen/`) は opt-in。`--qwen` を付けたときだけ配布対象に加わる
- `--claude-dir <dir>` で `CLAUDE_CONFIG_DIR` 用の別プロファイルにも配布できる
- Linux / macOS / Git Bash では `install.sh` / `clean.sh` などのシェルラッパーから呼び出せる
- リポジトリ内の `README.md` と `docs/` は説明用。runtime contract は `templates/` 側を正とする

## Source Of Truth

- `templates/CLAUDE.md` - Claude Code / Codex CLI / Qwen Code 共通の agent guideline (唯一の正本)
- `templates/rules/` - Claude Code 向け markdown rules
- `templates/skills/` - Claude / Codex / Qwen Code 共用の skills
- `templates/output-styles/` - Claude Code 向け custom output styles (モデル切替時の行動規範。`fable-like` 同梱)
- `templates/config.toml` - Codex CLI 用設定テンプレート
- `templates/codex/*.config.toml` - Codex CLI 用 profile テンプレート (`~/.codex/<profile>.config.toml`)
- `templates/codex-rules/` - Codex CLI 用 exec policy rules
- `templates/statusline.py` - Claude Code 用 status line (リッチ 2 行レイアウト)
- `templates/subagent-statusline.py` - Claude Code サブエージェント行の status line
- `templates/settings.json` - Claude Code 推奨 settings.json ベースライン (既存ファイルへは shallow merge)
- `templates/qwen-settings.json` - Qwen Code 推奨 settings.json ベースライン (`--qwen` 指定時のみ利用。既存ファイルへは shallow merge)

`docs/` は参考資料として残す。履歴メモや検討計画は git で追跡し、作業中の計画メモが必要な場合は repo 直下の `.plan/` に置く。

## ディレクトリ構造

- `templates/` - 配布対象テンプレート
- `scripts/` - Python CLI 本体と補助スクリプト
- `scripts/cli.py` - インストーラ / クリーナ / 検証 / settings マージを束ねる Python CLI
- `scripts/tests/` - `scripts/cli.py` の unittest
- `evals/` - 挙動資産ごとの scenario bank。配布対象ではなく、`km-skill-improve` で改善を検証するときの材料
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

要件: Python 3.9+ (stdlib のみで動作。外部依存なし)。bash ラッパーは `python3`、`python` の順に PATH を探索し、要件を満たす interpreter を使う。特定の OS パッケージマネージャーには依存しない。

最低版を Python 3.9 とするのは、サポート対象の macOS 26.2 で初期状態から利用できる `/usr/bin/python3` が Python 3.9.6 だからである。これにより、パッケージマネージャーで別の Python を追加せずに `./install.sh` を実行できる。

> **OS ごとの Python**: Linux / macOS の例は `python3`、Windows の例は `python` と表記する。macOS では `python` が存在しない場合があるため `python3` を先に探索する。installer 自体は macOS 固有の system Python や特定の導入方法に依存しない。

サポート境界は次のとおり。

| OS | 推奨入口 | platform 固有処理 |
| --- | --- | --- |
| Linux | `./install.sh` | POSIX permission と Python 3.9+ の interpreter 探索 |
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
- `~/.codex/*.config.toml` (Codex profile: `readonly`)
- `~/.codex/rules/`
- `~/.agents/skills/`

`~/.qwen/` は対象外。Qwen Code を配布したい場合は `--qwen` を付ける (後述)。

`settings.json` 以外の既存ファイルは上書き前に `*.bak` へ退避される。バックアップは単一世代。

`rules` / `skills` ツリーは配備先をテンプレートに一致させる。**管理ディレクトリ内のテンプレートに無いファイル / サブディレクトリは prune する** (`pruned: ...` 出力、`*.bak` へ退避)。ただし **ツリー直下のトップレベルエントリ (テンプレートに無いファイル・ディレクトリ — ユーザが置いた独自 skill 等) は保護され、prune されない**。

配布を終了した組み込み skill 名と、組み込み skill の rename 前の旧名は明示管理する。skill loader による誤検出を防ぐため、installer は該当する現行ディレクトリと同名バックアップを `skills/` から削除する。既存の sibling `retired-skills/` も削除し、新旧または退役済みの skill を discovery 対象の近傍へ残さない。

`km-kaizen` の退役時、repo-local の `.kaizen/` は自動収集しない。外部 issue 作成や他 repo の削除を installer の副作用にしないため、残存 entry は利用者が確認し、後続対応の価値を説明できるものだけ follow-up issue へ移して残りを削除する。

### Qwen Code も配布する (`--qwen`)

Qwen Code 向けの配布は opt-in。`--qwen` は「Qwen だけを対象にする」selector ではなく、通常の配布対象へ Qwen component を**追加**する additive flag で、`install` / `verify` / `clean` のどれでも同じ意味を持つ。

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
| `templates/qwen-settings.json` | `~/.qwen/settings.json` (shallow merge) |

- 対象 component は CLI 引数を解釈した時点で確定し、`install` / `verify` / `clean` は同じ選択結果を使う。コマンド間で対象がずれることはない
- `--qwen` 無しのコマンドは `~/.qwen` に一切触れない。ディレクトリの作成も、skill tree の prune も、退役 skill の削除も、settings の merge も行わない。`~/.qwen` が既にある場合もその内容を変更しない
- `verify` は `--qwen` を付けたときだけ Qwen を検証対象にする。`--qwen` 無しで install した状態に `verify --qwen` を実行すると、Qwen 側の managed artifacts の欠落を通常の verify failure として報告する
- `clean --qwen` は Qwen の managed artifacts を `*.bak` へ退避して撤去するが、`~/.qwen/settings.json` はユーザ固有キーを含み得るため既存の clean contract どおり保持する
- `--qwen` と `--claude-dir` は併用できない。`--claude-dir` は Claude Code の設定 slice を別 root へ再配置するオプションで、`--qwen` は `$HOME/.qwen` を対象にするため、1 コマンドで無関係な 2 つの root を書き換えることになる。併用時は filesystem を触る前に usage error (exit code `2`) として拒否する
- Qwen を agent-config の管理下に置き続けたい場合は、以降のコマンドで `--qwen` を指定する。既に `~/.qwen` を持つ環境で `--qwen` 無しのコマンドを実行しても、自動 migration (削除・更新・prune) は行わない
- `--qwen` を付け忘れると `~/.qwen` は配布時点の内容で固定され、`verify` (`--qwen` 無し) も検証対象に含めないため drift を検出しない。管理下に置くと決めたら 3 コマンドとも `--qwen` を付ける
- **初回 `--qwen` は `~/.qwen/skills/` を管理下に取り込む**。ツリー直下のユーザ独自 skill は prune されないが、配布を終了した組み込み skill 名 (`plan` / `commit` / `review` など) と一致するディレクトリは `*.bak` を残さず削除される (`~/.claude/skills/` / `~/.agents/skills/` と同じ規律)。同名の自作 skill がある場合は先に退避する

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

`CLAUDE_CONFIG_DIR` は `~/.claude` そのものを置き換えるため、指定ディレクトリ**直下**へ配置する。

| Repository Source | Destination (`--claude-dir <dir>`) |
| --- | --- |
| `templates/CLAUDE.md` | `<dir>/CLAUDE.md` |
| `templates/rules/` | `<dir>/rules/` |
| `templates/skills/` | `<dir>/skills/` |
| `templates/output-styles/` | `<dir>/output-styles/` |
| `templates/statusline.py` | `<dir>/statusline.py` |
| `templates/subagent-statusline.py` | `<dir>/subagent-statusline.py` |
| `templates/settings.json` | `<dir>/settings.json` (shallow merge) |

配布内容は `~/.claude` 向けの manifest から導出する。`~/.claude` に配るものが増減すれば、指定ディレクトリ側も同じだけ増減する。

- 対象は Claude Code の設定ディレクトリのみ。Codex (`~/.codex`) / Qwen Code (`~/.qwen`) / 共用 skills (`~/.agents/skills`) は各ツールが自前のパスを見るため配布しない。`--qwen` との併用は usage error
- `settings.json` の status line は指定ディレクトリのスクリプトを指すよう書き換える (ホーム配下なら `~/.claude-sub/statusline.py`、ホーム外なら絶対パス)
- 既存ファイルの `*.bak` 退避、prune、退役 skill の削除、POSIX permission (`0700` / `0600`) は既定インストールと同じ規律で動く
- `clean` / `verify` も同じオプションを受け取る
- ディレクトリが無ければ `0700` で作成する。ホームディレクトリ自身・ファイルシステムのルート・既存の非ディレクトリは拒否する
- `CLAUDE_CONFIG_DIR` 環境変数は参照しない。それを export したシェルからの `./install.sh` も `~/.claude` を対象にし、配布先の切り替えは常に明示操作にする

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
| `permissions.defaultMode` | `"auto"` | セッションを既定で auto mode で開始する（classifier が安全な操作を自動承認する） |
| `language` | `"日本語"` | 応答言語を日本語に固定する |
| `effortLevel` | `"xhigh"` | reasoning effort を xhigh で永続化する |
| `attribution.commit` / `attribution.pr` | 空文字 | コミットおよび PR 説明から Claude の署名を抑止する |
| `fileCheckpointingEnabled` | `true` | 編集前ファイルをスナップショットし `/rewind` で巻き戻せるようにする |
| `tui` | `"fullscreen"` | ちらつきの無い alt-screen レンダラ + 仮想化スクロールバックを有効化する |
| `showTurnDuration` | `true` | アシスタントターンごとの所要時間を表示する |
| `showMessageTimestamps` | `true` | 各メッセージにタイムスタンプを付与する |
| `feedbackSurveyRate` | `0` | セッション品質アンケートを抑止する |

> **status line の `command` は OS 別に書き換わる**: テンプレートの `~/.claude/statusline.py` は POSIX シェル（Linux / macOS / Git Bash / WSL2）向け。ネイティブ Windows（`cmd.exe`）は `~` 展開も `.py` 直接実行もできないため、Python CLI がインストール時の Python を明示した `"C:/.../python.exe" "C:/Users/.../.claude/statusline.py"` 形式へ書き換える。POSIX では `~` パスのまま（shebang + 実行ビットで起動）。

### 共通 agent guideline の取り扱い

`templates/CLAUDE.md` は全プロジェクト共通の AI coding agent 動作指針で、リポジトリ内で唯一の正本。ツールごとに読み込むファイル名が違うだけなので、installer が同じ内容を各ツールのファイル名へ配布する。

| Destination | 配布条件 |
| --- | --- |
| `~/.claude/CLAUDE.md` | 常に |
| `~/.codex/AGENTS.md` | 常に |
| `~/.qwen/QWEN.md` | `--qwen` 指定時のみ |

配布後の 3 ファイルは `templates/CLAUDE.md` と byte-for-byte 一致する。テンプレートを source of truth として毎回上書きするため、repo 側の更新がそのまま各マシンへ伝播する。指針を変えたい場合は `templates/CLAUDE.md` を編集して再 install する。

内容はツール非依存に保つ。モデル名・reasoning effort・sandbox・承認ポリシーのような実行時設定は各ツール固有の設定ファイル (`templates/settings.json` / `templates/config.toml` / `templates/qwen-settings.json`) 側の責務とし、共通 guideline にツール別の分岐を持たせない。危険操作の抑止 (recursive deletion / hard reset / force push / 権限変更 / 秘密情報の読み取り / 外部サービスへの書き込み) は共通 guideline の安全規約が担う。Codex default profile は `approval_policy = "never"` / `sandbox_mode = "danger-full-access"` で動くため、この行動規範が実質的な安全境界になる。

マシン固有・個人ローカルなルールはこれらのファイルに書かない（次の install で失われる）。プロジェクト単位のローカル上書きは各リポジトリ直下の `CLAUDE.local.md`（git 管理外）に置く。ユーザレベルの `~/.claude/CLAUDE.local.md` は自動読み込みされない。

### Output Styles の取り扱い

`templates/output-styles/` は Claude Code の custom output style を `~/.claude/output-styles/` へ配布する。同梱の `fable-like` は、モデルを Opus / Sonnet に切り替えたセッションでも Fable 5 相当の行動様式（結論先行の報告・即行動・検証の実証・スコープ規律）を system prompt 末尾に注入する（`keep-coding-instructions: true` により組み込みのソフトウェアエンジニアリング指示は保持する）。

- **有効化**: `/config` → Output style で `fable-like` を選ぶ（選択は local レベル = プロジェクトの `.claude/settings.local.json` に保存）か、`.claude/settings.local.json` に `"outputStyle": "fable-like"` を直接書く。反映は `/clear` または新セッション（style は session 開始時にのみ読み込まれる）
- **運用注意**: user レベル `~/.claude/settings.json` の `outputStyle` はテンプレート宣言キー（既定 `Explanatory`）で、install 再実行のたびに repo の値へ戻る。そのため fable-like は user レベルでなく**プロジェクトレベル**（`.claude/settings.local.json` 等）で有効化する
- **無効化 (Fable に戻す)**: `/config` で outputStyle を元に戻すか、`.claude/settings.local.json` の `outputStyle` を削除する。反映は同じく `/clear` または新セッション

### Qwen Code `settings.json` の取り扱い

`templates/qwen-settings.json` は Claude Code 用と同様に **shallow merge** で `~/.qwen/settings.json` へ反映する (`--qwen` 指定時のみ)。

- 初回インストール時: テンプレート全体を `~/.qwen/settings.json` として作成する
- 2 回目以降: テンプレートが宣言するトップレベルキーはテンプレート値で上書きし、テンプレートが宣言しないキー (`env`, `modelProviders`, `model`, `providerMetadata` 等) はユーザ設定を保持する
- `model` キーはテンプレートに含めない。shallow merge がトップレベルキーを丸ごと置換するため、含めると既存の `model.name`・`model.baseUrl` が脱落する。`model.reasoningEffort` はユーザ側で設定する

`templates/qwen-settings.json` が配布する推奨キー:

| キー | 値 | 目的 |
| --- | --- | --- |
| `fastModel` | `"qwen3.6-flash"` | Auto Mode の classifier (stage 1) とバックグラウンド処理に軽量モデルを使う。空欄だと classifier がメインモデルへフォールバックし、重量級モデルでは stage 1 がタイムアウトして手動承認に落ちる |
| `tools.approvalMode` | `"auto"` | LLM classifier が安全な操作を自動承認する (Claude Code の `defaultMode: "auto"` 相当) |
| `permissions.deny` | `.env` / 秘密鍵 / `secrets/` 等の読み取り禁止 | 機密ファイルへのアクセスを既定で遮断する (Claude Code と同等) |
| `general.outputLanguage` | `"日本語"` | 応答言語を日本語に固定する |

`tools.sandbox` は配布しない。Linux / WSL では Docker/Podman のコンテナ隔離が使われ、ホストのツールや認証情報にアクセスできず日常的な運用を阻害するため。サンドボックスは公式既定どおり無効とし、信頼できないコードを扱うときだけ `qwen -s` または `QWEN_SANDBOX=true` でセッション単位で有効化する。

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

検証対象は install と同じ component selection に従う。`--qwen` 無しなら Claude / Codex / 共用 skills だけを検証し、`~/.qwen` が無くても成功する。`--qwen` を付けると Qwen component も検証対象に加わる。`--claude-dir <dir>` を付けると、そのディレクトリへのインストール結果を検証する。

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

このコマンドは配布済みのテンプレート管理対象を `*.bak` に退避してから削除する。`~/.claude/settings.json` はユーザのカスタマイズが含まれ得るため対象から除外している。`--claude-dir <dir>` を付けると、そのディレクトリへ配布した分を同じ規律で撤去する。

撤去対象も install / verify と同じ component selection に従う。`--qwen` 無しでは `~/.qwen` に触れない (過去に配布した `.qwen` が残っていても変更しない)。`--qwen` を付けると Qwen の managed artifacts も撤去するが、`~/.qwen/settings.json` は同じ理由で保持する。

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
| `templates/CLAUDE.md` | `~/.codex/AGENTS.md` |
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

`--qwen` 指定時のみ追加:

| Repository Source | Destination |
| --- | --- |
| `templates/CLAUDE.md` | `~/.qwen/QWEN.md` |
| `templates/skills/` | `~/.qwen/skills/` |
| `templates/qwen-settings.json` | `~/.qwen/settings.json` (shallow merge) |

注記: `templates/rules/` は Claude Code 向け markdown rules を指す。Codex CLI の exec policy rules は `templates/codex-rules/` から `~/.codex/rules/` へ配布する。`--claude-dir <dir>` 指定時の反映先は「別の設定ディレクトリへインストールする」を参照。

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
- Qwen Code
  - Settings: `https://qwenlm.github.io/qwen-code-docs/configuration/settings`
  - Skills: `https://qwenlm.github.io/qwen-code-docs/features/skills`
  - Approval Mode: `https://qwenlm.github.io/qwen-code-docs/features/approval-mode`
  - Extensions: `https://qwenlm.github.io/qwen-code-docs/extension/introduction`

## Codex 設計メモ

- default model は `gpt-5.6-sol`、reasoning effort は `high`、personality は `pragmatic`、verbosity は `low` にして、複雑な実装を簡潔に報告する
- 管理する reasoning effort は `high` に絞り、`low` / `ultra` は使わない
- `web_search = "cached"` を明示し、通常調査はキャッシュ検索を使う。最新確認が必要な場合は live web を明示して使う
- `plan_mode_reasoning_effort = "high"` を明示し、Plan mode でも reasoning effort を `high` に保つ
- `check_for_update_on_startup = true` を明示し、更新確認をローカル設定で無効化しない前提にしている
- stable な機能のうち platform 差分が小さいものだけを `[features]` で明示し、将来の既定値変更で挙動がぶれにくいようにしている
- TUI は `alternate_screen = "never"` を使い、端末 scrollback を保持する
- default は `danger-full-access + never` を前提にする。sandbox も承認もない完全信頼の自律運用で、`approval_policy = "never"` は常時自動実行扱い。危険操作は設定では止まらず、共通 guideline (`templates/CLAUDE.md` → `~/.codex/AGENTS.md`) の安全規約とリポジトリごとのルールで制御する
- Codex profile は `~/.codex/<profile>.config.toml` として配布する。管理対象は `readonly` だけに絞る
- `~/.codex/rules/` は承認が有効なときに force push、hard reset、外部 recursive delete、GitHub 書き込みなどを prompt 承認へ寄せる。日常的な危険コマンドの抑止は共通 guideline (`templates/CLAUDE.md`) の安全規約で扱う
- 読み取り専用で探索したい場合は `readonly` profile を使う
- `project_doc_fallback_filenames = ["CLAUDE.md"]` を設定し、既存リポジトリとの互換を保っている
- 外部エディタ起動はシェルの `VISUAL` / `EDITOR` に委ねている

## スキル一覧

| スキル | 説明 |
| --- | --- |
| `km-review` | 実装後のレビューが常に通る標準ワークフロー。対象 (未コミット / コミット範囲 / PR / サブツリー) を指定でき、main が反証・修正・再検証したうえで、残る material risk に独立レビュア (architect / product / reliability / security) を 0〜2 名だけ割り当てる。severity (CRITICAL / HIGH / MEDIUM / LOW) は影響度の可視化に使い、収束は未解決 blocker の有無だけで制御して `PASS` / `BLOCKED` を判定する |
| `km-third-party-oss-security-review` | npm / pip / VS Code extension / GitHub repo の採用前セキュリティレビュー |
| `km-commit` | Conventional Commits 形式で git commit |
| `km-github-workflow` | GitHub 管理 repo で変更を PR として届けるワークフロー (Plan / Develop / Verify / Report) と、branch / commit / PR / issue 連携 / follow-up issue / 完了報告の delivery 契約 |
| `km-skill-improve` | 挙動資産 (skill / rules / `CLAUDE.md` 等) の変更を実挙動の証拠に変換して採否を決める改善ループ。eval-first で題材を先に固定し、blind A/B・ablation・回帰再走で測り、使った題材を scenario bank に蓄積する |
| `km-plan` | 実装計画を実装 agent への設計ブリーフ (背景 / 現在地 / 設計判断とその理由 / 変更対象 / 反証可能な完了条件) として作り込み、`.plan/` への出力から GitHub issue への全文ミラーまでを行う。高コストな誤方向だけを実装前に止めるため、main が反証・修正したうえで、それでも残るリスクにだけ独立レビュアを 0〜2 名当て、未解決 blocker の有無で `READY` / `BLOCKED` を判定する。可逆な細部は固定せず実装時へ送る |

## ライセンス

MIT License。詳細は `LICENSE` を参照。
