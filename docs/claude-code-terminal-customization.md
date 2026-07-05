# Claude Code ターミナルカスタマイズガイド

> Optional reference. Not a runtime contract. この文書は導入可能なカスタマイズ例をまとめた参考資料であり、必須設定を定義しない。


Claude Code ターミナルのカスタマイズ方法とセキュリティベストプラクティス。

## カスタマイズ一覧

|カテゴリ|設定ファイル|概要|
|---|---|---|
|ステータスライン|`~/.claude/statusline.py` + `settings.json`|画面下部にモデル・コンテキスト・コスト等を常時表示|
|Output Styles|`~/.claude/output-styles/*.md` or `/config`|応答スタイルの変更|
|Hooks|`settings.json`|イベント駆動の自動処理（フォーマット等）|
|Vim モード|`settings.json`|プロンプト入力欄での Vim キーバインド|

## 1. ステータスライン

`settings.json` に以下を追加し、スクリプトを配置する。本リポジトリの status line は Python 実装 (`templates/statusline.py`) で、Linux / macOS / Windows で動く。

```json
{
  "statusLine": {
    "type": "command",
    "command": "~/.claude/statusline.py",
    "refreshInterval": 30
  },
  "subagentStatusLine": {
    "type": "command",
    "command": "~/.claude/subagent-statusline.py"
  }
}
```

上記はテンプレート (`templates/settings.json`) の値で、POSIX シェル（Linux / macOS / Git Bash / WSL2）向け。`install.sh` は OS に応じて `command` を書き換える: POSIX では `~` パス + shebang のまま起動し、ネイティブ Windows（`cmd.exe`）では `~` 展開も `.py` 直接実行もできないため、インストール時の Python を明示する形式 `"C:/.../python.exe" "C:/Users/.../.claude/statusline.py"` に置換する。

テンプレートの `templates/statusline.py` / `templates/subagent-statusline.py` を `~/.claude/` にコピーして使用する（`install.sh` で自動反映、実行ビット付与込み）。`statusline.py` は最大 2 行を表示する（行 1: モデル/コンテキスト/キャッシュ率/コスト、行 2: git/PR/レート制限）。

### 依存関係

- **Python 3.12+**: 標準ライブラリのみで動作。`jq` 等の外部依存なし（JSON は Python でパース）
- **git**: 行 2 のブランチ・変更行数表示に使用（無い/リポジトリ外なら自動で省略）

### スクリプトに渡される JSON フィールド（主なもの）

|フィールド|説明|
|---|---|
|`model.display_name`|モデル名|
|`effort.level`|reasoning effort (low/medium/high/xhigh/max)|
|`context_window.used_percentage`|コンテキスト使用率|
|`context_window.total_input_tokens`|コンテキスト内の入力トークン数|
|`context_window.context_window_size`|コンテキストウィンドウサイズ (200k / 1M)|
|`context_window.current_usage`|cache 読み書き内訳（cache 率算出に使用）|
|`cost.total_cost_usd` / `cost.total_duration_ms` / `cost.total_api_duration_ms`|コスト / 実時間 / API 時間|
|`rate_limits.{five_hour,seven_day}.{used_percentage,resets_at}`|レート制限の使用率とリセット時刻|
|`pr.number` / `pr.url`|現ブランチの open PR（クリック可能リンク化）|
|`worktree.branch`|Git ブランチ名（worktree セッション時）|
|`session_id`|git 結果のキャッシュキーに使用|

### セキュリティ上の注意

- **POSIX はチルダ (`~`) パスで可搬性を確保**: `command` を `~/.claude/statusline.py` とし、shebang (`#!/usr/bin/env python3`) + 実行ビットで起動する。shebang の改行が CRLF になると `env` が `python3\r` を探して `exit 127` で失敗するため、`.gitattributes` で全テキストを LF 固定し、Windows clone（`core.autocrlf=true`）での LF→CRLF 変換を防ぐ。ネイティブ Windows は shebang を解釈できないため `install.sh` が Python を明示した `command` に置換する（前節参照）
- **git 環境変数をクリアする**: `GIT_DIR` 等を unset し、悪意あるリポジトリからの config / repo 差し替えを防ぐ
- **外部入力をサニタイズする**: モデル名・ブランチ名等の制御文字・ANSI エスケープを除去してから出力する
- **高速・低負荷に保つ**: status line は高頻度（300ms デバウンス）で実行されるため、git 結果は `session_id` キーで数秒キャッシュする

## 2. Output Styles

