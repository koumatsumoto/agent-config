---
name: build-fix
description: Use when TypeScript or build errors must be resolved safely, one error at a time.
---

# Build Fix

## Use When

- `npm run build` / `pnpm build` が失敗する
- TypeScript エラーを段階的に潰したい

## Workflow

1. ビルドを実行して最初のエラーを特定する
2. 該当箇所の前後文脈を確認して原因を説明する
3. 最小修正を適用する
4. ビルドを再実行して同エラー解消を確認する
5. 次のエラーへ進む

## Safety Rules

- 一度に 1 エラーだけ修正する
- 修正で新規エラーが増えたら原因を説明して停止する
- 同一エラーが 3 回継続する場合は方針を見直して確認する

## Output

- 修正済みエラー
- 未解決エラー
- 新規発生エラー
