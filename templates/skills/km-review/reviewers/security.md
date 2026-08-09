# security

**反証命題** — この変更は、現実的な攻撃者・濫用者が利用できる経路を新設せず、trust boundary、権限、tenant / user separation、秘密・機密データ、危険な副作用を保全している。

返し方・materiality gate・レーンの規律は、同時に渡される `reviewers/contract.md`。脆弱性クラスの引き出しは既に持っている前提で、探索予算は**この対象に固有の信頼境界とデータフロー**の特定へ配分する。

## 探索予算を使うテーマ

- **actor / asset / boundary** — 誰がどの入口から何へ到達できるか。信頼済みと未信頼の境界が変更でどう動くか
- **authority** — authn / authz、tenant・所有者・role、privilege、delegation が全経路で維持され、別経路から bypass できないか
- **sensitive data** — secret、token、PII、内部設定が入力・保存・log・error・egress・レポートのどこで露出・過剰共有されるか
- **untrusted input to execution** — 外部入力が query、command、template、path、code、LLM の tool / prompt、外部送信へ到達する境界
- **high-impact side effects** — 削除、送信、課金、本番反映、CI/CD、credential 利用を、越権・濫用で実行できないか
- **abuse と audit** — 正当な利用者の濫用が security consequence を持つとき、検出・追跡・否認防止が足りるか

## 境界

security consequence の無い通常障害・性能劣化・retry / recovery は reliability が主担当。現実的な actor・入口・破られる境界・得られる結果を構成できない一般的な hardening 提案は finding にしない。

## finding の根拠

**攻撃・濫用主体、入口、前提、破られる境界、達成される結果**を一つのシナリオとして示す。秘密値そのものはレポートへ複製しない。
