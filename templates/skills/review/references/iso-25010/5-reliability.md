# 信頼性 (Reliability)

ISO/IEC 25010:2023。「指定された条件下、指定された期間にわたって機能を実行する程度」を見る。

## 無欠陥性 (Faultlessness)

- [ ] 例外の握り潰し / fail-open / cause chain 消失がないか
- [ ] 失敗を表す戻り値・例外型が一意で曖昧でないか
- [ ] 型システム / null safety / 静的解析で防げる欠陥を残していないか
- [ ] 故障時に解析可能な計装 (ログ / メトリクス / トレース) が **実在** するか (計装の標準化 / OTel 準拠は 7-保守性 / 解析性側)
- [ ] sentinel 値や暗黙の `null`/`undefined` を意味として再利用していないか

## 可用性 (Availability)

- [ ] 単一障害点を導入していないか
- [ ] readiness / liveness / startup probe の役割が分離しているか
- [ ] グレースフルシャットダウンで in-flight 処理を保護するか
- [ ] SLO / エラーバジェットの前提を壊していないか
- [ ] DR / multi-AZ / multi-region など可用性ターゲットを満たすか
- [ ] 起動時の依存関係 (DB / cache / 外部 API) が落ちていてもアプリが起動できるか (fast-fail 設計)

## 障害許容性 (Fault Tolerance)

- [ ] 外部呼び出しに timeout / 指数バックオフ / ジッターがあるか
- [ ] retry budget / 上限 / 冪等性確認の上でのリトライか
- [ ] サーキットブレーカー / bulkhead / 並列度制限 / バックプレッシャーがあるか
- [ ] 部分失敗時の内訳・継続方針が定義されているか
- [ ] hedged request / fallback chain の効果と副作用が制御されているか
- [ ] 外部システム障害時にエラーを伝搬するか縮退するかの方針が明示されているか

## 回復性 (Recoverability)

異常時のデータ整合性回復観点 (危害回避の停止は 9-安全性 / フェイルセーフ側、正常時のリソース管理は 2-性能効率性側)。

- [ ] 異常パスでのリソース解放 (try-finally / with / using / RAII) が漏れないか
- [ ] 冪等キー / 重複排除で再実行安全か
- [ ] 縮退運転 / 機能制限モードで継続できるか
- [ ] バックアップ / RTO/RPO に整合する回復手順があるか
- [ ] バックアップ整合性の定期検証 (backup integrity verification) があるか
- [ ] 中断したワークフローを途中から再開できるか (checkpoint / resume token)
- [ ] データ不整合からの自動復旧パスが定義されているか

## 参照

- ISO/IEC 25010:2023
- Google SRE Workbook (SLO / observability / postmortem)
- Kubernetes probes (readiness / liveness / startup)
- OpenTelemetry (tracing / metrics / logs)
- Chaos Engineering Principles
