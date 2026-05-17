# 柔軟性 (Flexibility)

異なる環境・要件に適応できるか。環境差し替え・スケール・デプロイ・ベンダー置換のしやすさを見る。

## 適応性 (Adaptability)

- [ ] URL / パス / ポート / 資格情報がハードコードされず環境から注入されるか
- [ ] OS / ランタイム / ロケール差を吸収できるか
- [ ] feature flag / 設定駆動で振る舞いを切り替えられるか
- [ ] 環境変数名がドキュメント化され衝突しないか
- [ ] dev / staging / production 間で同じバイナリ / イメージが動くか

## スケーラビリティ (Scalability)

「容量を増やす操作が可能か」(再デプロイ不要 / 自動 / 線形)。現行容量設計の限界判定は 2-性能効率性 / 容量充足性側。

- [ ] ステートレスでプロセス間共有状態に依存しないか
- [ ] セッション / キャッシュが共有ストア (Redis 等) に外出しされるか
- [ ] ロック / スケジューラ / キューが水平スケール前提か
- [ ] スケールアウト操作が再デプロイなしで実行可能か
- [ ] shared-nothing architecture を維持しているか
- [ ] cost scalability (FinOps) — 容量増加が線形に費用増加しない設計か

## 設置性 (Installability)

- [ ] 自動化された導入手順 (IaC / コンテナ / Helm / Terraform) があるか
- [ ] 段階的デプロイ (blue-green / canary / shadow / feature flag rollout) と自動ロールバックが可能か
- [ ] 依存バージョンが固定され再現可能ビルドになるか
- [ ] migration が forward-only にならず、ロールバック可能か (または明示的に forward-only と承認されているか)
- [ ] 初回セットアップに必要な手順が `README` / `INSTALL` で完全に網羅されているか

## 置換性 (Replaceability)

自分の中身を入れ替える観点 (相手と合わせるのは 3-互換性 / 相互運用性側)。

- [ ] 外部 SDK / ベンダー API が interface / port で抽象化されているか (hexagonal / Ports & Adapters)
- [ ] 一方向 migration を避け、後方互換とロールバック面があるか
- [ ] 内部実装が標準形式 (JSON Schema / Protobuf / OpenAPI) を採用しベンダー固有形式を増やしていないか
- [ ] ベンダーロックインを避けるため、代替候補が複数あるか
- [ ] regional / sovereign cloud 対応のため依存抽象化が可能か

## 参照

- ISO/IEC 25010:2023
- The Twelve-Factor App
- CNCF deployment patterns (canary / blue-green)
- Terraform / Pulumi / Helm
- Ports & Adapters (Hexagonal Architecture)
