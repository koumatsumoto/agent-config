---
name: tdd
description: Use when implementing features or fixes with a test-first workflow (RED -> GREEN -> REFACTOR).
argument-hint: "[task-description]"
---

# TDD

テスト先行で仕様を固定し、最小実装で前進するためのスキル。

## Use When

- 新機能実装
- バグ修正（再現テストを先に追加）
- 重要ロジックの改修

## Cycle

1. `RED`: 失敗するテストを書く
2. `GREEN`: テストを通す最小実装を入れる
3. `REFACTOR`: 挙動を保ったまま改善する
4. 次のケースへ繰り返す

## Coverage Policy

- 目標値はプロジェクト設定に従う
- 未設定なら全体 80% を初期目安とする
- 認証/課金/セキュリティ境界は 100% カバレッジを目標とする

## Anti-Patterns

- 実装を先に書く
- 失敗テストを確認せず進める
- 実装詳細に過度依存したテストを書く
