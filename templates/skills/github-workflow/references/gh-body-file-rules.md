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

## 代替

- 一時ファイル + `--body-file "$f"`

一時ファイル方式は、同じ本文を複数回再利用する必要がある場合や、stdin 流し込みが扱いにくい場合だけ使う。`trap` は使うなら最小限にし、複雑な quoting を増やさない。

## 防ぎたい事故

- backtick 展開
- `$()` 展開
- 改行やコードブロックの崩れ
- 一時ファイル cleanup まわりの複雑な shell quoting
