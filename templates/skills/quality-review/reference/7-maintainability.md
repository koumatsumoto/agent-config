# 保守性 (Maintainability)

ISO/IEC 25010:2023 の保守性に関するリファレンス。可読性だけでなく、境界検証、契約テスト、故障解析可能性まで含めて「後から安全に変えられるか」を見る。

## 副特性ごとのアンチパターン + diff シグナル

### モジュール性 / 再利用性

- 同一ロジックのコピペ、過大関数、複数関心の混在
- 上位モジュールが下位実装詳細へ依存している
- 標準ライブラリや既存ヘルパーで代替可能な自前実装

### 解析性 / 修正性

- 意図を表現しない命名、深いネスト、マジックナンバー、暗黙的依存
- 設定とロジックの密結合、依存注入なしの直接インスタンス化
- 変更箇所を追っても、ログ・メトリクス・トレースから障害箇所を絞れない

### 試験性

- diff の変更を通らない形式的テスト
- 実装詳細依存のアサーション、曖昧なアサーション
- 実行順序依存、時刻依存、共有ミュータブル状態、外部実通信
- 公開 API / メッセージ / 設定形式の変更に contract test や schema fixture がない

## surface 条件付き補助観点

- `HTTP API`: boundary validation、型絞り込み、schema、contract test を確認する（例: Zod / Pydantic、discriminated union）
- `database / data store`: migration と既存データ前提を検証する fixture や test があるかを見る
- `CLI / developer tool`: 出力フォーマットや help の契約を壊さないテストがあるかを見る
- `external integration`: 外部 API 契約や callback 形状を固定する test / schema を確認する

## false positive 注意

- 小規模なローカル変更に対し、将来の抽象化不足だけで MEDIUM を量産しない
- lint や formatter で自動是正できるものは保守性の主要所見にしない
- 既存の共通抽象化が別ファイルにある場合、差分上の重複だけで即コピペ断定しない

## 標準マップ

| 観点 | 標準 |
|---|---|
| 保守性の主軸 | ISO/IEC 25010:2023 |
| observability-driven diagnosability | OpenTelemetry context propagation |
