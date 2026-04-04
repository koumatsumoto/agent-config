# Claude Code ターミナルカスタマイズガイド

Claude Code ターミナルのカスタマイズ方法とセキュリティベストプラクティス。

## カスタマイズ一覧

|カテゴリ|設定ファイル|概要|
|---|---|---|
|ステータスライン|`~/.claude/statusline.sh` + `settings.json`|画面下部にモデル・コンテキスト・コスト等を常時表示|
|キーバインド|`~/.claude/keybindings.json`|キーボードショートカットのカスタマイズ|
|Output Styles|`~/.claude/output-styles/*.md` or `/config`|応答スタイルの変更|
|Hooks|`settings.json`|イベント駆動の自動処理（通知、フォーマット等）|
|Vim モード|`settings.json`|プロンプト入力欄での Vim キーバインド|

## 1. ステータスライン

`settings.json` に以下を追加し、スクリプトを配置する。

```json
{
  "statusLine": {
    "type": "command",
    "command": "/home/<user>/.claude/statusline.sh",
    "padding": 2
  }
}
```

テンプレートの `templates/statusline.sh` を `~/.claude/statusline.sh` にコピーして使用する（`install.sh` で自動反映）。

### スクリプトに渡される JSON フィールド

|フィールド|説明|
|---|---|
|`model.display_name`|モデル名|
|`context_window.used_percentage`|コンテキスト使用率|
|`context_window.current_usage`|現在の使用トークン数|
|`context_window.context_window_size`|コンテキストウィンドウサイズ|
|`cost.total_cost_usd`|セッションコスト|
|`worktree.branch`|Git ブランチ名|
|`rate_limits.five_hour.used_percentage`|5時間レート制限の使用率|

### セキュリティ上の注意

- **フルパス（絶対パス）で指定する**: チルダ (`~`) はシェル展開に依存するため、`/home/<user>/.claude/statusline.sh` の形式で記述する
- **PATH を固定する**: スクリプト冒頭で `export PATH="/usr/local/bin:/usr/bin:/bin"` を設定し、PATH 汚染を防止する
- **外部入力をサニタイズする**: ブランチ名等はユーザ制御可能な値。制御文字・ANSI エスケープシーケンスを除去してからターミナルに出力する
- **`echo -e` を避ける**: 未サニタイズの変数がエスケープ解釈される。`printf '%s'` + `'%b'`（カラーコード部分のみ）を使用する
- **数値検証を行う**: 算術展開 `$(( ))` に渡す前に値が数値であることを検証する（bash の算術評価は変数名を再帰展開する）

## 2. キーバインド

`~/.claude/keybindings.json` を作成する。テンプレートは `templates/keybindings.json`。

### 主要なアクション

|アクション|Claude Code デフォルト|説明|
|---|---|---|
|`chat:submit`|Enter|メッセージ送信|
|`chat:newline`|(未設定) ※本リポジトリでは Shift+Enter に設定|改行挿入（送信せず）|
|`chat:externalEditor`|Ctrl+G|外部エディタで編集|
|`chat:stash`|Ctrl+S|プロンプトを一時退避|
|`chat:modelPicker`|Meta+P|モデル切替|
|`chat:fastMode`|Meta+O|Fast モード切替|
|`chat:thinkingToggle`|Meta+T|拡張思考の切替|
|`chat:cycleMode`|Shift+Tab|パーミッションモード切替|
|`app:toggleTodos`|Ctrl+T|タスクリスト表示切替|
|`history:search`|Ctrl+R|履歴検索|

### 推奨設定

`Shift+Enter` で改行を設定すると、複数行入力が容易になる。送信キー（デフォルト `Enter`）はそのまま維持するのが一般的。

`chat:externalEditor` (`Ctrl+G`) を VS Code で使いたい場合は、Claude Code を起動するシェルで `VISUAL` または `EDITOR` を設定する。

```bash
export VISUAL="code --wait"
export EDITOR="code --wait"
```

`bash` なら `~/.bashrc`、`zsh` なら `~/.zshrc` に追記してからシェルを再起動する。

## 3. Output Styles

`/config` → Output style で選択するか、カスタムスタイルを作成する。

### 組み込みスタイル

- **Default**: 標準のソフトウェアエンジニアリング向け
- **Explanatory**: 教育的な解説を追加
- **Learning**: 協調学習モード

