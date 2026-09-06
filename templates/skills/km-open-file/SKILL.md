---
name: km-open-file
description: ローカルのファイル・フォルダをWindows側で開く。「ブラウザで開いて」「エクスプローラで開いて」などの依頼で使う。Windows / WSL Ubuntuのみ対応。
argument-hint: "[パス]"
---

# Open File

Windows（Git Bash）とWSL（Ubuntu）で使う。Linux形式・Windows形式のパスを受け付け、`wslview`などの追加パッケージは前提にしない。
フォルダはExplorer、HTML（`.html` / `.htm`）は既定ブラウザで開き、その他はExplorerで選択表示する。HTML以外は直接実行しない。

## 実行

1. ユーザーが意図したローカルのパスまたは既知のパスであることを確認する。
2. HTMLは作成元・外部資源・埋め込みスクリプト・秘密情報を確認し、ユーザーが明示したものか、このセッションで生成したものだけを開く。ブラウザでスクリプトが動く可能性を考慮し、信頼判断をhelperに委ねない。
3. 読み込んだ`SKILL.md`の実在directoryからhelperを解決する。そこへ`cd`せず、対象を一つの引数で渡す。パスをshell文字列へ埋め込まない。

```bash
bash "<skill-directory>/scripts/open-file.sh" "<path>"
```

相対パスの基準は呼び出し時のworking directory。
存在しないパス・対応外環境では開かず、helperの失敗時は理由を報告して停止する。
成功時は起動要求の送信と対象の絶対パスを報告する。GUI表示完了は保証しない。
