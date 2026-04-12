# npm Package Security Review Checklist

単一 npm package の採用前レビューで確認する観点。

## 1. identity / provenance

- npm metadata の `repository`、`homepage`、publisher 情報を確認したか
- package と GitHub repository の対応が自然に説明できるか
- repository URL が任意入力で渡された場合、npm metadata と矛盾していないか
- 対応が曖昧、欠落、不整合なら `ALLOW` を止める

## 2. known vulnerabilities

- advisory source で対象 version を確認したか
- Critical / High の未解決 advisory があるか
- advisory 情報が取得不能なら `ALLOW` を止める

## 3. install / runtime behavior

- `scripts` に lifecycle scripts があるか
- `bin` や高リスク entry file に外部取得、shell 実行、自己更新、import 時副作用の兆候があるか
- install / runtime behavior が明確に危険なら `REJECT` を検討する

## 4. maintainer / repo health

- 最新 release 日を確認したか
- 最新 commit 日を確認したか
- `SECURITY.md` の有無を確認したか
- CI の有無を確認したか
- 利用方針に対して未メンテ期間が長すぎないか

## 5. dependency surface

- direct dependency 規模を確認したか
- optional / peer dependency の複雑さを確認したか
- 用途に対して依存が過剰でないか

## 6. license / policy fit

- declared license を確認したか
- 社内禁止ライセンスに該当しないか
- policy violation があるなら `REJECT` を検討する

## 7. usage-context impact

- `production` / `development` の違いを反映しているか
- runtime が `browser`、`cli`、`ci`、`node-server` のどれかでリスクの意味が変わるか
- `secrets_access` と `data_sensitivity` を判定に反映しているか
- 高権限、高機密な文脈では保守的に止めているか