### カスタムスタイル

`~/.claude/output-styles/<name>.md` にファイルを作成:

```yaml
---
name: Custom Style
description: 説明
keep-coding-instructions: true
---

カスタム指示をここに記述。
```

## 4. Hooks

`settings.json` の `hooks` セクションでイベント駆動の自動処理を設定する。

### 主要イベント

|イベント|タイミング|活用例|
|---|---|---|
|`Notification`|通知発生時|デスクトップ通知|
|`PreToolUse`|ツール実行前|危険なコマンドをブロック|
|`PostToolUse`|ツール実行後|コードの自動フォーマット|
|`Stop`|応答完了時|完了通知|

### 通知フックの例

以下の例では `matcher: ""` を使用している（全 Notification イベントにマッチ）。Notification イベントは Claude Code がユーザの注意を必要とする場合にのみ発火するため通常は低頻度だが、必要に応じて特定のイベントに絞ることもできる。

#### Linux (notify-send)

```json
{
  "hooks": {
    "Notification": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "notify-send 'Claude Code' 'Action needed'"
      }]
    }]
  }
}
```

#### macOS

```json
{
  "hooks": {
    "Notification": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "osascript -e 'display notification \"Action needed\" with title \"Claude Code\"'"
      }]
    }]
  }
}
```

#### Windows — Git Bash

Git Bash では `powershell.exe` が Windows PATH 経由で利用可能。フルパスで指定する:

```json
{
  "hooks": {
    "Notification": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "C:/WINDOWS/System32/WindowsPowerShell/v1.0/powershell.exe -Command \"[void][Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime]; $t = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02); $n = $t.GetElementsByTagName('text'); $n.Item(0).InnerText = 'Claude Code'; $n.Item(1).InnerText = 'Action needed'; [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('Claude Code').Show([Windows.UI.Notifications.ToastNotification]::new($t))\""
      }]
    }]
  }
}
```

#### Windows — WSL2

WSL2 では `/mnt/c/` プレフィックスでフルパス指定する:

```json
{
  "hooks": {
    "Notification": [{
      "matcher": "",
      "hooks": [{
        "type": "command",
        "command": "/mnt/c/WINDOWS/System32/WindowsPowerShell/v1.0/powershell.exe -Command \"[void][Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime]; $t = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02); $n = $t.GetElementsByTagName('text'); $n.Item(0).InnerText = 'Claude Code'; $n.Item(1).InnerText = 'Action needed'; [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('Claude Code').Show([Windows.UI.Notifications.ToastNotification]::new($t))\""
      }]
    }]
  }
}
```

### フックのセキュリティ注意事項

- **外部コマンドはフルパスで指定する**: 特に Windows 環境（Git Bash / WSL2）の `powershell.exe` は PATH 汚染で偽バイナリが実行される可能性がある
- **matcher は必要なイベントに絞る**: 空文字列 (`""`) は全イベントにマッチし、高頻度でプロセスが起動される

## 5. settings.json セキュリティハードニング

### ファイルパーミッション

```bash
chmod 700 ~/.claude/
chmod 600 ~/.claude/settings.json
chmod 600 ~/.claude/keybindings.json
chmod 700 ~/.claude/statusline.sh
```

`~/.claude/` 配下には hook コマンド、パーミッション設定、credentials 等が含まれるため、他ユーザからの読み取りを防止する。`install.sh` はディレクトリと statusline.sh、keybindings.json のパーミッションを自動設定する。`settings.json` は install.sh の管理対象外のため、手動で `chmod 600` を設定すること。

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

**WSL2:**
- `/mnt/c/` 経由で Windows ファイルシステムにアクセス可能。Bash コマンドで Windows 側のファイルを読み書きできる
- フックで Windows プロセス（powershell.exe 等）を起動すると、Windows 側から `\\wsl$\` 経由で WSL2 ファイルシステムにアクセス可能
- サンドボックスの `allowRead` / `allowWrite` で `/mnt/c/` へのアクセスを制限することを推奨

**共通:**
- 通知フックでは `powershell.exe` をフルパスで指定し PATH 汚染を防止する（Git Bash: `C:/WINDOWS/...`、WSL2: `/mnt/c/WINDOWS/...`）
- `statusline.sh` は bash スクリプトのため、Git Bash / WSL2 のどちらでも動作する
