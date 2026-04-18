# gh Body File Rules

`gh issue create/edit` と `gh pr create/edit` の本文は、必ず `--body-file` で渡す。

## 禁止

- `--body "..."`
- 非クォート heredoc: `<<EOF`

## 許容

- 一時ファイル + `trap 'rm -f "$f"' EXIT` + `--body-file "$f"`
- クォート heredoc: `<<'EOF'` + `--body-file -`

## 防ぎたい事故

- backtick 展開
- `$()` 展開
- 改行やコードブロックの崩れ
