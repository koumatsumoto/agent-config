# Third-Party OSS Security Review 出力形式

`reference/decision-rules.md`の契約衝突に該当する場合は、同規則の例外報告を優先し、最終判定を確定する以下の通常形式は使わない。

## サマリー

冒頭に次のキーを必ず出力する。

- `対象`：入力識別子
- `種別 / ecosystem`：`npm` / `pip` / `vscode-extension` / `github-repo`
- `Resolved Artifact`：特定した成果物。未解決なら`未特定`
- `Artifact Resolution Status`：`resolved` / `candidate` / `unresolved`
- `Repository`：解決済みGitHub URL。未解決なら`未特定`
- `最終判定`：`ALLOW` / `ALLOW_WITH_CONDITIONS` / `NEEDS_HUMAN_REVIEW` / `REJECT`
- `Review Confidence`：`High` / `Medium` / `Low`

## 必須セクション

次の順序を保つ。

1. `レビュー対象`
2. `利用文脈`
3. `対象成果物の特定結果`
4. `最終判定`
5. `主要な判断理由`
6. `カテゴリ評価`
7. `主要な指摘`
8. `必要条件`
9. `人間確認が必要な点`
10. `主要な証跡`
11. `不確実性 / 未確認事項`

特定結果にstatusを明示し、`candidate`なら候補と一次ソース上の区別を示す。`unresolved`なら冒頭に「採用判定ではなくリポジトリ単位の暫定評価」と書く。

## Review Confidence

- `High`：全8観点が一次ソースで裏付けられ、`Artifact Resolution Status = resolved`
- `Medium`：主要観点は一次ソースで確認済みだが、一部に補助ソースまたはunknownが残る
- `Low`：`Artifact Resolution Status != resolved`、または主要観点の一次ソースが欠落

VS Code Marketplaceの`Verified Domain`バッジがないpublisherは、提供元の信頼性の不確実要素として確信度を下げる。

## 記述

日本語で書き、主要指摘は`## <severity>: <要約>`に観点・問題・根拠・推奨対応を付ける。証跡にはURLと確認日（`YYYY-MM-DD`）を付け、不在が論点なら「該当なし（確認日: YYYY-MM-DD）」と書く。
判定理由は原則2〜4点にまとめ、独立理由が増える場合も主要理由へ畳む。安全を断言せず、確認済み範囲と未確認事項を分ける。
- `ALLOW_WITH_CONDITIONS`：運用条件を「必要条件」へ書く
- `NEEDS_HUMAN_REVIEW`：不足情報と確認主体を「人間確認が必要な点」へ書く
- `REJECT`：理由を`policy` / `vulnerability` / `provenance` / `behavior` / `privilege`で分類する
