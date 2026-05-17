# 柔軟性 (Flexibility)

ISO/IEC 25010:2023。「製品が異なる環境・要件に適応できる程度」を見る。環境差し替え、スケール、デプロイ、ベンダー置換のしやすさを確認する。

## 適応性 (Adaptability)

- [ ] URL / パス / ポート / 資格情報がハードコードされず環境から注入されるか
- [ ] OS / ランタイム / ロケール差を吸収できるか
- [ ] feature flag / 設定駆動で振る舞いを切り替えられるか
- [ ] 環境変数名がドキュメント化され衝突しないか
- [ ] dev / staging / production 間で同じバイナリ / イメージが動くか

## スケーラビリティ (Scalability)

- [ ] ステートレスでプロセス間共有状態に依存しないか
- [ ] セッション / キャッシュが共有ストア (Redis 等) に外出しされるか
- [ ] ロック / スケジューラ / キューが水平スケール前提か
- [ ] 容量増加に対し垂直 / 水平の両方で対応可能か
- [ ] shared-nothing architecture を維持しているか

## 設置性 (Installability)

- [ ] 自動化された導入手順 (IaC / コンテナ / Helm / Terraform) があるか
- [ ] 段階的デプロイ (blue-green / canary / shadow / feature flag rollout) と自動ロールバックが可能か
- [ ] 依存バージョンが固定され再現可能ビルドになるか
- [ ] migration が forward-only にならず、ロールバック可能か (または明示的に forward-only と承認されているか)
- [ ] 初回セットアップに必要な手順が `README` / `INSTALL` で完全に網羅されているか

## 置換性 (Replaceability)

- [ ] 外部 SDK / ベンダー API が interface / port で抽象化されているか (hexagonal / Ports & Adapters)
- [ ] 一方向 migration を避け、後方互換とロールバック面があるか
- [ ] 独自形式でなく標準形式 (JSON Schema / Protobuf / OpenAPI) を選好するか
- [ ] ベンダーロックインを避けるため、代替候補が複数あるか

## 参照

- ISO/IEC 25010:2023
- The Twelve-Factor App
- CNCF deployment patterns (canary / blue-green)
- Terraform / Pulumi / Helm
- Ports & Adapters (Hexagonal Architecture)
