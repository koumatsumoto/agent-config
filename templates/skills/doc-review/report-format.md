# Document Review 出力形式

## サマリー（必ず冒頭に出力）

```
## レビュー結果

**ドキュメントタイプ**: README (高重要度) | 変更行数: 80行 | ファイル数: 3
**検出件数**: CRITICAL: 0 / HIGH: 1 / MEDIUM: 2 / LOW: 1
**コミット判定**: ⚠️ BLOCKED（HIGH 以上の問題あり）
```

## 問題報告

問題ごとに以下の形式で報告する。確信度（`confirmed` = 確認済み / `suspected` = 疑い）を付与する。

```
## HIGH: API エンドポイントのパスが実装と不一致 [confirmed]

**場所**: docs/api.md:42
**問題**: `/api/v2/users` と記載されているが、実装は `/api/v1/users` のまま。
**修正**: 実装に合わせて `/api/v1/users` に修正する。
```
