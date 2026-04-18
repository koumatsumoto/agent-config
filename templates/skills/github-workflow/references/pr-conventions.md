# PR Conventions

- issue が 1 件に決まっている単一 PR では、PR description に独立行で `Closes #<num>` を入れる。末尾が推奨
- 複数 PR に分割する場合は、中間 PR を `Refs #<num>`、最終 PR を `Closes #<num>` にする
- issue 番号が曖昧なまま close 記法を入れない
- close 記法は commit message ではなく PR description に置く
