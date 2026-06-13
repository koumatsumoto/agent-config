---
name: km:open-html
description: ローカルの HTML ファイルを既定ブラウザで開く（Windows / WSL Ubuntu のみ）。"ブラウザで開いて" のときに使う。
argument-hint: "[path.html]"
---

# Open HTML

ローカルの HTML ファイルを既定ブラウザで開く。対応環境は **Windows** と **WSL (Ubuntu)** のみ。

## Context

- Platform: !`uname -sr 2>/dev/null || echo unknown`
- WSL?: !`grep -qi microsoft /proc/version 2>/dev/null && echo yes || echo no`

## Success Criteria

- 対象 HTML を既定ブラウザで開く
- 対応外環境では何もせず、未対応である旨を伝える

## Workflow

1. 対象ファイルを決める（`$ARGUMENTS` のパス、無ければ直近に生成・言及した `.html`）。存在を確認する
2. 環境を判定する（WSL / Windows / それ以外）
3. 環境に応じて開く（下記）。開けたら絶対パスを添えて報告する

## 開き方

### WSL (Ubuntu)

WSL から Windows 既定ブラウザで開く。`wslview` があれば最優先、無ければ Windows パスへ変換して `explorer.exe` で開く。

```bash
if command -v wslview >/dev/null 2>&1; then
  wslview "<file>"
else
  explorer.exe "$(wslpath -w "<file>")"
fi
```

- `explorer.exe` は成功時でも非 0 を返すことがある。終了コードではなくブラウザが開いたかで判断する

### Windows (Git Bash / MSYS)

```bash
start "" "<file>"
# start が使えない場合
powershell.exe -NoProfile -Command "Start-Process '<file>'"
```

- パスが MSYS 形式（`/c/...`）なら `cygpath -w` で Windows パスへ変換してから渡す

## Safety Rules

- 対応は Windows / WSL (Ubuntu) のみ。素の Linux / macOS など他環境は開かず「未対応」と伝えて止まる
- 開く対象はユーザーが意図したローカル HTML / 既知のパスに限る。未検証の外部 URL を勝手に開かない
- ファイルが存在しない場合は開かずに知らせる
