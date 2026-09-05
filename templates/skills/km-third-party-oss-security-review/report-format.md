# Third-Party OSS Security Review 出力形式

## サマリー（必ず冒頭に出力）

サマリーには次のキーを必ず含める。

- `対象`: 入力として与えられた識別子
- `種別 / ecosystem`: `npm` / `pip` / `vscode-extension` / `github-repo`
- `Resolved Artifact`: 特定できた対象成果物（未解決なら `未特定`）
- `Artifact Resolution Status`: `resolved` / `candidate` / `unresolved`
- `Repository`: 解決済み GitHub repository URL（未解決なら `未特定`）
- `最終判定`: `ALLOW` / `ALLOW_WITH_CONDITIONS` / `NEEDS_HUMAN_REVIEW` / `REJECT`
- `Review Confidence`: `High` / `Medium` / `Low`

## 必須セクション

以下をこの順で出力する。

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

`対象成果物の特定結果`では `resolved` / `candidate` / `unresolved` を明示し、`candidate` のときは候補と、それぞれが一次ソース上どう区別されているかを書く。

## Review Confidence

- `High`: 全 8 観点で一次ソースから裏付けが取れており、`Artifact Resolution Status = resolved`
- `Medium`: 主要観点は一次ソースで確認できているが、一部観点で補助ソースまたは unknown が残る
- `Low`: `Artifact Resolution Status != resolved`、または主要観点で一次ソースが欠落している

## 指摘形式

主要指摘は`## <severity>: <要約>`を見出しにし、`観点`、`問題`、`根拠`、`推奨対応`を明記する。根拠には確認日も含める。

## 記述ルール

- レポート本文は日本語で書く
- 判定理由は原則 2〜4点、独立理由が増える場合は主要理由に畳む
- 証跡には URL と絶対日付（`YYYY-MM-DD`）を付ける
- 証跡が無いことが論点の場合は「該当なし（確認日: YYYY-MM-DD）」と明記する
- `ALLOW_WITH_CONDITIONS`の運用条件を「必要条件」に書く
- `NEEDS_HUMAN_REVIEW` は不足情報と確認主体を書く
- `REJECT` は拒否理由を `policy` / `vulnerability` / `provenance` / `behavior` / `privilege` に分類する
- 「安全である」と断定せず、「確認できた範囲では」と「未確認事項」を分ける
- `Artifact Resolution Status = unresolved` のレポート冒頭には「採用判定ではなくリポジトリ単位の暫定評価」と明示する