有効化は `/config` → Output style（選択は local レベル = プロジェクトの `.claude/settings.local.json` に保存）か、settings.json の `outputStyle` キー（user / project / local）で行う。style は session 開始時に一度だけ読み込まれ、変更の反映には `/clear` または新セッションが必要。

### 組み込みスタイル

- **Default**: 標準のソフトウェアエンジニアリング向け
- **Explanatory**: 教育的な解説を追加
- **Learning**: 協調学習モード

### カスタムスタイル

配置場所は user レベル `~/.claude/output-styles/<name>.md` かプロジェクトレベル `.claude/output-styles/<name>.md`。このリポジトリは `fable-like`（モデル切替時に Fable 相当の行動規範を注入）を `templates/output-styles/` から user レベルへ配布する（有効化・運用は README を参照）。独自スタイルを作る場合はファイルを作成:

```yaml
---
name: Custom Style
description: 説明
keep-coding-instructions: true
---

カスタム指示をここに記述。
```

## 3. Hooks

`settings.json` の `hooks` セクションでイベント駆動の自動処理を設定する。

### 主要イベント

|イベント|タイミング|活用例|
|---|---|---|
|`PreToolUse`|ツール実行前|危険なコマンドをブロック|
|`PostToolUse`|ツール実行後|コードの自動フォーマット|
|`Stop`|応答完了時|ログ記録・後処理|

### フックのセキュリティ注意事項

- **外部コマンドはフルパスで指定する**: 特に Windows 環境（Git Bash / WSL2）の `powershell.exe` は PATH 汚染で偽バイナリが実行される可能性がある
- **matcher は必要なイベントに絞る**: 空文字列 (`""`) は全イベントにマッチし、高頻度でプロセスが起動される

## 4. settings.json セキュリティハードニング

### ファイルパーミッション

```bash
chmod 700 ~/.claude/
chmod 600 ~/.claude/settings.json
chmod 700 ~/.claude/statusline.py
chmod 700 ~/.claude/subagent-statusline.py
```

`~/.claude/` 配下には hook コマンド、パーミッション設定、credentials 等が含まれるため、他ユーザからの読み取りを防止する。`install.sh` はディレクトリと statusline.py、subagent-statusline.py のパーミッションを自動設定する。`settings.json` は install.sh による shallow merge 対象だが、パーミッションも `chmod 600` で書き込まれる。

### 多層防御の考え方

Claude Code のセキュリティは単一の仕組みではなく、以下の多層防御で成り立つ:

1. **サンドボックス** (`sandbox.enabled: true` または `/sandbox` コマンド): OS レベルでファイルシステムとネットワークを隔離。最も強力な防御
2. **パーミッションモード** (`defaultMode`): ツール実行の承認フロー
3. **allow / deny リスト**: ベストエフォートのコマンドフィルタ
4. **Hooks** (`PreToolUse`): プログラマティックなツール実行制御

**重要**: deny リストだけでは安全ではない。制約の詳細は「permissions.deny の注意事項」を参照。強固な隔離が必要な場合はサンドボックス (`sandbox.enabled: true`) を使用すること。

### permissions.allow のベストプラクティス

allow リストに含めるコマンドは、組み合わせによる攻撃チェーンを考慮する:

#### 危険な組み合わせ（avoid）

|コマンド|リスク|
|---|---|
|`curl *` + `node *`/`python3 *`|リモートコード取得→実行チェーン|
|`docker *`（無制限）|`docker run --privileged` でホスト特権昇格|
|`aws *`（無制限）|`aws s3 rm --recursive` 等の破壊操作|
|`env *` / `printenv *`|機密環境変数の漏洩 + 外部送信|
|`xargs *`|任意コマンドの間接実行（deny バイパス）|
|`chmod *`（無制限）|`chmod 000` でファイルアクセス除去|
|`pip install *` / `npm install *`|サプライチェーン攻撃（インストール時の任意コード実行）|
|`git clone *`|post-checkout フック経由の任意コード実行|

#### 推奨: サブコマンド単位で許可

```json
{
  "permissions": {
    "allow": [
      "Bash(docker ps *)",
      "Bash(docker images *)",
      "Bash(docker logs *)",
      "Bash(docker inspect *)",
      "Bash(aws s3 ls *)",
      "Bash(aws sts get-caller-identity *)"
    ]
  }
}
```

### permissions.deny の注意事項

deny リストはベストエフォートの追加防御であり、以下の制約がある:

