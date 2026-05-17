# 互換性 (Compatibility)

ISO/IEC 25010:2023。「同じハードウェア・ソフトウェア環境を共有しながら、他の製品・システムと情報交換できる程度」を見る。

## 共存性 (Co-existence)

他プロセス / 他サービスとの共存観点 (変更局所性の問題は 7-保守性 / 修正性側)。

- [ ] ネットワーク資源 (ポート / 帯域) で他プロセスと衝突しないか
- [ ] 永続資源 (DB / cache / queue / テーブル名) で名前空間衝突がないか
- [ ] 観測資源 (logger / metrics 名) で他プロセスのストリームと混ざらないか
- [ ] ワーカ数 / プールサイズの引き上げが同居プロセスを圧迫しないか
- [ ] ファイルパス / ロック / シグナル処理が同居前提と整合するか
- [ ] サポートする OS / ランタイム / ライブラリのバージョン範囲が明示されているか
- [ ] グローバル状態 (環境変数 / シングルトン / プロセス全体の logger 設定) を他プロセスに影響する形で書き換えていないか

## 相互運用性 (Interoperability)

相手と合わせる観点 (自分を入れ替え可能にするのは 8-柔軟性 / 置換性側)。

- [ ] API / Webhook / メッセージ / CLI / 設定 / DB スキーマで必須項目の追加・削除・型変更がないか
- [ ] DB schema migration が expand-contract / online schema change / dual write 等で互換性を保てるか
- [ ] メッセージング契約 (Kafka schema registry / Avro 互換モード = BACKWARD / FORWARD / FULL) が成立するか
- [ ] 列挙値 / 日時形式 / タイムゾーン / エンコード / 小数表現 / nullability の意味変更がないか
- [ ] ヘッダ名 / 署名方式 / HTTP ステータス / エラーフォーマットの意味が変わっていないか
- [ ] HTTP content negotiation (Accept / Content-Type / charset) が正しく扱われるか
- [ ] 破壊的変更にバージョニング (SemVer / API バージョン) / 段階移行 / deprecation 期間があるか
- [ ] 契約 (OpenAPI / JSON Schema / Protobuf) と実装が同期しているか
- [ ] consumer-driven contract test / schema fixture / golden file で互換が検証されるか
- [ ] 連携側に合わせる形式選択 (UTF-8 / RFC 3339 / 業界標準など) が成立しているか
- [ ] エンコード変換 (CSV escape / JSON escape / URL encode) が context-aware か
- [ ] CORS / preflight / cookie SameSite (ブラウザ互換性) が成立するか

## 参照

- ISO/IEC 25010:2023
- SemVer 2.0.0
- OpenAPI 3.x, JSON Schema, Protocol Buffers
- RFC 9457 (Problem Details), RFC 3339 (Date/Time), RFC 8259 (JSON)
