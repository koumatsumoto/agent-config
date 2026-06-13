# Review 統合出力フォーマット

km:review Phase 4 (統合) が main コンテキストで生成する統合レポート形式。

## 統合サマリー (必ず冒頭に出力)

```
## 統合レビュー結果

**実行レベル**: standard
**対象スコープ**: uncommitted | pr:123 | a1b2c3d..HEAD | --repo src/api 等
**変更概要**: feat | コード 450行 (8ファイル) + ドキュメント 80行 (3ファイル)
**総検出件数**: CRITICAL: 0 / HIGH: 1 / MEDIUM: 3 / LOW: 2
**コミット判定**: ⚠️ BLOCKED（HIGH 以上の問題あり）
```

## 各 Phase の詳細

各 Phase の結果をセクションごとに表示する。スキップした Phase は見出し + `（スキップ）` を出力 (省略しない)。Phase 3 は中央 dedup 後の所見を表示する。

```
---
### Phase 2: Code Review (generalist)
CRITICAL: 0 / HIGH: 1 / MEDIUM: 1 / LOW: 0

## HIGH: [問題タイトル] [confirmed]
**場所**: src/api/users.ts:42
**問題**: ...
**修正**: ...
---
### Phase 3: 第三者レビュー
CRITICAL: 0 / HIGH: 0 / MEDIUM: 1 / LOW: 0

#### システムアーキテクト
CRITICAL: 0 / HIGH: 0 / MEDIUM: 1 / LOW: 0

## MEDIUM: [問題タイトル] [confirmed]
**場所**: src/api/auth.ts:28
**問題**: ...
**修正**: ...

#### セキュリティ専門家
CRITICAL: 0 / HIGH: 0 / MEDIUM: 0 / LOW: 0
（指摘なし）

#### 敵対レビュア
CRITICAL: 0 / HIGH: 0 / MEDIUM: 0 / LOW: 0
（指摘なし）
---
### Phase 5: Doc Review
CRITICAL: 0 / HIGH: 0 / MEDIUM: 1 / LOW: 1
```

スキップ / defer の表記例: `### Phase 3: 第三者レビュー\n（スキップ - standard レベルのため）`。doc-review は `### Phase 5: Doc Review\n（defer - コード解消後に実施）` / `（スキップ - test/config/chore のため）` 等。

## 共通ルール

1. 統合サマリーに実行レベル・対象スコープ・変更概要・総検出件数・コミット判定を含める
2. 全 Phase の重大度ごとの件数を合算する。Phase 3 は中央 dedup 後の件数を使う
3. 同一ファイル・近接行の類似指摘の集約 (dedup) は Phase 4 統合が一括で行う (判定基準は `experts/report-format.md` の「中央 dedup ルール」)
4. コードレビュー層 (Phase 2 + Phase 3) に `CRITICAL` または `HIGH` が残れば `BLOCKED`。doc-review (Phase 5) が CRITICAL/HIGH を出した場合も `BLOCKED` に更新する
5. スキップ / defer された Phase は見出しと理由を出力。セクション自体を省略しない
6. Phase が結果を返さなかった場合は `（実行失敗）` として記録し失敗理由を含める。実行失敗 Phase が 1 つでもあれば全体判定は **安全側に倒して BLOCKED** とする
7. 指摘がゼロの Phase は件数サマリーと `（指摘なし）` を出力
8. レビュー対象がなく Phase 1 で終了した場合は `**コミット判定**: ⏭ NOOP（対象なし）` の単行を出力するだけで Phase 2 以降のセクションは省略してよい
