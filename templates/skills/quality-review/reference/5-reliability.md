# 信頼性 (Reliability)

ISO/IEC 25010:2023 の信頼性特性に関する品質リファレンス。副特性ごとに、diff レビューで確認すべきパターンとアンチパターンを示す。

## 無欠陥性 (Faultlessness)

- 例外の握り潰し: `except Exception: pass`、空 `catch` ブロック → fail-open の原因
- cause チェーンの欠如: Python `raise ... from` 未使用、TS エラーラッピングで original の `cause` 消失
- fail-open パターン: 認証・認可チェックがエラー時にアクセス許可にフォールバック
- 不適切な Result 型: エラー戻り値が `string | null` で型安全でない（TS: neverthrow, Python: returns ライブラリ）

## 可用性 (Availability)

- 単一障害点: 1 つの外部サービス障害でシステム全体が停止する設計
- ヘルスチェック: Kubernetes readiness/liveness probe の欠如、DB接続チェックのみで依存サービス未確認
- グレースフルシャットダウン: SIGTERM ハンドリングなし、in-flight リクエストの完了待ちなし
- コールドスタート: サーバーレス環境で初回リクエストの遅延を考慮していない初期化処理

## 障害許容性 (Fault Tolerance)

- タイムアウト欠如: HTTP クライアント・DB クエリ・外部 API 呼び出しにタイムアウトなし（TS: `fetch` の `signal`/`AbortController`, Python: `httpx` の `timeout`）
- リトライ: 指数バックオフなし・非冪等操作のリトライ・上限なしリトライ・ジッターなし
- サーキットブレーカー: 障害中の外部サービスへの継続的アクセス（カスケード障害の原因）
- 部分障害: バッチ処理で一部失敗時に全体ロールバック（部分成功を返すべき場面）、エラー応答に成功/失敗の内訳がない

## 回復性 (Recoverability)

- リソース解放漏れ: Python `with`/`contextmanager` 未使用、TS `using`（5.2+）/`try-finally` 未使用
- DB コネクション・ファイルハンドル・トランザクションの解放漏れ（特にエラーパス）
- 一時ファイル・一時テーブル・ロックのクリーンアップ漏れ
- 冪等性: リトライ時に二重処理が発生する操作（冪等キーの欠如）

## 実務補助: 並行性

- 同期ブロッキング: Python asyncio 内の `requests.get`・`time.sleep`・`open()`（→ `httpx`・`asyncio.sleep`・`aiofiles`）
- 無制限タスク生成: セマフォ/ワーカープールなしの並列タスク起動
- 共有ミュータブル状態: ロックなしの並行書き込み、TOCTOU 競合
- トランザクション分離: 読み取り一貫性の欠如、lost update

## 実務補助: 可観測性

- 失敗パスのログ欠如: エラーハンドリング内でログを出さずに握り潰し
- 構造化ログ未使用: 文字列結合のみ、コンテキスト情報（リクエスト ID, ユーザー ID, トレース ID）なし
- 分散トレース: コンテキスト伝播の途切れ（HTTP ヘッダ/メッセージメタデータの未転送）、span の欠如
- メトリクス: 重要なビジネス操作のカウンター/ヒストグラム未計装
