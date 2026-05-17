# 互換性 (Compatibility)

ISO/IEC 25010:2023。「同じハードウェア・ソフトウェア環境を共有しながら、他の製品・システムと情報交換できる程度」を見る。

## 共存性 (Co-existence)

- [ ] ポート / 環境変数 / キャッシュキー / キュー名 / テーブル名 / メトリクス名で名前空間衝突がないか
- [ ] ワーカ数 / プールサイズの引き上げが同居プロセスを圧迫しないか
- [ ] ファイルパス / ロック / シグナル処理が同居前提と整合するか
- [ ] サポートする OS / ランタイム / ライブラリのバージョン範囲が明示されているか
- [ ] グローバル状態 (環境変数 / シングルトン / プロセス全体の logger 設定) を破壊的に書き換えていないか

## 相互運用性 (Interoperability)

- [ ] API / Webhook / メッセージ / CLI / 設定 / DB スキーマで必須項目の追加・削除・型変更がないか
- [ ] 列挙値 / 日時形式 / タイムゾーン / エンコード / 小数表現 / nullability の意味変更がないか
- [ ] ヘッダ名 / 署名方式 / HTTP ステータス / エラーフォーマットの意味が変わっていないか
- [ ] 破壊的変更にバージョニング (SemVer / API バージョン) / 段階移行 / deprecation 期間があるか
- [ ] 契約 (OpenAPI / JSON Schema / Protobuf) と実装が同期しているか
- [ ] consumer-driven contract test / schema fixture / golden file で互換が検証されるか
- [ ] 標準形式 (UTF-8 / RFC 3339 / OpenAPI 3.x など) を選好し、独自形式を増やしていないか
- [ ] エンコード変換 (CSV escape / JSON escape / URL encode) が context-aware か

## 参照

- ISO/IEC 25010:2023
- SemVer 2.0.0
- OpenAPI 3.x, JSON Schema, Protocol Buffers
- RFC 9457 (Problem Details), RFC 3339 (Date/Time), RFC 8259 (JSON)