- **glob パターンマッチ**: `*` はワイルドカードとして任意の位置に配置可能だが、`Bash(rm -rf *)` は `rm --recursive --force` にはマッチしない
- **Bash 内のコマンドには Read/Edit deny は無効**: `cat`, `python -c` 等で回避可能
- **未知のコマンドには無力**: deny リスト外のコマンド（`shred`, `truncate` 等）は通過する

より確実な防御には `PreToolUse` フックでプログラマティックにブロックするか、サンドボックスを使用する。

以下は一般的な危険パターンの deny 例:

```json
{
  "permissions": {
    "deny": [
      "Bash(rm -rf *)",
      "Bash(rm -r *)",
      "Bash(rm -f *)",
      "Bash(chmod 777 *)",
      "Bash(chmod 000 *)",
      "Bash(sudo *)",
      "Bash(su *)",
      "Bash(shutdown *)",
      "Bash(reboot *)",
      "Bash(git push --force *)",
      "Bash(git push -f *)",
      "Bash(git reset --hard *)",
      "Bash(git clean -fd *)",
      "Bash(git clean -fdx *)",
      "Bash(docker run --privileged *)",
      "Bash(dd if= *)",
      "Bash(mkfs *)"
    ]
  }
}
```

### Read パーミッションの注意

- `Read(/tmp/**)` は避ける: `/tmp` は全ユーザ書き込み可能。シンボリックリンク経由で任意ファイルが読み取られる
- 特定サブディレクトリに限定するか、必要時に都度承認する

### defaultMode の選択

|モード|説明|推奨用途|
|---|---|---|
|`plan`|分析のみ。ファイル変更・コマンド実行ともに不可|安全な探索・計画|
|`default`|初回使用時にプロンプト|通常の対話的使用|
|`acceptEdits`|ファイル編集を自動承認。Bash は都度確認|編集中心の信頼度の高いワークフロー|
|`dontAsk`|`/permissions` または `permissions.allow` で事前許可されたツールのみ実行。それ以外は自動拒否|セキュアな自動化|
|`auto`|バックグラウンド安全性分類器でリクエストとの整合性を検証し自動承認（research preview）|信頼度の高い自動ワークフロー|
|`bypassPermissions`|全承認プロンプトをスキップ（`.git`, `.claude` 等への書き込みは除く）。コンテナ/VM 等の隔離環境専用|完全隔離された CI/CD 環境|

セキュリティ強度の順序: `plan` > `dontAsk` > `default` > `acceptEdits` > `auto` > `bypassPermissions`

### 追加のセキュリティ考慮事項

#### プロンプトインジェクション対策

悪意のあるリポジトリの CLAUDE.md やファイル内容にプロンプトインジェクションが含まれている場合、Claude に設定ファイルを書き換えさせる攻撃が理論的に可能。対策:

- 信頼できないリポジトリでは `plan` モードで初期探索する
- `ConfigChange` フックで設定変更を監査・ブロックする
- `.claude/settings.json` への書き込みは Claude Code が確認プロンプトを表示する（`bypassPermissions` モード以外）

#### Windows 環境の注意（Git Bash / WSL2 共通）

Windows 上で Claude Code を使用する場合、環境に応じた考慮が必要:

**Git Bash:**
- パスの形式が POSIX 風（`/c/Users/...`）になるが、`powershell.exe` 等の Windows バイナリは `C:/WINDOWS/...` のネイティブパスでも動作する
- `chmod` はファイルシステムが NTFS の場合に制限がある。`install.sh` は `chmod` 失敗時に警告を出力する
- `~/.claude/` は `C:/Users/<user>/.claude/` に対応する
- **Python**: `statusline.py` は Python で動作する。Git Bash から実行する場合は shebang が解決できるよう `python`（または `py`）が PATH 上に必要。`statusLine.command` のパスはフォワードスラッシュで記述する

**WSL2:**
- `/mnt/c/` 経由で Windows ファイルシステムにアクセス可能。Bash コマンドで Windows 側のファイルを読み書きできる
- フックで Windows プロセス（powershell.exe 等）を起動すると、Windows 側から `\\wsl$\` 経由で WSL2 ファイルシステムにアクセス可能
- サンドボックスの `allowRead` / `allowWrite` で `/mnt/c/` へのアクセスを制限することを推奨
- **Python**: 多くの WSL2 ディストリビューションでは `python3` がデフォルトで利用可能。`statusline.py` は標準ライブラリのみで動作する

**共通:**
- `statusline.py` は Python 標準ライブラリのみで動作し、外部依存（jq 等）は不要。Git Bash / WSL2 のどちらでも動作する
