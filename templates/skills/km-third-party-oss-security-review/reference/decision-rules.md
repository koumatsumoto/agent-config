# Third-Party OSS Security Review Decision Rules

判定は`ALLOW` / `ALLOW_WITH_CONDITIONS` / `NEEDS_HUMAN_REVIEW` / `REJECT`。共通8観点とecosystem固有の評価から、契約衝突の有無→基本判定→利用文脈の順に適用する。

## 契約が衝突する場合

第1節の`NEEDS_HUMAN_REVIEW`と第2節の`REJECT`が同時に成立する場合の優先順位は未決。例は、成果物が`unresolved`で、信頼できない由来も確定している場合。
節の順序から優先順位を推測せず、`ALLOW` / `ALLOW_WITH_CONDITIONS`にも進まない。通常の最終判定レポートの代わりに、同時成立する条件・根拠と優先順位が未決であることを報告し、採用ポリシーの決定者へ確認する。未特定と既知の危険の両方を示す。

## 1. 特定不能・証跡不足

次のいずれかなら`NEEDS_HUMAN_REVIEW`とし、`ALLOW` / `ALLOW_WITH_CONDITIONS`を選ばない。

- `Artifact Resolution Status != resolved`（tag未特定、複数候補を含む）。
- ecosystemが不明・曖昧、または推測で絞り込まれている。
- registry / marketplaceを取得できない。

## 2. 採用阻害要因

次のいずれかが対象成果物に当たれば`REJECT`。

- 組織の方針違反。
- 未解決Critical advisory。
- 明確に危険な実行権限・影響範囲。
- 信頼できない由来（typosquatting、impersonation、publisher不整合）。

## 3. 許可できる範囲

`ALLOW`は、第2節に該当せず、次をすべて満たす場合だけ。

- 成果物・GitHub repository・ソース（tag / release / commit、vsix等）の対応を一次ソースで検証済み。
- advisory情報源を確認済みで、対象に未解決Critical / High advisoryがない。
- 主要観点（提供元と由来、脆弱性、実行権限と影響範囲、公開・配布の整合性）に未確認事項がない。
- `yanked` / `deprecated` / `unpublished`ではない。
- 供給網証明のあるecosystemで、証明欠落とpublisher不整合が同時に生じていない。

阻害要因がなく、運用可能な条件で採用できる場合は`ALLOW_WITH_CONDITIONS`。条件の例はversion / tag固定、devDependency / build-time限定、install scripts無効化、本番非投入、secretsアクセス制限。
証跡や主要要素の欠落、repository対応の未解決・曖昧さ、高いトレードオフ、権限・データ影響を機械的に止めきれない場合など、画一的に決められなければ`NEEDS_HUMAN_REVIEW`。repository対応が曖昧な状態を`ALLOW`にしない。
阻害要因が確認されていなくても、advisory情報源が取得不能なら`NEEDS_HUMAN_REVIEW`。脆弱性は未確認とし、`ALLOW` / `ALLOW_WITH_CONDITIONS`を選ばない。

## ecosystem固有の判定影響

- **npm**：新規パッケージで期待されるprovenance statementが欠落するなど、不確実性が残る場合は厳しい判定を選ぶ。
- **pip**：ネイティブ拡張（C / Rust / Cython）は「実行権限と影響範囲」を一段高いリスクとして扱う。ネイティブ拡張・`.pth`注入・ビルド時ネットワーク取得のいずれかがあれば「利用環境への影響」でも厳しい判定を選ぶ。

ここでのリスク評価を最終判定へ反映する段階数と、利用文脈との重複加算は未決。自動的な段階数・加算順を作らず、確認事実と未決の判定影響を分けて示す。

- **VS Code extension**：存在するclient / server等の内容、またはbundler出力の対応ソースを確認できなければ`NEEDS_HUMAN_REVIEW`。

## 判定を厳しくする条件

基本判定に、次の高リスク条件ごとに1段階を加える。段階は`ALLOW → ALLOW_WITH_CONDITIONS → NEEDS_HUMAN_REVIEW`とし、`NEEDS_HUMAN_REVIEW`で止める。この規則だけで`REJECT`にはしない。

- `production=true`
- `secrets_access=true`
- `data_sensitivity=high`
- `実行形態 ∈ {editor-extension, ci, cli}`

既定で降格なしとする組合せ:

- `実行形態 ∈ {library, build-tool, test-tool, node-server, browser}`
- `development` scope のみでの利用
最保守の既定値を採用した利用条件も加算対象にする。既定値の採用を「主要な判断理由」と「不確実性 / 未確認事項」に書き、適用前後の判定を「主要な判断理由」に1点として示す。
