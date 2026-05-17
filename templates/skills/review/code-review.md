# Phase 2: Code Review (generalist)

km:review orchestrator の **Phase 2**。**コードレベル (関数・モジュール・システム境界) 全部** の generalist code review を行う。Phase 3 architect 専門家との住み分けは `references/scope-alignment.md` に集約。

> 本ファイル内の "Step N" は workflow 番号で、orchestrator (SKILL.md) の "Phase N" とは別の番号空間。

## Step 1: 変更把握

orchestrator から「変更ファイル一覧 + diff 内容 + 変更構成 + 実行 level」を受け取る。`docs-only` なら本ファイルは起動されない。

変更構成 + コミットメッセージのプレフィックスからレビュー深度を決める:

| 変更内容 | 設計・実装の深度 | 規約・可読性の深度 |
|---|---|---|
| `feat` (新機能 / 新規ファイル中心) | Full | Full |
| `code+docs` / `mixed` (振る舞い変更を含む) | Full | Full |
| `fix` / `refactor` (`code-only` の既存実装修正) | Focused | Focused |
| `test-or-config-or-chore-only` | Skip | Quick |

`quick` レベルでは「規約・可読性」を Quick に降格、`thorough` レベルでは上記どおり、`standard` は中間。読み込み範囲は `quick` = 変更ファイル中心、`standard` = 必要な近傍 context まで、`thorough` = 関連モジュールまで広げる。

新規ファイル中心の `feat` 変更では「既存パターンとの整合性」も確認する: 類似 endpoint / module の既存実装を必要なら 1-3 ファイル Read して、設計判断 (パターン選択、責務分割) が repo の他箇所と揃っているか確認する。

## Step 2: 設計・実装 (3 層)

関数 (単体) → モジュール (結合) → システム境界 (総合) の 3 層で段階的に確認する。**ここでは「現在の diff で破綻するか否か」に限定する**。将来の波及・進化方向との整合は Phase 3 architect の責務 (`references/scope-alignment.md` 参照)。

### 2a. 関数 / メソッドレベル

個々の関数・メソッドの正しさと安全性を確認する:

- 型・null 安全性、エッジケース (空配列、ゼロ、最大値、undefined)
- エラーパスの網羅 (例外の握り潰し、fail-open パターン)
- 副作用の最小化 (引数や共有データのイミュータブル原則)
- off-by-one エラー (`<` vs `<=`、0-indexed vs 1-indexed)

見落としやすいパターン:

- サイレント型変換 (暗黙比較、truthy/falsy の誤用)
- ミュータブルオブジェクトのデフォルト引数・共有参照
- 未検証の外部入力がロジックに直接到達

### 2b. モジュール / ファイルレベル

モジュール間の結合と責務分離を確認する:

- 責務の分離 (単一責任原則)、依存方向 (具象→抽象)
- 公開インターフェースの最小化 (内部型のリーク防止)
- モジュール間の結合度と凝集度のバランス

見落としやすいパターン:

- 循環依存の導入
- import 時の副作用や初期化順序への暗黙依存
- 内部型や内部事情の公開 API へのリーク

### 2c. システム / アーキテクチャレベル

データフロー全体と信頼境界を確認する:

- 信頼境界を跨ぐ入力検証 (外部入力がバリデーションなしに内部レイヤーまで到達していないか)
- レイヤー境界の遵守 (UI→DB 直接アクセス、ドメイン層の外部 API 依存)
- データフロー全体の型安全性と変換の整合性
- 変更の波及範囲が意図した範囲に収まっているか

見落としやすいパターン:

- 分散トランザクションや複数サービス間の整合性に関する誤った仮定
- 非同期処理やイベント駆動でのデータ整合性の欠如
- 複数システム間の障害伝播経路の見落とし

## Step 3: 規約・可読性

以下に限定して確認する:

- `AGENTS.md` / `CLAUDE.md` / repo ルールに書かれた実質的な制約 (**コード規約に限定**。設計方針 / アーキ判断記述は Phase 3 architect の責務)
- システム設計・アーキテクチャへの準拠
- 変更対象ファイル内の既存コメントや TODO の重要な指示
- 意図が伝わる命名、過度なネスト、不要な複雑性

純粋な好み、機械的に直せるスタイル、未変更行への一般論は優先しない。

## Step 4: 偽陽性フィルタリング

以下は原則除外する:

- 今回の差分で入っていない既存問題
- linter、型チェッカー、formatter が拾うべきだけの問題
- 合意済みの設計判断
- 未変更行だけに対する指摘
- シニアレビューとして弱い、些末な指摘

## 判定

- `CRITICAL`: 即時悪用可能な欠陥
- `HIGH`: 明確なバグ、仕様回帰、危険な入力検証不足
- `MEDIUM`: 設計不整合、保守性低下、テスト不足
- `LOW`: 小さな改善

`CRITICAL` または `HIGH` があれば orchestrator の進行ゲートにより Phase 3 (experts) の起動が阻まれ、Phase 5 で BLOCKED 報告して終了する。確信度ラベル ([confirmed]/[likely]/[possible]) は Phase 3 experts の規約であり本ステップでは任意添付可。

## 出力フォーマット

```
### Phase 2: Code Review (generalist)
CRITICAL: 0 / HIGH: 1 / MEDIUM: 1 / LOW: 0
**Doc impact hints**: API endpoint / CLI flag / config schema / none （Phase 4 need-check の起点）

## HIGH: [問題タイトル]
**場所**: src/api/users.ts:42
**問題**: 何が問題か (2-4 文で具体的に)
**修正**: どう直すべきか (具体的な対応)
**根拠**: diff / repo ルール / 設計方針への参照

## MEDIUM: [問題タイトル]
**場所**: ...
**問題**: ...
**修正**: ...
```

`Doc impact hints` 行は diff が以下のいずれかに該当する場合のみ出力する: パブリック API endpoint の追加 / 削除 / レスポンス変更、CLI flag の追加 / 削除 / 意味変更、config / 環境変数 / DB スキーマの変更。該当なしなら `none` または行ごと省略。Phase 4 (need-check) はこの hints から該当 doc を探索する。

指摘ゼロ:

```
### Phase 2: Code Review (generalist)
CRITICAL: 0 / HIGH: 0 / MEDIUM: 0 / LOW: 0
（指摘なし）
```
