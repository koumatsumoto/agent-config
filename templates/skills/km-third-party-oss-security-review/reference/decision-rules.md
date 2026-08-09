# Third-Party OSS Security Review Decision Rules

判定は次の 4 つに固定する。

- `ALLOW`
- `ALLOW_WITH_CONDITIONS`
- `NEEDS_HUMAN_REVIEW`
- `REJECT`

## ALLOW

次をすべて満たす場合のみ許可する。

- `Artifact Resolution Status = resolved`
- 対象成果物とリポジトリの対応が一次ソースで確認できている
- advisory の情報源を確認済みで、未解決の Critical / High advisory がない
- 実行権限と影響範囲に明確な危険の兆候がない
- 組織の方針に違反していない
- 対象成果物が yanked / deprecated / unpublished でない
- 主要観点（提供元と由来、脆弱性、実行権限と影響範囲、公開・配布の整合性）に未確認事項がない

## ALLOW_WITH_CONDITIONS

`Artifact Resolution Status = resolved` であり、明確な採用阻害要因はないものの、運用条件を付ければ採用できる場合に使う。

例:

- version / extension version / tag pin が必要
- devDependency / build-time only 限定
- install scripts を無効化できる環境限定
- `production` 環境非投入
- secrets へのアクセス権限を制限する

条件は運用可能なものだけを書き、抽象的な注意喚起は避ける。

## NEEDS_HUMAN_REVIEW

画一的に判定できない場合に使う。

- 証跡不足
- `Artifact Resolution Status != resolved`（repo-only で tag 未特定等を含む）
- 対象成果物とリポジトリの対応が曖昧
- 外部ソースの障害で主要な判定要素が欠落
- ecosystem 判別が曖昧（monorepo 等）
- 利用文脈依存の高トレードオフ
- 権限やデータ影響が大きく、機械的に止めきれない

## REJECT

次のいずれかに当てはまる場合に使う。

- 組織の方針違反
- 対象成果物に当たる未解決 Critical advisory
- 明確に危険な実行権限や影響範囲
- 信頼できない由来（typosquatting、impersonation、publisher の整合性欠落）

## 必須判定規則

次のいずれかに該当する場合は `ALLOW` を出さない。

- `Artifact Resolution Status != resolved`
- 対象成果物とリポジトリの対応が曖昧
- 対象成果物（registry / marketplace の配布物）とリポジトリのソースとの対応を一次ソースで検証できない（例: tag / release / commit の紐付けが取れない、vsix とソースの対応が取れない）
- advisory の情報源を確認していない
- 主要観点（提供元と由来、脆弱性、実行権限と影響範囲、公開・配布の整合性）のいずれかに未確認事項が残る
- 対象成果物が yanked / deprecated / unpublished
- 供給網の証明がある ecosystem で証明が欠落し、publisher の整合も取れない

次に該当する場合は `ALLOW` と `ALLOW_WITH_CONDITIONS` のどちらとも判定せず、`NEEDS_HUMAN_REVIEW` または `REJECT` と判定する。

- リポジトリだけを入力し、対象成果物を特定できていない
- 複数 ecosystem 候補を推測で絞り込んだ場合

対象成果物に当たる未解決の Critical 相当 advisory がある場合は `REJECT` を検討する。

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

例:

- 基本判定=`ALLOW`、`production=true` のみ → `ALLOW_WITH_CONDITIONS`
- 基本判定=`ALLOW`、`production=true` + `secrets_access=true` → `NEEDS_HUMAN_REVIEW`
- 基本判定=`ALLOW`、高リスク 3 条件以上 → `NEEDS_HUMAN_REVIEW`（下限）
- 基本判定=`ALLOW_WITH_CONDITIONS`、`production=true` のみ → `NEEDS_HUMAN_REVIEW`
- 基本判定=`NEEDS_HUMAN_REVIEW`、任意 → `NEEDS_HUMAN_REVIEW`（下限）

備考:

- 最も保守的な既定値を採用した利用条件も対象に含める。既定値を使った旨はレポートの「主要な判断理由」と「不確実性 / 未確認事項」に明記する
- 条件適用前後の判定値を「主要な判断理由」に 1 点として書く
