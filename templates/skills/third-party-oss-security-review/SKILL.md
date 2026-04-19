---
name: km:third-party-oss-security-review
description: Reviews a single third-party OSS artifact before internal adoption. Use when a specific npm / pip package, VS Code extension, or GitHub repository is identified and you need a security-focused intake review before approving its introduction. Not for code review, diff review, or continuous monitoring.
argument-hint: "[npm:pkg@ver | pip:pkg==ver | vscode:publisher.ext | <repo-url>]"
disable-model-invocation: true
---

# Third-Party OSS Security Review

GitHub でホストされる third-party OSS を社内採用する前のセキュリティレビュー。対象は採用可否判断のみで、未コミット差分レビューや PR レビューには使わない。

## Success Criteria

- 最新の一次情報だけを根拠に保守的に判定する
- 危険・不確実な artifact に誤って `ALLOW` を出さない
- ecosystem 固有の攻撃表面と利用文脈を判定に反映する
- 判定値、Review Confidence、主要証跡、未確認事項を日本語で明確に出力する

## Use When

- npm / pip / VS Code extension の採用可否を確認したい
- GitHub repository URL から採用判断材料を確認したい
- 利用文脈と社内ポリシーを踏まえた一次レビューを得たい

## Do Not Use

- 未コミット差分レビュー
- PR 差分レビュー
- 継続監視
- 動的解析や sandbox 実行
- GitHub 外の source host、closed-source binary 配布物（v1 非対応）
- `km:review` の代替

## Inputs

対応入力:

- npm package: `name`、`name@version`、scoped は `@scope/name@version` も可
- pip package: `name`、`name==version`、`name@version`
- VS Code extension: `publisher.extension-id`、または Marketplace URL
- GitHub repository URL: `https://github.com/<owner>/<repo>`（任意で `@tag` や `#commit` を追加）

必須の利用文脈:

- `production` / `development`
- `runtime`: `node-server` / `browser` / `cli` / `build-tool` / `test-tool` / `ci` / `editor-extension` / `library`
- `secrets_access`: true / false
- `data_sensitivity`: low / medium / high
- 社内ポリシー要点: 禁止ライセンス、install scripts の扱い、未メンテ許容期間

不足していれば確認する。確認できず既定値を採らざるを得ない場合は最保守の既定値を使う。

- 最保守既定: `production=true` / `secrets_access=true` / `data_sensitivity=high` / `runtime=cli`
- 既定値採用時はレポートの「不確実性 / 未確認事項」に明記する

## Workflow

1. Phase 1: 入力解釈と artifact 解決
2. **`report-format.md` と `reference/` 配下の全ファイルを Read する**
3. Phase 2: 一次情報の収集
4. Phase 3: 共通 8 観点の評価（`reference/review-framework.md`）
5. Phase 4: ecosystem-specific 評価（`reference/<ecosystem>.md`）
6. Phase 5: 判定（`reference/decision-rules.md`）
7. Phase 6: レポート生成（`report-format.md`）

## Phase 1: 入力解釈と artifact 解決

- registry / marketplace 由来の入力は `配布 artifact` と `GitHub repository` の両方を解決する
- repo URL 由来の入力は `ecosystem` と `配布 artifact` を解決する
- 複数候補が残る場合は推測しない。候補を列挙し `NEEDS_HUMAN_REVIEW` に倒す
- monorepo で `package.json` と `pyproject.toml` が併存する等、ecosystem 判別が曖昧な場合も `NEEDS_HUMAN_REVIEW` に倒す
- `配布 artifact` の特定度を次で表現し、`Artifact Resolution Status` として summary に出力する
  - `resolved`: version / tag / commit / marketplace version のいずれかが一意に解決済み
  - `candidate`: 複数候補があるが一次ソースで列挙できる
  - `unresolved`: artifact が解決できていない（repo-only 入力で tag が取れない等）
- `unresolved` のときは `ALLOW` も `ALLOW_WITH_CONDITIONS` も出さない。判定は `NEEDS_HUMAN_REVIEW` 固定。レポート冒頭で「採用判定ではなく repository-level の暫定評価」であることを明示する

## Phase 2: 一次情報の収集

許可する一次情報源:

- GitHub repository / tags / releases / commits / SECURITY.md / Actions 状態 / GitHub Security Advisories
- npm registry / npm package page / npm provenance statement
- PyPI project page / PyPI JSON API / PyPI Trusted Publishers メタデータ
- VS Code Marketplace listing / Marketplace API
- OpenSSF Scorecard、deps.dev、GitHub Advisory Database API（補助二次ソース）
- 必要に応じた raw manifest / raw metadata（`package.json` / `pyproject.toml` / extension `package.json` 等）

禁止事項:

- LLM の記憶だけを根拠にする
- 非公式 mirror、信頼不明な blog、キャッシュのみの情報
- install / execute / sandbox 実行
- `gh` コマンド必須依存
- HEAD のみを見て配布 artifact とみなす

ソース障害時のルール:

- registry / marketplace が取れない: `NEEDS_HUMAN_REVIEW`
- repository が解決できない、対応が曖昧: `ALLOW` は出さない
- advisory source が取得不能: `ALLOW` は出さない
- 一部証跡のみ失敗: `unknown` として残し、判定への影響を明記する

## Phase 3: 共通 8 観点

`reference/review-framework.md` に沿って次の 8 観点を評価する:

1. identity / provenance（typosquatting / impersonation を含む）
2. known vulnerabilities
3. execution / privilege surface（malicious behavior heuristics を含む）
4. maintainer / repo health
5. dependency / supply-chain surface（supply-chain attestation を含む）
6. release / distribution integrity（yanked / deprecated / unpublished を含む）
7. license / policy fit
8. usage-context impact

ソース間に不整合がある場合は無理に統合せず、不整合自体を report する。

## Phase 4: ecosystem-specific 評価

解決した ecosystem に対応する reference を適用する:

- npm → `reference/npm.md`
- pip → `reference/pip.md`
- VS Code extension → `reference/vscode-extension.md`

共通観点の一部は adapter 側の証跡で上書き／補強される。ecosystem-specific の判断結果は Phase 3 の該当観点に反映する。

## Phase 5: 判定

`reference/decision-rules.md` の hard rules と降格表に従う。

- blocker を先に判定する
- 未解決の Critical 相当 advisory が対象 artifact に当たる場合は `REJECT`
- hard rules のいずれかに抵触する場合は `ALLOW` 不可
- usage-context の高リスク条件に従って判定値を降格する

## Phase 6: レポート生成

`report-format.md` に沿って日本語レポートを出力する。

- 「安全である」と断定せず、「確認できた範囲では」と「未確認事項」を分ける
- `ALLOW_WITH_CONDITIONS` は対象 artifact が `resolved` の場合にのみ使い、運用可能な条件を書く
- 判定理由は原則 2-4 点。独立理由がそれ以上ある場合は主要理由に畳む
- `NEEDS_HUMAN_REVIEW` は不足情報と確認主体を明示する
- `REJECT` は拒否理由を `policy` / `vulnerability` / `provenance` / `behavior` / `privilege` に分類する
