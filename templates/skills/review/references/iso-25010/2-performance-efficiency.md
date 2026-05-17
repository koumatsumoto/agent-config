# 性能効率性 (Performance Efficiency)

指定条件下で使う資源量に対して達成される性能を見る。

## 時間効率性 (Time Behaviour)

- [ ] アルゴリズム計算量が入力規模に対して妥当か (O(n²) / 重複線形探索を回避)
- [ ] N+1 が JOIN / batch fetch / DataLoader 等に集約されているか
- [ ] フィルタ条件が DB / API 側で適用され、アプリ側全件取得後の絞り込みになっていないか
- [ ] async 経路で同期ブロッキング I/O を使っていないか
- [ ] p95 / p99 のテールレイテンシが SLO 内に収まる前提か
- [ ] cold start / lazy init / JIT 暖機の影響が運用許容範囲か
- [ ] 並列化可能な処理が直列実行になっていないか
- [ ] 過剰な再描画 / 過剰な API 呼び出しを抑止する仕組み (debounce / memoize) があるか

## 資源効率性 (Resource Utilization)

正常時の資源使用を最小化する観点 (異常時の解放漏れは 5-信頼性 / 回復性側)。

- [ ] インメモリキャッシュに LRU / TTL / 上限があるか
- [ ] 大量データはストリーム処理され、全件メモリ展開を避けているか
- [ ] DB / HTTP クライアントでコネクション再利用 / プールが効くか
- [ ] バンドルサイズが tree-shaking / code splitting で最小化されているか
- [ ] 正常パスでリソース (close / dispose / cleanup / unsubscribe) のライフサイクル管理が成立しているか
- [ ] イベントリスナー / observer / timer が累積しないか
- [ ] GC / メモリプレッシャ / heap fragmentation のリスクが許容範囲か
- [ ] メトリクスの cardinality 爆発を起こさないラベル設計か
- [ ] ロギングの volume / sampling が運用許容範囲か

## 容量充足性 (Capacity)

「現行の容量設計が要求を満たすか」(限界値・上限・予測)。容量を増やす操作の可否は 8-柔軟性 / スケーラビリティ側。

- [ ] ページネーション / バッチサイズの上限があるか
- [ ] アップロード / ダウンロード / キュー深度に上限と背圧 (backpressure) があるか
- [ ] レート制限 / 同時実行数 / クォータが設定されているか
- [ ] autoscaling シグナル (CPU / メモリ / QPS / 待ち行列長) と probe / SLI が整合するか
- [ ] 想定ピーク時の容量見積りが定量化されているか

## 参照

- ISO/IEC 25010:2023
- RFC 9111 (HTTP Caching)
- web.dev Core Web Vitals
- Google SRE Workbook (SLO / latency)
