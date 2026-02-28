---
name: test-coverage
description: Use when analyzing coverage gaps and adding the minimum high-value tests to close them.
disable-model-invocation: true
---

# Test Coverage

カバレッジ不足箇所を特定し、価値の高いテストを追加する。

## Workflow

1. カバレッジ付きでテスト実行する
2. レポートから不足ファイルを抽出する
3. 優先度の高い経路（失敗時の影響が大きい処理）から補完する
4. 追加テストを実行して妥当性を確認する
5. 変更前後の差分を報告する

## Priority Order

- エラーハンドリング
- 境界値
- 認可/認証
- 外部 I/O 連携

## Notes

- 目標カバレッジはプロジェクト方針を優先する
- 数値達成だけでなく、回帰防止効果を重視する
