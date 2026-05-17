# 安全性 (Safety)

ISO/IEC 25010:2023。「製品が、人・財産・環境への危害のリスクを許容範囲内に抑える程度」を見る。正当な利用者・運用者が事故・不可逆損失を起こしにくいかを確認する (攻撃者視点はセキュリティ側)。

## 運用制約 (Operational Constraint)

- [ ] バッチサイズ / 再帰深度 / 同時接続数 / 再試行回数に上限があるか
- [ ] 上限がコード or 設定で明示され、無制限な経路がないか
- [ ] 高権限操作 (admin / root) が必要な経路で明示的な elevation を要求するか
- [ ] 危険なフラグ (`--force` / `--yes` / 環境変数) が runtime に伝わらない経路が確保されているか

## リスク識別 (Risk Identification)

- [ ] 全件削除 / 一括送信 / 本番反映 / 課金確定など高リスク操作が識別されているか
- [ ] 設定値の妥当性検証があり、不正設定で静かに誤動作しないか
- [ ] 危険な操作の前にチェックリスト / プリフライト確認があるか
- [ ] 環境名 (`production` / `staging`) を hostname / config / UI で目立つように示しているか

## フェイルセーフ (Fail Safe)

危害回避のための停止 / 安全側倒れ観点 (データ整合性復旧は 5-信頼性 / 回復性側)。

- [ ] 失敗時に fail-closed (安全側) に倒れるか
- [ ] 部分書き込みを避け、トランザクション / ロールバックで一貫性を保つか
- [ ] 危害が拡大する前にシステムを停止する明示的な経路があるか
- [ ] タイムアウト / 接続失敗時に「成功」と誤判定しないか
- [ ] immutable infrastructure / blast radius limitation を考慮しているか
- [ ] canary deploy で SLO breach の自動ロールバックが効くか

## ハザード警告 (Hazard Warning)

事故防止のための冗長確認 / 利用者通知観点 (利用者エラー回避視点は 4-インタラクション能力 / ユーザーエラー防止側)。

- [ ] 破壊的操作の事故防止確認 (確認 / dry-run / 差分プレビュー) が冗長に成立しているか
- [ ] feature flag / メンテナンスモード / 一時停止条件が運用に伝わるか
- [ ] 危険操作が WARN/ERROR レベルで明示され INFO に埋もれないか
- [ ] エラーメッセージで「実行された影響範囲」が利用者に伝わるか
- [ ] 環境名 (production / staging) を hostname / config / UI で目立つように示しているか
- [ ] 「成功」表示なのに副作用が部分失敗のような誤誘導を回避しているか

## 安全な統合 (Safe Integration)

正当な利用での妥当性確認 (攻撃面遮断は 6-セキュリティ側)。

- [ ] 外部 API 応答をスキーマ妥当性検証してから使うか
- [ ] timeout / レート制限超過 / 不正レスポンスを事故 (誤動作) として扱うか
- [ ] webhook / callback の署名検証とリプレイ防止があるか
- [ ] サードパーティライブラリの実行範囲が明示されているか
- [ ] LLM / AI の自律実行で副作用 (DB 書き込み / API 呼び出し / shell 実行) に Human-in-the-Loop (HITL) 承認ステップを挟むか
- [ ] money-affecting operation に二重承認 (4-eyes principle) を要求するか

## 参照

- ISO/IEC 25010:2023
- IEC 61508 (Functional Safety) 概念
- AWS Well-Architected Framework — Operational Excellence pillar
- OWASP API Security Top 10 (2023) — Server Side Request Forgery / Broken Authorization
- Anthropic AI safety / responsible scaling policy (agentic AI の自律実行)
