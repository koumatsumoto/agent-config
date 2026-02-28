---
name: refactor-clean
description: Use when identifying and removing dead code safely with test-backed verification.
disable-model-invocation: true
---

# Refactor Clean

デッドコード候補を特定し、テストで安全性を確認しながら削除する。

## Workflow

1. 解析ツールを実行する（`knip`, `depcheck`, `ts-prune`）
2. 候補を `SAFE/CAUTION/DANGER` に分類する
3. `SAFE` から段階的に削除する
4. 変更前後でテストを実行する
5. 失敗時は原因を特定し、削除方針を見直す

## Safety Rules

- テスト未実行で削除しない
- `DANGER` は削除前にユーザー確認を取る
- 影響範囲が不明な候補は保留する
