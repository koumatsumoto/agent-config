# セキュリティ (Security)

ISO/IEC 25010:2023 のセキュリティに関するリファレンス。インジェクションだけでなく、認可粒度、ブラウザ境界、API 消費安全性、サプライチェーンまで含めて現代的な実害へ寄せて確認する。

## 副特性ごとのアンチパターン + diff シグナル

### 機密性 (Confidentiality)

- ハードコードされたシークレット、`.env` / `.pem` / `.key` の tracked 化
- ログやレスポンスへの PII、トークン、内部情報の漏えい
- 平文通信や保存時暗号化の欠如

### 真正性 / 完全性 (Authenticity / Integrity)

**真正性**

- 認証ミドルウェア未適用、所有者検証不足、BOPLA を含む認可粒度不足

**完全性**

- スキーマバリデーション未適用、SQLi（`$queryRawUnsafe`, f-string SQL）、XSS（`dangerouslySetInnerHTML`, `| safe`）、SSRF、コマンド / パスインジェクション
- デシリアライゼーションや prototype pollution の入口（`pickle.loads`, `yaml.load`, 無検証 `JSON.parse`）を開く
- ユーザー入力を含む URL や外部 API 応答を信頼しすぎる unsafe consumption of APIs
- LLM 出力を検証せず実行に使う

### 責任追跡性 / 否認防止 (Accountability / Non-repudiation)

**責任追跡性**

- 重要操作に監査ログがない、操作者を特定できない、改ざん耐性がない

**否認防止**

- append-only 証跡や署名付き送信が必要な操作で証明がない

### 耐性 (Resistance)

- 認証や高コスト API にレート制限やサイズ上限がない
- 全件更新や全件削除を単一リクエストで実行できる
- コネクション上限、slowloris 耐性、エッジ保護の前提が必要な変更なのに、アプリ側でも無防備なままになっている
- 既知脆弱性依存、ロックファイル不在、依存関係混乱、来歴不明なアーティファクトを導入する

## surface 条件付き補助観点

- `HTTP API`: BOLA、BOPLA、入力境界、レート制限、unsafe API consumption を確認する
- `Web / Browser`: CORS、Cookie 属性、CSP、XSS の導線を見る
- `external integration`: webhook 署名、リプレイ防止、外部応答の検証、TLS、認証ヘッダ、SSRF の導線を見る
- `AI/LLM`: 構造化入力、出力検証、テナント分離、tool 実行境界を見る
- `cloud runtime / IaC`: secret 配布、アーティファクト署名 / 来歴、公開設定の緩さ、暗号設定を確認する

## false positive 注意

- 権限モデルが単純な変更に対し、BOPLA を機械的に要求しない
- WAF や CDN など diff に出ない外部防御層の有無を断定しない
- DDoS 耐性の指摘は、`cloud runtime / IaC` やアプリ側レート制限・サイズ上限の変更が差分にある場合に寄せる
- 監査ログの保存先や改ざん耐性がコード差分にない場合、存在しないと断定しない

## 標準マップ

| 観点 | 標準 |
|---|---|
| セキュリティの主軸 | ISO/IEC 25010:2023 |
| Web / API の検証観点 | OWASP ASVS |
| BOLA / リソース消費 / unsafe API consumption | OWASP API Security Top 10 2023 |
| アーティファクト来歴 / transparency | Sigstore documentation |
