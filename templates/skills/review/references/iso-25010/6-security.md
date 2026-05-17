# セキュリティ (Security)

ISO/IEC 25010:2023。「製品が情報・データを保護し、許可された人物・システムだけがそれにアクセスできるようにする程度」を見る。

## 機密性 (Confidentiality)

- [ ] シークレットがハードコードされず secret manager 経由で取得されるか
- [ ] `.env` / `.pem` / `.key` / `*credentials*` が VCS に入っていないか
- [ ] ログ / レスポンス / エラーメッセージに PII / トークン / 内部情報が漏れないか
- [ ] 通信 (TLS 1.2+) と保存時暗号化が適用されるか
- [ ] 鍵管理 (KMS / HSM) と rotation が設計されているか
- [ ] バックアップ / スナップショット / メトリクス側で機密情報が漏れないか
- [ ] アクセス制御 (RBAC / ABAC) で最小権限の原則が成立しているか

## 完全性 (Integrity)

- [ ] スキーマバリデーションで入力境界を防御するか
- [ ] SQLi / コマンドインジェクション / パストラバーサル / SSRF / NoSQLi 対策が成立するか
- [ ] 出力エンコーディング (HTML / JS / URL / SQL / CSV) が context-aware か
- [ ] CSRF / clickjacking / Host header injection / open redirect の対策が成立するか
- [ ] デシリアライズ (pickle / yaml.load / 無検証 JSON.parse / prototype pollution) を避けるか
- [ ] LLM 出力を検証なしで実行・SQL・OS コマンドへ流していないか
- [ ] 改ざん検知 (HMAC / 署名 / hash チェーン) が必要な経路で適用されるか

## 否認防止 (Non-repudiation)

- [ ] 重要操作の証跡が署名 / append-only / 第三者検証可能な形で残るか
- [ ] タイムスタンプが信頼可能なソースから取得されるか (NTP / TSA)

## 責任追跡性 (Accountability)

- [ ] 重要操作の監査ログに操作者 / 時刻 / 結果 / 対象が記録されるか
- [ ] 監査ログが改ざん耐性 (WORM / 不変ストレージ / 別アカウント保管) を持つか
- [ ] 管理者操作と一般操作のログが分離されているか

## 真正性 (Authenticity)

- [ ] 認証ミドルウェアが全保護リソースに適用されるか
- [ ] 認可粒度 (BOLA / BOPLA 含むオブジェクト所有者検証) が成立するか
- [ ] MFA / セッション失効 / JWT 検証 (alg=none 拒否) が成立するか
- [ ] OAuth / OIDC の state / PKCE / nonce が正しく扱われるか
- [ ] WebAuthn / Passkey などフィッシング耐性のある認証手段が考慮されるか

## 耐性 (Resistance)

- [ ] 認証 / 高コスト API にレート制限 / サイズ上限があるか
- [ ] 全件更新 / 削除を単一リクエストでできないか
- [ ] 依存関係に既知脆弱性がなく、ロックファイル / SBOM / vulnerability scan があるか
- [ ] アーティファクト来歴 (SLSA / Sigstore) が確認可能か
- [ ] LLM/AI: prompt injection 防御 / tool 実行境界 / テナント分離が成立するか
- [ ] AI/LLM の出力を検証なしで privilege escalation 経路 (DB write / shell exec) へ流していないか
- [ ] DDoS / Slowloris / 増幅攻撃に対する基本防御が成立しているか

## 参照

- ISO/IEC 25010:2023
- OWASP ASVS, OWASP Top 10 (2021)
- OWASP API Security Top 10 (2023)
- OWASP LLM Top 10
- CWE Top 25
- SLSA, Sigstore
- Anthropic AI safety / responsible scaling policy
- NIST Cybersecurity Framework
