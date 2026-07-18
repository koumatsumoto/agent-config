---
name: km-open-file
description: ローカルのファイル / フォルダを Windows 側で開く（Windows / WSL Ubuntu のみ）。"ブラウザで開いて" / "エクスプローラで開いて" のときに使う。
argument-hint: "[path]"
---

# Open File

ローカルのファイルやフォルダを Windows 側で開く。対応環境は **Windows (Git Bash)** と **WSL (Ubuntu)** のみ。標準コマンド（`uname` / `wslpath` / `cygpath` / `explorer.exe`）だけで動き、追加パッケージ（`wslview` 等）は前提にしない。

開く手段は `explorer.exe` に統一し、対象の種類で扱いを分ける。これにより、開いたファイルがプログラムとして実行されることはない。

- **フォルダ**: Explorer で開く
- **`.html` / `.htm`**: 拡張子の関連付けで既定ブラウザに描画する
- **その他のファイル**: 実行せず、Explorer で選択表示（reveal）するだけにとどめる

入力パスは Linux 形式（`/home/...`, `./x`）でも Windows 形式（`C:\...`, `C:/...`, `\\...`）でも受け付ける。

## Context

- Platform: !`uname -sr 2>/dev/null || echo unknown`

## Success Criteria

- 対象を種類に応じて Windows 側で開く（フォルダ=Explorer / HTML=既定ブラウザ / その他=選択表示）
- 存在しないパス・対応外環境では開かず、理由を伝えて止まる

## 開き方

`<path>` を対象に置き換えて、次の 1 ブロックをそのまま実行する。環境判定・パス正規化・存在確認・種別分岐はスクリプト内で行うため、WSL / Git Bash を呼び分ける必要はない。

```bash
target='<path>'

# 実行環境でパス変換ツールを選ぶ（wslpath / cygpath は -u/-w/-- 互換）
case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*) tool=cygpath ;;
  *) grep -qi microsoft /proc/version 2>/dev/null && tool=wslpath || { echo "open-file: 未対応の環境（WSL / Git Bash のみ）" >&2; exit 1; } ;;
esac

# 入力が Windows 形式なら Linux パスへ正規化（存在確認・種別判定は Linux パスで行う）
case "$target" in
  [A-Za-z]:[\\/]* | *\\*) target="$("$tool" -u -- "$target")" ;;
esac

[ -e "$target" ] || { echo "open-file: not found -> $target" >&2; exit 1; }
winpath="$("$tool" -w -- "$target")" || { echo "open-file: path 変換に失敗 -> $target" >&2; exit 1; }

if [ -d "$target" ]; then
  explorer.exe "$winpath"                 # フォルダを開く
elif [[ "${target,,}" == *.html || "${target,,}" == *.htm ]]; then
  explorer.exe "$winpath"                 # .html は関連付けで既定ブラウザに描画
else
  # Git Bash では先頭 / の引数が Windows パスへ変換されるのを防ぐ
  MSYS2_ARG_CONV_EXCL='*' explorer.exe /select,"$winpath"
fi
```

- 開けたら対象の絶対パスを添えて報告する
- `explorer.exe` は成功時でも非 0 を返すことがある。終了コードではなく開いたかどうかで判断する

## Safety Rules

- ファイルを実行しない。`.html` / `.htm` だけを関連付け（既定ブラウザ）で開き、それ以外のファイルは Explorer の選択表示にとどめる
- `.html` / `.htm` を開くとブラウザで JavaScript が実行される。ユーザーが明示的に指定した / このセッションで生成した HTML だけを開く。取得元が不明・未検証の HTML（ダウンロード物・外部由来・第三者作成）や、未検証の外部 URL は開かない
- 開く対象はユーザーが意図したローカルのパス / 既知のパスに限る
- 対応は Windows (Git Bash) / WSL (Ubuntu) のみ。それ以外の環境は開かず「未対応」と伝えて止まる
