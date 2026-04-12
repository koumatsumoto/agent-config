# 信頼性 (Reliability)

ISO/IEC 25010:2023 の信頼性に関するリファレンス。タイムアウトやリトライだけでなく、probe の役割分離、縮退運転、可観測性まで含めて「障害時に壊れにくく、追跡しやすいか」を見る。

## 副特性ごとのアンチパターン + diff シグナル

### 無欠陥性 (Faultlessness)

- 例外の握り潰し（`except Exception: pass`, 空 `catch`）、fail-open、cause チェーン消失（`raise ... from` なし）
- `string | null` のような曖昧なエラー戻り値で失敗意味が崩れる

### 可用性 (Availability)

- 単一障害点の導入
- readiness / liveness / startup の役割分離がない
- グレースフルシャットダウンなしで in-flight 処理を落とす
- 依存サービス障害で全機能停止する

### 障害許容性 (Fault Tolerance)

- タイムアウトなし（`AbortController`, `httpx timeout` 等なし）、指数バックオフやジッターなし、非冪等操作のリトライ
- retry budget や上限なしの再試行
- サーキットブレーカーやバックプレッシャーなしで障害を増幅する
- 部分失敗時の内訳や継続方針がない

### 回復性 (Recoverability)

- リソース解放漏れ（`try-finally`, `with`, `contextmanager` 不足）、一時ファイルやロックのクリーンアップ漏れ
- 冪等キーや重複排除がなく二重処理を起こす
- 縮退運転や機能制限で継続する設計がない

## surface 条件付き補助観点

- `external integration`: timeout、retry、idempotency、circuit breaker、degraded mode を確認する
- `cloud runtime / IaC`: startup / readiness / liveness、graceful shutdown、autoscaling と probe の整合を見る
- `async job / queue`: 並列数制限、部分失敗の表現、再実行の安全性を見る
- `HTTP API`: リクエスト ID、トレース伝播、重要操作のメトリクスが維持されるかを見る

## false positive 注意

- 外部依存がない変更に対して timeout や circuit breaker を機械的に求めない
- probe 設定の詳細が diff にない場合、存在しないと断定しない
- observability 指摘は「解析不能なまま障害を増やすか」で判断し、計装の好みの問題にしない

## 標準マップ

| 観点 | 標準 |
|---|---|
| 信頼性の主軸 | ISO/IEC 25010:2023 |
| startup / readiness / liveness | Kubernetes probes documentation |
| trace / log correlation | OpenTelemetry context propagation |
