---
name: km:open-file
description: ローカルのファイル / フォルダを Windows 側で開く（Windows / WSL Ubuntu のみ）。"ブラウザで開いて" / "エクスプローラで開いて" / "Windows で開いて" のときに使う。
argument-hint: "[path]"
---

# Open File

ローカルのファイルやフォルダを Windows 側で開く。対応環境は **Windows** と **WSL (Ubuntu)** のみ。

開く手段は `explorer.exe`（WSL）/ `start`・`explorer`（Windows）に統一し、対象の種類で扱いを分ける。これにより、開いたファイルがプログラムとして実行されることはない。

- **フォルダ**: Explorer で開く
- **`.html` / `.htm`**: 拡張子の関連付けで既定ブラウザに描画する
- **その他のファイル**: 実行せず、Explorer で選択表示（reveal）するだけにとどめる

## Context

- Platform: !`uname -sr 2>/dev/null || echo unknown`
- WSL?: !`grep -qi microsoft /proc/version 2>/dev/null && echo yes || echo no`

## Success Criteria

- 対象を種類に応じて Windows 側で開く（フォルダ=Explorer / HTML=既定ブラウザ / その他=選択表示）
- 存在しないパス・対応外環境では開かず、理由を伝えて止まる

## Workflow

1. 対象を決める（`$ARGUMENTS` のパス、無ければ直近に生成・言及したファイル）
2. 対象が**存在する**ことを確認する。無ければ開かずに知らせる
3. 環境を判定する（WSL / Windows / それ以外）
4. 環境に応じて開く（下記）。開けたら絶対パスを添えて報告する

## 開き方

### WSL (Ubuntu)

Windows パスへ変換し、種類に応じて `explorer.exe` に渡す。

```bash
target="<target>"
[ -e "$target" ] || { echo "open-file: not found -> $target" >&2; exit 1; }
winpath="$(wslpath -w -- "$target")" || { echo "open-file: path 変換に失敗 -> $target" >&2; exit 1; }
if [ -d "$target" ]; then
  explorer.exe "$winpath"                 # フォルダを開く
elif [[ "${target,,}" == *.html || "${target,,}" == *.htm ]]; then
  explorer.exe "$winpath"                 # .html は関連付けで既定ブラウザに描画
else
  explorer.exe /select,"$winpath"         # その他は実行せず Explorer で選択表示
fi
```

- `-- ` で `target` をオプションと解釈させない（先頭 `-` のファイル名対策）
- `winpath="$(...)" || { … }` で変換失敗を終了コードで検知する。関数内で `local` と同じ行に代入すると終了コードが隠れるため、その場合は宣言と代入を分ける
- `explorer.exe` は成功時でも非 0 を返すことがある。終了コードではなく開いたかどうかで判断する

### Windows (Git Bash / MSYS)

```bash
# フォルダ
explorer "<dir>"
# .html / .htm（既定ブラウザ）
start "" "<file>"
# その他のファイル（実行せず選択表示）
explorer /select,"<winpath>"
```

- 渡す前に対象が存在することを確認する（WSL と同じ）
- パスが MSYS 形式（`/c/...`）なら `cygpath -w -- "<path>"` で Windows パスへ変換してから渡す（`-- ` で先頭 `-` のファイル名対策）

## Safety Rules

- ファイルを実行しない。`.html` / `.htm` だけを関連付け（既定ブラウザ）で開き、それ以外のファイルは Explorer の選択表示にとどめる
- `.html` / `.htm` を開くとブラウザで JavaScript が実行される。ユーザーが明示的に指定した / このセッションで生成した HTML だけを開く。取得元が不明・未検証の HTML（ダウンロード物・外部由来・第三者作成）や、未検証の外部 URL は開かない
- 開く対象はユーザーが意図したローカルのパス / 既知のパスに限る
- ファイルが存在しない場合・パス変換に失敗した場合は開かずに知らせる
- 対応は Windows / WSL (Ubuntu) のみ。素の Linux / macOS など他環境は開かず「未対応」と伝えて止まる
