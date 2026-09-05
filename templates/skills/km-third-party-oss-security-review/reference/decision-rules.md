# Third-Party OSS Security Review Decision Rules

判定は`ALLOW` / `ALLOW_WITH_CONDITIONS` / `NEEDS_HUMAN_REVIEW` / `REJECT`に固定する。共通8観点とecosystem固有の評価をもとに、まず下記の契約衝突がないか確認し、衝突しない場合は各節の条件で基本判定を決め、最後に利用文脈を適用する。

## 契約が衝突する場合

第1節の`NEEDS_HUMAN_REVIEW`条件と第2節の`REJECT`条件が同時に成立する場合の優先順位は未決である。例えば、成果物は`unresolved`だが、信頼できない由来が既に確定している場合が該当する。

節の順序から優先順位を推測せず、`ALLOW` / `ALLOW_WITH_CONDITIONS`にも進まない。最終判定を確定する通常のレポートは作らず、同時に成立する条件・根拠と、`NEEDS_HUMAN_REVIEW` / `REJECT`のどちらを優先するか未決であることを報告し、採用ポリシーの決定者へ確認する。未特定と既知の危険のどちらも隠さない。

## 1. 特定不能・証跡不足

次の場合は`NEEDS_HUMAN_REVIEW`とし、`ALLOW` / `ALLOW_WITH_CONDITIONS`へ進まない。

- `Artifact Resolution Status != resolved`（repo-onlyでtag未特定、複数候補を含む）
- ecosystemが不明・曖昧、または複数候補を推測で絞り込んでいる
- registry / marketplaceが取得できない

## 2. 採用阻害要因

対象成果物について次のいずれかに当てはまる場合は`REJECT`とする。

- 組織の方針違反
- 対象成果物に当たる未解決Critical advisory
- 明確に危険な実行権限や影響範囲
- 信頼できない由来（typosquatting、impersonation、publisherの整合性欠落）

## 3. 許可できる範囲

`ALLOW`は、次をすべて満たす場合だけ選ぶ。

- 対象成果物とGitHub repository、およびそのソース（tag / release / commit、vsix等）の対応を一次ソースで検証できている
- advisoryの情報源を確認済みで、対象に未解決Critical / High advisoryがない
- 主要観点（提供元と由来、脆弱性、実行権限と影響範囲、公開・配布の整合性）に未確認事項がない
- 対象成果物が`yanked` / `deprecated` / `unpublished`でない
- 供給網の証明があるecosystemで、証明欠落とpublisher不整合が同時に生じていない

実行権限の明確な危険と組織の方針違反は第2節で除外済みとする。

明確な採用阻害要因はないものの、運用条件を付ければ採用できる場合は`ALLOW_WITH_CONDITIONS`を使う。条件は運用可能なものに限る（version / tag pin、devDependency / build-time only、install scripts無効化、本番非投入、secretsへのアクセス制限など）。

証跡不足、repository対応の曖昧さ、外部ソース障害による主要要素の欠落、利用文脈の高トレードオフ、権限・データ影響を機械的に止めきれない場合など、画一的に判定できなければ`NEEDS_HUMAN_REVIEW`とする。repositoryを解決できない・対応が曖昧な場合も`ALLOW`にはしない。

採用阻害要因が確認されておらず、advisory情報源が取得不能の場合は`NEEDS_HUMAN_REVIEW`とする。`ALLOW` / `ALLOW_WITH_CONDITIONS`は選ばず、脆弱性の有無を未確認として残す。

## 判定を厳しくする条件

判定は次の 3 段階で厳しくする。`REJECT` は別の規則で判定し、この条件だけでは到達しない。

```
ALLOW → ALLOW_WITH_CONDITIONS → NEEDS_HUMAN_REVIEW
```

基本判定（共通 8 観点と対象種別ごとの評価から導いた判定）に対し、次の高リスク条件ごとに 1 段階ずつ厳しい判定を適用する。該当する条件の数だけ段階を進め、下限は `NEEDS_HUMAN_REVIEW` とする。

高リスク条件（各 1 段階）:

- `production=true`
- `secrets_access=true`
- `data_sensitivity=high`
- `実行形態 ∈ {editor-extension, ci, cli}`

既定で降格なしとする組合せ:

- `実行形態 ∈ {library, build-tool, test-tool, node-server, browser}`
- `development` scope のみでの利用

備考:

- 最も保守的な既定値を採用した利用条件も対象に含める。既定値を使った旨はレポートの「主要な判断理由」と「不確実性 / 未確認事項」に明記する
- 条件適用前後の判定値を「主要な判断理由」に 1 点として書く
