# Third-Party OSS Security Review Decision Rules

判定は次の 4 つに固定する。

- `ALLOW`
- `ALLOW_WITH_CONDITIONS`
- `NEEDS_HUMAN_REVIEW`
- `REJECT`

## ALLOW

次をすべて満たす場合のみ許可する。

- `Artifact Resolution Status = resolved`
- artifact と repository の対応が一次ソースで確認できている
- advisory source を確認済みで、未解決の Critical / High advisory がない
- 明確に危険な execution / privilege surface の兆候がない
- org policy 違反がない
- artifact が yanked / deprecated / unpublished でない
- 主要観点（identity/provenance、vulnerabilities、execution surface、release integrity）に unresolved unknown がない

## ALLOW_WITH_CONDITIONS

`Artifact Resolution Status = resolved` かつ明確な blocker が無いが、運用条件を付けることで採用可能な場合に使う。

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
- artifact と repository の対応が曖昧
- 外部ソース障害で主要信号が欠落
- ecosystem 判別が曖昧（monorepo 等）
- 利用文脈依存の高トレードオフ
- 権限やデータ影響が大きく、機械的に止めきれない

## REJECT

次のいずれかに当てはまる場合に使う。

- org policy 違反
- 対象 artifact に当たる未解決 Critical advisory
- 明確に危険な execution / privilege 挙動
- 信頼できない provenance（typosquatting、impersonation、publisher 整合性欠落）

## Hard Rules

次のいずれかに該当する場合は `ALLOW` を出さない。

- `Artifact Resolution Status != resolved`
- artifact と repository の対応が曖昧
- 対象 artifact (registry / marketplace の配布物) と repository source の対応が一次ソースで検証できない（例: tag / release / commit の紐付けが取れない、vsix と source の対応が取れない）
- advisory source 未確認
- 主要観点（identity/provenance、vulnerabilities、execution surface、release integrity）のいずれかに unresolved unknown が残る
- 対象 artifact が yanked / deprecated / unpublished
- supply-chain attestation がある ecosystem で attestation が欠落かつ publisher 整合が取れない

次に該当する場合は `ALLOW` と `ALLOW_WITH_CONDITIONS` を両方出さず、`NEEDS_HUMAN_REVIEW` 以下に倒す。

- repo-only 入力かつ artifact 未特定
- 複数 ecosystem 候補を推測で絞り込んだ場合

対象 artifact に当たる未解決の Critical 相当 advisory がある場合は `REJECT` を検討する。

## 降格ロジック（usage-context による厳格化）

降格 ladder は次の 3 段に固定する。`REJECT` は別系統で、降格では到達しない。

```
ALLOW → ALLOW_WITH_CONDITIONS → NEEDS_HUMAN_REVIEW
```

ベース判定（共通 8 観点と adapter 評価から導いた素の判定）に対し、次の高リスク条件ごとに 1 step の累積降格を適用する。適用する条件の数だけ step を進め、下限は `NEEDS_HUMAN_REVIEW`。

高リスク条件（各 1 step）:

- `production=true`
- `secrets_access=true`
- `data_sensitivity=high`
- `runtime ∈ {editor-extension, ci, cli}`

既定で降格なしとする組合せ:

- `runtime ∈ {library, build-tool, test-tool, node-server, browser}`
- `development` scope のみでの利用

例:

- base=`ALLOW`、`production=true` のみ → `ALLOW_WITH_CONDITIONS`
- base=`ALLOW`、`production=true` + `secrets_access=true` → `NEEDS_HUMAN_REVIEW`
- base=`ALLOW`、高リスク 3 条件以上 → `NEEDS_HUMAN_REVIEW`（floor）
- base=`ALLOW_WITH_CONDITIONS`、`production=true` のみ → `NEEDS_HUMAN_REVIEW`
- base=`NEEDS_HUMAN_REVIEW`、任意 → `NEEDS_HUMAN_REVIEW`（floor）

備考:

- 最保守既定値が採用された context も降格対象に含める。既定値を使った旨はレポートの「主要な判断理由」と「不確実性 / 未確認事項」に明記する
- 降格適用前後の値を「主要な判断理由」に 1 点として書く
