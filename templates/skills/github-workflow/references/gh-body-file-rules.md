# gh Body File Rules

`gh issue create/edit` と `gh pr create/edit` の本文は、必ず `--body-file` で渡す。
第一選択は `--body-file - <<'EOF'` で stdin から直接流し込む方法とする。

## 禁止

- `--body "..."`
- 非クォート heredoc: `<<EOF`

## 推奨

- クォート heredoc: `<<'EOF'` + `--body-file -`

```bash
gh issue create --title "..." --body-file - <<'EOF'
## Context

`backtick` や `$()` を含んでも展開されない。
EOF
```

## 防ぎたい事故

- backtick 展開
- `$()` 展開
- 改行やコードブロックの崩れ
