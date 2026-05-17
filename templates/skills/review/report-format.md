# Review 統合出力フォーマット

km:review Phase 5 の統合レポート形式。

## 統合サマリー (必ず冒頭に出力)

```
## 統合レビュー結果

**実行レベル**: standard
**対象スコープ**: uncommitted | pr:123 | a1b2c3d..HEAD | --repo src/api 等
**変更概要**: feat | コード 450行 (8ファイル) + ドキュメント 80行 (3ファイル)
**総検出件数**: CRITICAL: 0 / HIGH: 1 / MEDIUM: 3 / LOW: 2
**コミット判定**: ⚠️ BLOCKED（HIGH 以上の問題あり）
```

`--skip-gating` 指定時は判定行に `(--skip-gating 指定)` を付記する。

## 各 Phase の詳細

各 Phase の結果をセクションごとに表示する。スキップした Phase は見出し + `（スキップ）` を出力 (省略しない)。

```
---
### Phase 2: Code Review (generalist)
CRITICAL: 0 / HIGH: 1 / MEDIUM: 1 / LOW: 0

## HIGH: [問題タイトル] [confirmed]
**場所**: src/api/users.ts:42
**問題**: ...
**修正**: ...
---
### Phase 3: 第三者専門家レビュー
CRITICAL: 0 / HIGH: 0 / MEDIUM: 1 / LOW: 0

#### システムアーキテクト
CRITICAL: 0 / HIGH: 0 / MEDIUM: 1 / LOW: 0

## MEDIUM: [問題タイトル] [confirmed]
**場所**: src/api/auth.ts:28
**問題**: ...
**修正**: ...

#### QA 専門家
CRITICAL: 0 / HIGH: 0 / MEDIUM: 0 / LOW: 0
（指摘なし）

#### セキュリティ専門家
CRITICAL: 0 / HIGH: 0 / MEDIUM: 0 / LOW: 0
（指摘なし）
---
### Phase 4: Doc Review
CRITICAL: 0 / HIGH: 0 / MEDIUM: 1 / LOW: 1
```

## レベル別の例

### `standard` の例

```md
## 統合レビュー結果

**実行レベル**: standard
**対象スコープ**: uncommitted
**変更概要**: feat | コード 120行 (3ファイル)
**総検出件数**: CRITICAL: 0 / HIGH: 0 / MEDIUM: 1 / LOW: 1
**コミット判定**: ✅ PASS

---
### Phase 2: Code Review (generalist)
CRITICAL: 0 / HIGH: 0 / MEDIUM: 1 / LOW: 1
---
### Phase 3: 第三者専門家レビュー
（スキップ - standard レベルのため）
---
### Phase 4: Doc Review
（need-check モード）
- README.md: API エンドポイントの追加に伴い更新推奨
```

### `quick` の例 (code-only)

```md
## 統合レビュー結果

**実行レベル**: quick
**対象スコープ**: uncommitted
**変更概要**: fix | コード 24行 (1ファイル)
**総検出件数**: CRITICAL: 0 / HIGH: 0 / MEDIUM: 0 / LOW: 1
**コミット判定**: ✅ PASS

---
### Phase 2: Code Review (generalist)
CRITICAL: 0 / HIGH: 0 / MEDIUM: 0 / LOW: 1
---
### Phase 3: 第三者専門家レビュー
（スキップ - quick レベルのため）
---
### Phase 4: Doc Review
（need-check モード - 更新必要性なし）
```

### docs-only の例

```md
## 統合レビュー結果

**実行レベル**: standard
**対象スコープ**: uncommitted
**変更概要**: docs | ドキュメント 80行 (2ファイル)
**総検出件数**: CRITICAL: 0 / HIGH: 0 / MEDIUM: 1 / LOW: 0
**コミット判定**: ✅ PASS

---
### Phase 2: Code Review (generalist)
（スキップ - docs-only のため）
---
### Phase 3: 第三者専門家レビュー
（スキップ - docs-only のため）
---
### Phase 4: Doc Review
CRITICAL: 0 / HIGH: 0 / MEDIUM: 1 / LOW: 0
```

### `thorough` + BLOCKED の例

```md
## 統合レビュー結果

**実行レベル**: thorough
**対象スコープ**: pr:123
**変更概要**: feat | コード 450行 (8ファイル) + ドキュメント 80行 (3ファイル)
**総検出件数**: CRITICAL: 0 / HIGH: 2 / MEDIUM: 4 / LOW: 1
**コミット判定**: ⚠️ BLOCKED（HIGH 以上の問題あり）

---
### Phase 2: Code Review (generalist)
CRITICAL: 0 / HIGH: 1 / MEDIUM: 2 / LOW: 0
...
---
### Phase 3: 第三者専門家レビュー
CRITICAL: 0 / HIGH: 1 / MEDIUM: 2 / LOW: 1

#### システムアーキテクト
CRITICAL: 0 / HIGH: 1 / MEDIUM: 1 / LOW: 0
...

#### QA 専門家
CRITICAL: 0 / HIGH: 0 / MEDIUM: 1 / LOW: 1
...

#### セキュリティ専門家
CRITICAL: 0 / HIGH: 0 / MEDIUM: 0 / LOW: 0
（指摘なし）
---
### Phase 4: Doc Review
CRITICAL: 0 / HIGH: 0 / MEDIUM: 0 / LOW: 0
（指摘なし）
```

## 共通ルール

1. 統合サマリーに実行レベル・対象スコープ・変更概要・総検出件数・コミット判定を含める
2. 全 Phase の重大度ごとの件数を合算する
3. 同一ファイル・近接行の類似指摘は重複の可能性を注記する
4. いずれかの Phase で `CRITICAL` または `HIGH` があれば `BLOCKED` とする (`--skip-gating` 指定時もレポート上は BLOCKED を表示するが、Phase 進行は完了している)
5. スキップされた Phase は見出しと `（スキップ）` を出力。セクション自体を省略しない
6. Phase が結果を返さなかった場合は、該当 Phase を `（実行失敗）` として記録し、失敗理由を含める
7. 指摘がゼロの Phase は件数サマリーと `（指摘なし）` を出力

## ループ上限超過時のユーザ提示

Phase 2 / 3 / 4 でループ上限 (5 / 3 / 3 周) を超過した場合、orchestrator は以下の形式でユーザに判断を仰ぐ:

```md
## ループ上限超過 - ユーザ判断が必要です

Phase <N> で最大ループ回数を超過しても CRITICAL/HIGH 指摘が残っています。

### 現在の指摘
- HIGH: ...
- ...

### 判断
- **続行**: 残指摘付きで Phase <N+1> へ進む (Phase 5 で BLOCKED を表示)
- **中止**: ここで終了し、修正後に再度 `/km:review` を実行する

どちらにしますか?
```
