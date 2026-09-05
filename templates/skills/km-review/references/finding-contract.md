# Finding分類契約

mainと独立reviewerは、正式なfindingの採用と分類にこの同じ契約を使う。

正式なfindingは次をすべて満たすものだけとする。

- 対象または必要なrepository内文脈に具体的な根拠がある
- 現実的な利用・運用・変更・攻撃条件で成立する
- 製品価値、信頼性、security、data、運用、保守性を意味のある程度で損なう
- 最小の修正方向または確認方法を示せる

好み・様式、機械的に検出できる形式問題、根拠のない一般論、極端な将来仮説、範囲を広げる理想論、今回の差分と無関係な既存問題はfindingにしない。`--repo`では既存問題も対象に含める。

severityは次で付ける。

- `CRITICAL` — 現実的な経路で即時の重大事故、壊滅的損失、即時悪用につながる
- `HIGH` — 主な成果の不達、重大な回帰、脆弱性、data・運用事故、長期保守を直撃する設計欠陥
- `MEDIUM` — 限定的だが意味のある品質・性能・可用性・運用・設計上の問題
- `LOW` — 具体的な改善価値はあるが、主な成果を重大には損なわない

blockingはseverityと別に判定する。

- CRITICAL / HIGHは`blocking: true`のblocker
- MEDIUM / LOWは原則`blocking: false`
- 明示された完了条件または主な成果を満たせない場合は、MEDIUM / LOWもblockerにできる
- 真偽を確定できない懸念はseverityを付けず、何を確認すれば決まるかを確認推奨として残す
- ユーザーが理由と条件を理解して受け入れた問題は`accepted-risk`とし、severityは変えない
- 判定を通すためにseverityやblockingを変更しない
