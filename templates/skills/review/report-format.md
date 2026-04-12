# Review 出力形式

## 統合サマリー（必ず冒頭に出力）

```
## 統合レビュー結果

**実行レベル**: standard
**変更概要**: feat | コード 450行 (8ファイル) + ドキュメント 80行 (3ファイル)
**総検出件数**: CRITICAL: 0 / HIGH: 1 / MEDIUM: 3 / LOW: 2
**コミット判定**: ⚠️ BLOCKED（HIGH 以上の問題あり）
```

## 品質評価サマリー

quality-review を実行した場合は、quality-review が出力する 9 品質特性ごとの評価テーブルをそのまま含める。実行しなかった場合は `（スキップ）` を出力する。

## 各レビューの詳細

各レビューの結果をセクションごとに表示する。

```
---
### Intent Review
（スキップ / または結果を表示）
---
### Code Review
CRITICAL: 0 / HIGH: 1 / MEDIUM: 1 / LOW: 0

## HIGH: [問題タイトル] [confirmed]
**場所**: src/api/users.ts:42
**問題**: ...
**修正**: ...
---
### Quality Review
CRITICAL: 0 / HIGH: 0 / MEDIUM: 1 / LOW: 1
---
### 第三者専門家レビュー
CRITICAL: 0 / HIGH: 0 / MEDIUM: 1 / LOW: 0

#### セキュリティ専門家
CRITICAL: 0 / HIGH: 0 / MEDIUM: 1 / LOW: 0

## MEDIUM: [問題タイトル] [confirmed]
**場所**: src/api/auth.ts:28
**問題**: ...
**修正**: ...

#### シニア QA アーキテクト
CRITICAL: 0 / HIGH: 0 / MEDIUM: 0 / LOW: 0
（指摘なし）
---
### Doc Review
CRITICAL: 0 / HIGH: 0 / MEDIUM: 1 / LOW: 1
```

`standard` の例:

```md
## 統合レビュー結果

**実行レベル**: standard
**変更概要**: feat | コード 120行 (3ファイル)
**総検出件数**: CRITICAL: 0 / HIGH: 0 / MEDIUM: 1 / LOW: 1
**コミット判定**: ✅ PASS

### 品質評価サマリー
| 特性 | 評価 | 所見 |
|------|------|------|
| 機能適合性 | PASS | ... |

---
### 第三者専門家レビュー
（スキップ）
```

`quick` の例:

```md
## 統合レビュー結果

**実行レベル**: quick
**変更概要**: fix | コード 24行 (1ファイル)
**総検出件数**: CRITICAL: 0 / HIGH: 0 / MEDIUM: 0 / LOW: 1
**コミット判定**: ✅ PASS

### 品質評価サマリー
（スキップ）

---
### Intent Review
（スキップ）
---
### Code Review
CRITICAL: 0 / HIGH: 0 / MEDIUM: 0 / LOW: 1
---
### Quality Review
（スキップ）
---
### 第三者専門家レビュー
（スキップ）
```

ルーティングでスキップされたレビューは、セクション見出しと `（スキップ）` を出力する:

```
### 品質評価サマリー
（スキップ）
---
### 第三者専門家レビュー
（スキップ）
```

docs-only + `quick` では、`Code Review` ではなく `Doc Review` を実行し、他の review は `（スキップ）` とする。

指摘がゼロのセクションは件数サマリーと `（指摘なし）` を出力する:

```
### Code Review
CRITICAL: 0 / HIGH: 0 / MEDIUM: 0 / LOW: 0
（指摘なし）
```

ドキュメント更新チェックの結果がある場合は末尾に追加する:

```
---
### ドキュメント更新の必要性
- README.md: API エンドポイントの追加に伴い更新推奨
```
