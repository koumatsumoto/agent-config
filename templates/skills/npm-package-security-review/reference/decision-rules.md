# npm Package Security Review Decision Rules

判定は次の 4 つに固定する。

- `ALLOW`
- `ALLOW_WITH_CONDITIONS`
- `NEEDS_HUMAN_REVIEW`
- `REJECT`

## ALLOW

以下をすべて満たす場合のみ許可する。

- exact version が特定されている
- package と repository の対応が確認できている
- advisory source を確認済みで、未解決の Critical / High advisory がない
- 明確に危険な install / runtime behavior がない
- org policy 違反がない
- 主要 unknown が残っていない

## ALLOW_WITH_CONDITIONS

明確な blocker はないが、運用条件が必要な場合に使う。

例:

- version pin が必要
- devDependency 限定
- install scripts を無効化できる環境に限定
- 利用用途や実行環境の制限が必要

## NEEDS_HUMAN_REVIEW

画一的に判定できない場合に使う。

- 証跡不足
- package と repository の対応が曖昧
- 外部ソース障害で主要信号が欠落
- 利用文脈依存の高トレードオフ
- 権限やデータ影響が大きく、機械的に止めきれない

## REJECT

次のいずれかに当てはまる場合に使う。

- org policy 違反
- 未解決 Critical advisory
- 明確に危険な install / runtime behavior
- 信頼できない provenance

## Hard Rules

- version 未特定では `ALLOW` を出さない
- package / repository 対応が曖昧なら `ALLOW` を出さない
- advisory source 未確認では `ALLOW` を出さない
- 主要 unknown が残るなら `ALLOW` を出さない
- production、`secrets_access=true`、`data_sensitivity=high` の場合は一段厳しく扱う
