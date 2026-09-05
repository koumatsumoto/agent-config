---
name: km-open-file
description: ローカルのファイル / フォルダを Windows 側で開く（Windows / WSL Ubuntu のみ）。"ブラウザで開いて" / "エクスプローラで開いて" のときに使う。
argument-hint: "[パス]"
---

# Open File

ローカルのファイルやフォルダを Windows 側で開く。対応環境は **Windows (Git Bash)** と **WSL (Ubuntu)** のみ。追加パッケージ（`wslview` 等）は前提にしない。

入力パスは Linux 形式（`/home/...`, `./x`）でも Windows 形式（`C:\...`, `C:/...`, `\\...`）でも受け付ける。

## Success Criteria

- 対象種別に応じたWindows側の起動要求を送信する（フォルダ=Explorer / HTML=既定ブラウザ / その他=選択表示）
- 存在しないパス・対応外環境では開かず、理由を伝えて止まる

## Workflow

1. 対象がユーザーの意図したローカルのパス / 既知のパスであることを確認する
2. HTMLの場合は、作成元、外部資源、埋め込みスクリプト、秘密情報の有無を確認し、ユーザーが明示したHTMLまたはこのsessionで生成したHTMLだけを開く
3. 読み込んだこの `SKILL.md` の実在directoryを基準に `scripts/open-file.sh` を解決し、skill directoryへ `cd` せず次の形で呼ぶ。対象pathはshell文字列へ埋め込まず、一つの引数として渡す

```bash
bash "<skill-directory>/scripts/open-file.sh" "<path>"
```

相対パスは呼び出し時のworking directoryを基準にする。

- helperが成功したら、Windows側へ起動要求をdispatchできたものとして対象の絶対pathを報告する
- helperが失敗したら、その理由を報告して停止する

成功は起動要求の送信を意味し、GUI表示完了を保証しない。

## Safety Rules

- HTML（`.html` / `.htm`）はブラウザでスクリプトが動く可能性がある。HTML以外のファイルは直接実行しない
- HTMLの信頼判断とユーザー意図の確認をhelperへ委ねない
