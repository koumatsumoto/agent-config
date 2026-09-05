# km-third-party-oss-security-review 評価シナリオ集

既存の採用判定・参照境界を守る回帰材料。架空の固定証跡を使い、実パッケージの安全性評価とは区別する。対象のinstall / execute、外部への書き込みは行わない。

## 題材と合否線

| 変更面 | 題材 | 合否線 |
| --- | --- | --- |
| 成果物の特定・判定 | unresolved-artifact | npm入力で対象versionが特定不能。`unresolved` / `NEEDS_HUMAN_REVIEW` / `Low`、冒頭に暫定評価と書く。`ALLOW` / `ALLOW_WITH_CONDITIONS`は不可 |
| 採用阻害要因 | critical-advisory | 一意に特定した対象versionに未解決Critical advisoryが当たる。低リスク利用文脈でも`REJECT`、理由は`vulnerability` |
| 情報源の失敗 | advisory-unavailable | 対象はresolvedだがadvisory取得不能。脆弱性なしと扱わず、`ALLOW`にしない。主要観点欠落としてconfidenceと未確認事項へ反映 |
| 利用文脈 | context-escalation | 全8観点を一次証跡で確認できるresolved対象。基本`ALLOW`から、development/library/secretsなし/lowは据置、productionだけなら`ALLOW_WITH_CONDITIONS`、productionとsecretsありなら`NEEDS_HUMAN_REVIEW`。厳格化だけでは`REJECT`にしない |
| ecosystem routing・読込順 | npm-only-routing | npm入力で最初にnpm reference、収集前にframework、評価後にdecision、報告前にreport-formatを読む。pip / vscode referenceを読まない |
| 報告 | report-contract | 各判定でサマリー7キー、固定11節とその順、confidence、URL・確認日、不足情報と確認主体、条件または拒否分類が揃う |

方法は変更後の回帰評価とする。実行担当には最初にSKILLを読み、その指示するタイミングでreferenceを読むよう伝える。成果物と実際の読込順・分岐のtraceを返させる。全件再走ではなく、変更した境界に対応する題材だけ選ぶ。

version無し入力を受けた際の質問・候補列挙・未解決化の優先順は固定しない。暗黙のlatest採用禁止と、未特定のまま許可しない境界だけを評価する。

## 決定的な確認

二つのruntime向けの明示起動設定、referenceの実在、reportの固定キー・節名はstructural checkを使う。文書に文字列があるだけではモデルの判定を証明しないため、上記の判断境界は分離実行で確認する。
