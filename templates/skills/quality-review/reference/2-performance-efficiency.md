# 性能効率性 (Performance Efficiency)

ISO/IEC 25010:2023 の性能効率性に関するリファレンス。アルゴリズムだけでなく、HTTP・UI・データ取得・バックプレッシャーのような現代的なボトルネックを差分から拾う。

## 副特性ごとのアンチパターン + diff シグナル

### 時間効率性 (Time Behaviour)

- ネストループ O(n²)、配列線形探索の繰り返し、N+1 クエリ（→ JOIN / batch fetch / DataLoader）
- DB / API 側で絞れるデータをアプリケーションで全件取得後にフィルタしている
- async ハンドラ内で同期ブロッキング I/O を使っている（例: `fs.readFileSync`, `requests.get` in async）
- 再検証可能な読み取り処理で毎回フルフェッチしている

### 資源効率性 (Resource Utilization)

- LRU / TTL のないインメモリキャッシュ
- ストリーム処理可能なデータを全件メモリ展開している
- DB / HTTP クライアントでコネクション再利用やプールがない
- 無駄なポリフィルや tree-shaking 不全でバンドルが肥大化している（例: CJS 出力, `import type` 未使用）

### 容量充足性 (Capacity)

- ページネーションやバッチサイズ制御がない
- アップロード、ダウンロード、キュー、外部 API 呼び出しに上限がない
- バックプレッシャーなしで producer が consumer を圧倒する

## surface 条件付き補助観点

- `Web / Browser`: 不要な再レンダリング、バンドル増大、Core Web Vitals への悪影響を見る
- `HTTP API`: `Cache-Control`, `ETag`, 再検証、圧縮、ページネーションを確認する
- `database / data store`: N+1、全件読み込み、クエリ形状とインデックス前提の崩れを見る
- `async job / queue`: 同時実行数制限、バックプレッシャー、バッチサイズの妥当性を見る

## false positive 注意

- 小規模データしか扱わないことが diff から明らかな処理へ、将来の大規模化だけを理由に HIGH を付けない
- キャッシュ導入がないこと自体を問題視しない。繰り返しアクセスや再検証可能な読み取りがあるかで判断する
- React などの UI 指摘は、実際に再レンダリングや bundle 増大が差分に出ているときに限る

## 標準マップ

| 観点 | 標準 |
|---|---|
| 性能効率性の主軸 | ISO/IEC 25010:2023 |
| HTTP caching / revalidation | RFC 9111 |
| UI 操作体験の性能観点 | web.dev Core Web Vitals |
