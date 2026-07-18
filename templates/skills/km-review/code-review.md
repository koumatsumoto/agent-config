# Phase 2: Code Review (generalist)

km-review orchestrator の **Phase 2**。コードレベル (関数・モジュール・システム境界) 全体を対象とする generalist code review。Phase 3 architect との住み分けは `references/scope-alignment.md`。

> 本ファイルの "Step N" は workflow 番号で、orchestrator (SKILL.md) の "Phase N" とは別。

## Step 1: 変更把握

orchestrator から「変更ファイル一覧 + diff + 変更構成 + 実行 level」を受け取る (`docs-only` では起動しない)。変更構成と diff の signal で深度を決める (下表は `standard` 基準):

| 変更の性質 | 設計・実装 | 規約・可読性 |
|---|---|---|
| 新規ファイル中心 / 公開挙動を変える (`code+docs` / `mixed` / 振る舞いを変える `code-only`) | Full | Full |
| 既存実装の局所修正 (振る舞い変更が限定的) | Focused | Focused |
| `test-or-config-or-chore-only` | Skip | Quick |

`thorough` は読み込みを関連モジュールまで広げ、`quick` は規約・可読性を Quick に下げ変更ファイル中心に絞る。コミット / PR では Conventional 接頭辞も補助に使える (`refactor:` 振る舞い不変の検証 / `fix:` 再発防止テスト / `perf:` 性能特性)。新規ファイル中心では類似実装を 1-3 ファイル読み、設計判断が repo と揃うか確認する。

対象が **挙動資産** (skill / rule / prompt 定義。判定は SKILL.md Phase 1) に分類された実行では、orchestrator の指示で `references/prompt-asset-lens.md` を読み、そこに定義された写像で汎用レンズを prompt 資産の意味へ当てる (通常の code diff では読まない)。

## Step 2: 設計・実装 (3 層)

関数 → モジュール → システム境界 の 3 層で確認する。**「現在の diff で破綻するか」に限定**し、将来の波及・進化方向は Phase 3 architect に委ねる (`references/scope-alignment.md`)。

- **関数**: 型・null 安全性、エッジケース (空 / ゼロ / 最大値 / undefined)、エラーパスの網羅 (握り潰し・fail-open)、副作用、off-by-one。エッジケースは値の **受動的な列挙で止めず**、**変更が暗黙に置く前提・不変条件 (入力の形・呼び出し順・状態・並行度) を 1 つ特定し、それを崩す入力・経路を能動的に構築して破綻を試す**。
- **モジュール**: 責務分離・依存方向 (具象→抽象)、公開 interface の最小化 (内部型リーク)、循環依存・初期化順序への依存。
- **システム境界**: 信頼境界を跨ぐ入力検証、レイヤー境界の遵守、データフローの型整合、変更波及が意図内か。**非同期・分散・複数サービス間の整合性の誤った仮定**は特に見落としやすい。
- **diff 外照合 (diff 内で正しいと仮定せず、権威ある定義元・sibling・呼び出し元を開いて照合する)** — 次の 2 サブプローブを当てる。本項が継承の canonical 定義 (他ファイルはここを一方向に参照する)。
  - **不変条件の継承 (無条件・全レベル)**: 新設・分岐した経路 (新しい関数・エンドポイント・設定分岐・手順) が、既存の同種経路が通す gate・検証・権限・エラー処理を継承しているかを **経路列挙** で確認する。継承漏れ (新経路が既存の安全確認を素通り) は頻出の欠陥クラス (新エンドポイントが既存の認可 middleware を継承しない等)。**レベル・変更構成・Phase 3 起動有無によらず無条件** — `quick` では本サブプローブのみ、`test-or-config-or-chore-only` の Skip (Step 1 深度表) からも本サブプローブのみ除外する (CI 権限・デプロイ等の config 変更こそ継承漏れが刺さる)。
  - **値・契約の drift**: diff が変える識別子・値・契約 (path・設定キー・定数・enum・スキーマ列・エラーコード・公開契約) を、権威ある定義元・複製 / 連動箇所 (config・スキーマ・呼び出し元・sibling 実装・doc・テスト) と照合し、片側だけ更新して stale になる drift を拾う。

## Step 3: 規約・可読性

`AGENTS.md` / `CLAUDE.md` / repo ルールの実質的制約 (コード規約に限定。設計方針・アーキ判断は Phase 3 architect)、変更ファイル内の既存コメント / TODO、意図が伝わる命名・不要な複雑性。純粋な好み・機械的スタイル・未変更行への一般論は出さない。

## Step 4: 偽陽性フィルタ (出さない)

今回の diff で導入していない既存問題 / linter・型チェッカー・formatter が拾うもの / 合意済み設計判断 / 未変更行への指摘 / シニアレビューとして些末なもの。

## 判定

重大度は `experts/report-format.md` の 4 段階に従う (「今すぐ直す重さ」)。Phase 2 は code-level の正しさに範囲を絞る (長期保守を直撃する設計欠陥は architect、脅威は security が同尺度で別途評価)。CRITICAL/HIGH でも早期停止せず Phase 4 統合で BLOCKED 判定する。確信度ラベルは Phase 3 規約で、本 Phase は任意添付可。

## 出力フォーマット

```
### Phase 2: Code Review (generalist)
CRITICAL: 0 / HIGH: 1 / MEDIUM: 1 / LOW: 0

## HIGH: [問題タイトル]
**場所**: src/api/users.ts:42
**問題**: 何が問題か (具体的に)
**修正**: どう直すか (具体的に)
**根拠**: diff / repo ルール / 設計方針への参照
```

指摘ゼロ:

```
### Phase 2: Code Review (generalist)
CRITICAL: 0 / HIGH: 0 / MEDIUM: 0 / LOW: 0
（指摘なし）
```
