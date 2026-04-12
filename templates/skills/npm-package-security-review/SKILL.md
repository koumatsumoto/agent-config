---
name: km:npm-package-security-review
description: Reviews a single npm package for internal adoption risk. Use when a package or package@version is identified and you need a security-focused intake review before approval.
argument-hint: "[package[@version]]"
disable-model-invocation: true
---

# npm Package Security Review

単一 npm package の社内採用前レビューを行う。対象は package 受入判断であり、未コミット差分レビューや PR レビューでは使わない。

## Success Criteria

- 最新の一次情報だけを根拠にレビューする
- 危険な package に誤って `ALLOW` を出さない
- 判定理由、主要証跡、未確認事項を日本語で明確に出力する

## Use When

- npm package の社内採用可否を確認したい
- `package@version` が特定されている、または exact version を確認しながらレビューしたい
- 利用文脈と社内ポリシーを踏まえて一次レビューを出したい

## Do Not Use

- 未コミット差分レビュー
- PR 差分レビュー
- 継続監視
- 動的解析や sandbox 実行
- `km:review` の代替

## Inputs

最小入力は `package_name` または `package_name@version`。scoped package も許容する。

例:

- `lodash@4.17.21`
- `@angular/core@18.0.0`
- `@scope/pkg`

不足している場合だけ次を確認する:

- exact version
- 利用文脈
  - `production` / `development`
  - runtime: `node-server` / `browser` / `cli` / `build-tool` / `test-tool` / `ci`
  - `secrets_access`
  - `data_sensitivity`: `low` / `medium` / `high`
- 社内ポリシー要点
  - install scripts の扱い
  - 禁止ライセンス
  - 未メンテ許容期間など

GitHub repository URL は任意入力とし、npm metadata と矛盾する場合は provenance リスクとして扱う。

## Workflow

1. Phase 1: 入力確認
2. **`report-format.md` と `reference/` 配下の 2 ファイルを Read する**
3. Phase 2: 一次情報の収集
4. Phase 3: 7 観点の評価
5. Phase 4: 判定
6. Phase 5: レポート生成

## Phase 1: 入力確認

`$ARGUMENTS` から `package_name` と `version` を解釈する。version が未指定なら exact version を確認する。latest を暗黙採用してはならない。

利用文脈と社内ポリシー要点が不足している場合だけ追加確認する。

## Phase 2: 一次情報の収集

以下の一次情報だけを使う:

- npm registry / npm package page
- GitHub repository / releases / commits / SECURITY.md
- GitHub Security Advisories などの advisory source

取得手段は browse / fetch capabilities を優先し、`gh` コマンド、package install、package execution には依存しない。

収集順序:

1. npm metadata で package identity、version、repository、license、scripts、dependencies を確認する
2. npm metadata の repository / homepage / publisher 情報から GitHub repository を特定する
3. GitHub 上で最新 release 日、最新 commit 日、SECURITY.md、CI 状態を確認する
4. advisory source で対象 version の脆弱性を確認する

ソース障害時のルール:

- npm metadata が取れない: `NEEDS_HUMAN_REVIEW`
- repository が解決できない、存在しない、対応が曖昧: `ALLOW` は出さない
- advisory source が取得不能: `ALLOW` は出さない
- 一部証跡のみ取得失敗: `unknown` として残し、判定への影響を明記する

## Phase 3: 7 観点の評価

`reference/review-checklist.md` に沿って次を確認する:

- identity / provenance
- known vulnerabilities
- install / runtime behavior
- maintainer / repo health
- dependency surface
- license / policy fit
- usage-context impact

ソース間に不整合がある場合は無理に統合せず、不整合自体を report する。

## Phase 4: 判定

`reference/decision-rules.md` に沿って blocker を先に判定する。blocker がなければ `ALLOW_WITH_CONDITIONS` と `ALLOW` を検討する。

`ALLOW` を出してはいけない条件:

- exact version が未特定
- package / repository 対応が曖昧
- advisory source 未確認
- 主要 unknown が残る
- 未解決の Critical / High advisory がある

production、`secrets_access=true`、`data_sensitivity=high` の場合は一段厳しく扱う。

## Phase 5: レポート生成

`report-format.md` に沿って日本語レポートを出力する。

- 判定理由は 2-4 点に絞る
- 主要証跡は URL と絶対日付を付ける
- `ALLOW_WITH_CONDITIONS` は実施可能な条件を書く
- `NEEDS_HUMAN_REVIEW` は不足情報と確認主体を明示する
- 「安全である」と断定せず、「確認できた範囲では」と「未確認事項」を分ける
