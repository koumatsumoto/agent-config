---
name: km-open-file
description: ローカルのファイル・フォルダをWindows側で開く。「ブラウザで開いて」「エクスプローラで開いて」などの依頼で使う。Windows / WSL Ubuntuのみ対応。
argument-hint: "[パス]"
---

# Open File

Windows（Git Bash）またはWSL（Ubuntu）から、指定したローカルのファイル・フォルダをWindows側で開く。

- フォルダ：Explorerで開く
- HTML（`.html` / `.htm`）：既定ブラウザへ渡す
- その他のファイル：実行せずExplorerで選択表示する

`<skill-directory>`はこの`SKILL.md`のあるdirectory。

```text
bash "<skill-directory>/scripts/open-file.sh" "<path>"
```

相対pathは呼び出し時のworking directory基準。起動要求を送信したことと対象pathを報告する。GUI表示完了は確認しない。helperが失敗した場合は理由を伝える。
