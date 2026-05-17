# セキュリティ (Security)

情報・データを保護し、許可された人物・システムだけがアクセスできるか。

## 機密性 (Confidentiality)

- [ ] シークレットがハードコードされず secret manager 経由で取得されるか
- [ ] `.env` / `.pem` / `.key` / `*credentials*` が VCS に入っていないか
- [ ] ログ / レスポンス / エラーメッセージに PII / トークン / 内部情報が漏れないか
- [ ] 通信 (TLS 1.2+ / 適切な cipher suite) と保存時暗号化が適用されるか
- [ ] 鍵管理 (KMS / HSM) と rotation が設計されているか
- [ ] バックアップ / スナップショット / メトリクス側で機密情報が漏れないか
- [ ] 新規エンドポイント / handler に認可チェック (middleware / `@authorize` / policy gate / RLS 等) が設定されているか
- [ ] ロール定義の追加で wildcard (`admin:*`) / `super-admin` 濫用が発生していないか
- [ ] 認可粒度 (BOLA / BOPLA — オブジェクト所有者検証) が成立しているか
- [ ] secret rotation の自動化 / 秘密の検出 (gitleaks / trufflehog) が CI に組み込まれているか

## 完全性 (Integrity)

データ・状態の改変防御観点 (攻撃耐性は Resistance 側)。

- [ ] スキーマバリデーションで入力境界を防御するか
- [ ] SQLi / コマンドインジェクション / パストラバーサル / SSRF / NoSQLi 対策が成立するか
- [ ] 出力エンコーディング (HTML / JS / URL / SQL / CSV) が context-aware か
- [ ] CSRF / clickjacking / Host header injection / open redirect の対策が成立するか
- [ ] デシリアライズ (pickle / yaml.load / 無検証 JSON.parse / prototype pollution) を避けるか
- [ ] LLM 出力を DB スキーマ整合 / 型検証してから使うか (改変経路の遮断視点)
- [ ] 改ざん検知 (HMAC / 署名 / hash チェーン) が必要な経路で適用されるか
- [ ] CI/CD pipeline integrity (artifact 改ざん防止) が成立しているか

## 否認防止 (Non-repudiation)

- [ ] 重要操作の証跡が署名 / append-only / 第三者検証可能な形で残るか
- [ ] タイムスタンプが信頼可能なソースから取得されるか (NTP / TSA)

## 責任追跡性 (Accountability)

- [ ] 重要操作の監査ログに操作者 / 時刻 / 結果 / 対象が記録されるか
- [ ] 監査ログが改ざん耐性 (WORM / 不変ストレージ / 別アカウント保管) を持つか
- [ ] 管理者操作と一般操作のログが分離されているか
- [ ] Security Logging and Monitoring (SIEM 連携、検知ルール) が構築されているか

## 真正性 (Authenticity)

主体 (利用者・サービス) の真正性確認観点。認可粒度は機密性側。

- [ ] 認証ミドルウェアが全保護リソースに適用されるか
- [ ] MFA / セッション失効 / JWT 検証 (alg=none 拒否) が成立するか
- [ ] OAuth 2.1 / OIDC の state / PKCE / nonce / DPoP / refresh token rotation が正しく扱われるか
- [ ] WebAuthn / Passkey などフィッシング耐性のある認証手段が考慮されるか
- [ ] session fixation / session hijacking / cookie scope (SameSite / Secure / HttpOnly) を防御するか
- [ ] timing attack 耐性 (constant-time comparison for tokens) があるか

## 耐性 (Resistance)

攻撃面遮断 / 攻撃耐性観点 (データ改変防御は Integrity 側)。

- [ ] 認証 / 高コスト API にレート制限 / サイズ上限があるか
- [ ] 全件更新 / 削除を単一リクエストでできないか
- [ ] 業務ロジック乱用 (bulk 購入 bot / ポイント乱獲 / 投機的アクセス) を検知 / 制限する仕組みがあるか
- [ ] 廃止 / 旧バージョンの API endpoint / staging / debug endpoint が本番に残置していないか
- [ ] 依存関係に既知脆弱性がなく、ロックファイル / SBOM / vulnerability scan / SCA / EOL 管理があるか
- [ ] アーティファクト来歴 (SLSA / Sigstore) が確認可能か
- [ ] LLM/AI: prompt injection 防御 / tool 実行境界 / テナント分離 / Excessive Agency 制限が成立するか
- [ ] LLM/AI 出力の tool execution 経路を sandbox / allowlist で隔離するか (攻撃面視点)
- [ ] RAG / vector DB へのドキュメント取込で sanitize / source attestation があるか
- [ ] LLM 推論 API key / endpoint に rate limit / abuse detection (Model Theft 対策) があるか
- [ ] DDoS / Slowloris / algorithmic complexity (regex catastrophic backtracking / hash collision) / 増幅攻撃に対する基本防御が成立しているか
- [ ] CSP / HSTS / Referrer-Policy / Permissions-Policy / COEP / COOP のブラウザ多層防御が設定されているか
- [ ] Security Misconfiguration (debug endpoint の本番露出、default credential 残置) を回避するか

## 参照

- ISO/IEC 25010:2023
- OWASP ASVS, OWASP Top 10 (現行版を確認: 2025 リリース済)
- OWASP API Security Top 10 (2023)
- OWASP LLM Top 10
- CWE Top 25
- SLSA, Sigstore
- Anthropic AI safety / responsible scaling policy
- NIST Cybersecurity Framework
