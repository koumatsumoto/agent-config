---
name: km-open-file
description: ローカルのファイル / フォルダを Windows 側で開く（Windows / WSL Ubuntu のみ）。"ブラウザで開いて" / "エクスプローラで開いて" のときに使う。
argument-hint: "[パス]"
---

# Open File

ローカルのファイルやフォルダを Windows 側で開く。対応環境は **Windows (Git Bash)** と **WSL (Ubuntu)** のみ。追加パッケージ（`wslview` 等）は前提にしない。

開く手段は`explorer.exe`に統一し、対象の種類で扱いを分ける。HTML以外のファイルは直接実行しない。HTMLはブラウザ上のスクリプトが動く可能性を確認してから開く。

- **フォルダ**: Explorer で開く
- **`.html` / `.htm`**: 拡張子の関連付けで既定ブラウザに描画する
- **その他のファイル**: 実行せず、Explorer で選択表示（reveal）するだけにとどめる

入力パスは Linux 形式（`/home/...`, `./x`）でも Windows 形式（`C:\...`, `C:/...`, `\\...`）でも受け付ける。

## Context

- Platform: !`uname -sr 2>/dev/null || echo unknown`

## Success Criteria

- 対象を種類に応じて Windows 側で開く（フォルダ=Explorer / HTML=既定ブラウザ / その他=選択表示）
- 存在しないパス・対応外環境では開かず、理由を伝えて止まる

## Workflow

1. 対象がユーザーの意図したローカルのパス / 既知のパスであることを確認する
2. HTMLの場合は、作成元、外部資源、埋め込みスクリプト、秘密情報の有無を確認し、ユーザーが明示したHTMLまたはこのsessionで生成したHTMLだけを開く
3. 読み込んだこの `SKILL.md` の実在directoryを基準に `scripts/open-file.sh` を解決し、skill directoryへ `cd` せず次の形で呼ぶ。対象pathはshell文字列へ埋め込まず、一つの引数として渡す

```bash
bash "<skill-directory>/scripts/open-file.sh" "<path>"
```

helperはplatform判定、path正規化、存在確認、対象種別に応じたdispatchを担う。relative pathはhelperを呼んだworking directory基準で解釈される。

- helperが成功したら、Windows側へ起動要求をdispatchできたものとして対象の絶対pathを報告する
- helperが失敗したら、その理由を報告する
- `explorer.exe` は表示に成功しても非0を返すことがあるため、helperは前提検証後に起動要求をdispatchできたことを成功とする

## Safety Rules

- HTML以外のファイルは直接実行しない
- HTMLの信頼判断とユーザー意図の確認をhelperへ委ねない
- 対応は Windows (Git Bash) / WSL (Ubuntu) のみ。それ以外の環境は開かず「未対応」と伝えて止まる
