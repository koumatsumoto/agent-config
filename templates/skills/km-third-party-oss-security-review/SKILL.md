---
name: km-third-party-oss-security-review
description: npmパッケージ、Pythonパッケージ、VS Code拡張機能、GitHubリポジトリを採用前に安全性評価する。対象を明示した依頼で使う。
argument-hint: "[npm:pkg@ver | pip:pkg==ver | vscode:publisher.ext | <repo-url>]"
disable-model-invocation: true
---

# Third-Party OSS Security Review

GitHub でホストされる第三者製 OSS を社内採用する前のセキュリティレビュー。対象は採用可否の判断に限り、未コミット差分や PR のレビューには使わない。対象の特定、根拠収集、評価、判定、報告の順に進める。

## Success Criteria

- 最新の一次情報だけを根拠に保守的に判定する
- 危険または不確実な対象成果物を誤って `ALLOW` と判定しない
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
- `km-review` の代替

## Inputs

対応入力:

- npm package: `name`、`name@version`、scoped は `@scope/name@version` も可
- pip package: `name`、`name==version`、`name@version`
- VS Code extension: `publisher.extension-id`、または Marketplace URL
- GitHub repository URL: `https://github.com/<owner>/<repo>`（任意で `@tag` や `#commit` を追加）

必須の利用文脈:

- `production` / `development`
- `実行形態`: `node-server` / `browser` / `cli` / `build-tool` / `test-tool` / `ci` / `editor-extension` / `library`
- `secrets_access`: true / false
- `data_sensitivity`: low / medium / high
- 社内ポリシー要点: 禁止ライセンス、install scripts の扱い、未メンテ許容期間

不足していれば確認する。確認できず既定値を採らざるを得ない場合は最保守の既定値を使う。

- 最保守既定値 (確認不能時の fallback)
  - `production=true`
  - `secrets_access=true`
  - `data_sensitivity=high`
  - `実行形態`: ecosystem 別に設定する
    - npm → `cli`
    - pip → `cli`
    - vscode-extension → `editor-extension`
    - github-repo → ecosystem 解決後の既定値に従う
- 既定値採用時はレポートの「不確実性 / 未確認事項」と「主要な判断理由」に明記する

## Workflow

各 reference は、その内容が必要になる直前に Read する。**解決した ecosystem の対象種別ごとの確認手順以外は読まない** — 対象外 ecosystem の判断基準を載せると、審査に無関係な観点が判定に混入する。

1. **第1段階: 入力解釈と対象成果物の特定** — ecosystem を判別したら `reference/<ecosystem>.md` を Read し、その「対象成果物の特定」節の要件を満たす形で対象成果物を確定する
2. **第2段階: 一次情報の収集** — 収集を始める前に `reference/review-framework.md` を Read する（8 観点が収集すべき証跡を規定するため、後から読むと再収集になる）
3. **第3段階: 共通 8 観点の評価** — `reference/review-framework.md`（第2段階で読み込み済み）
4. **第4段階: 対象種別ごとの評価** — `reference/<ecosystem>.md`（第1段階で読み込み済み）
5. **第5段階: 判定** — `reference/decision-rules.md` を Read する
6. **第6段階: レポート生成** — `report-format.md` を Read する

ecosystem を判別できない場合は対象種別ごとの確認手順を読まず、`NEEDS_HUMAN_REVIEW` と判定する（第1段階）。

## 第1段階: 入力解釈と対象成果物の特定

- registry / marketplace 由来の入力は `配布対象成果物` と `GitHub repository` の両方を解決する
- repo URL 由来の入力は `ecosystem` と `配布対象成果物` を解決する
- 複数候補が残る場合は推測せず、候補を列挙して `NEEDS_HUMAN_REVIEW` と判定する
- monorepo で `package.json` と `pyproject.toml` が併存するなど、ecosystem 判別が曖昧な場合も `NEEDS_HUMAN_REVIEW` と判定する
- ecosystem を判別できたら `reference/<ecosystem>.md` を Read し、その「対象成果物の特定」節の要件（version の特定、名前形式の解釈、registry / marketplace entry で確認する項目）を満たしてから特定度を判定する
- `配布対象成果物` の特定度を次で表現し、`Artifact Resolution Status` としてサマリーに出力する
  - `resolved`: version / tag / commit / marketplace version のいずれかが一意に解決済み
  - `candidate`: 複数候補があるが一次ソースで列挙できる
  - `unresolved`: 対象成果物が解決できていない（repo-only 入力で tag が取れない等）
- `unresolved` のときは `ALLOW` も `ALLOW_WITH_CONDITIONS` も出さない。判定は `NEEDS_HUMAN_REVIEW` 固定。レポート冒頭で「採用判定ではなく repository-level の暫定評価」であることを明示する

## 第2段階: 一次情報の収集

収集した証跡は URL と確認日（`YYYY-MM-DD`）とともに記録する。後から遡れない証跡はレポートの根拠に使えず、`Review Confidence` を下げる。

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
- HEAD のみを見て配布対象成果物とみなす

ソース障害時のルール:

- registry / marketplace が取れない: `NEEDS_HUMAN_REVIEW`
- repository が解決できない、対応が曖昧: `ALLOW` は出さない
- advisory source が取得不能: `ALLOW` は出さない
- 一部の証跡だけ取得に失敗: `unknown` として残し、未確認であることと判定への影響を明記する

ソースが「不在」を明示した場合の扱い:

- `GET /releases/latest` や `GET /tags` が `404` / 空配列を返した場合は「取れない」ではなく「release / tag 不在」という確定的 negative evidence として `公開・配布の整合性` に反映する
- registry / marketplace 上で対象 version が `yanked` / `deprecated` / `unpublished` と明示された場合も確定的 negative evidence として扱う
- 上記は `unknown`ではないので、確証として判定ロジックに載せる

## 第3段階: 共通 8 観点

`reference/review-framework.md` に沿って次の 8 観点を評価する:

1. 提供元と由来（typosquatting / impersonation を含む）
2. 既知の脆弱性
3. 実行権限と影響範囲（悪意ある挙動の兆候を含む）
4. メンテナーとリポジトリの健全性
5. 依存関係と供給網（供給網の証明を含む）
6. 公開・配布の整合性（yanked / deprecated / unpublished を含む）
7. ライセンスと方針適合
8. 利用環境への影響

ソース間に不整合がある場合は無理に統合せず、不整合自体を report する。

## 第4段階: 対象種別ごとの評価

第1段階で Read した対象種別ごとの確認手順を適用する:

- npm → `reference/npm.md`
- pip → `reference/pip.md`
- VS Code extension → `reference/vscode-extension.md`

共通観点の一部は対象種別ごとの確認手順にある証跡で上書きまたは補強される。対象種別ごとの判断結果は第3段階の該当観点に反映する。

## 第5段階: 判定

`reference/decision-rules.md` を Read し、必須判定規則と判定を厳しくする条件に従う。

- blocker を先に判定する
- 未解決の Critical 相当 advisory が対象成果物に当たる場合は `REJECT`
- 必須判定規則のいずれかに抵触する場合は `ALLOW` と判定しない
- 利用条件の高リスク条件に従って、より厳しい判定を選ぶ

## 第6段階: レポート生成

`report-format.md` を Read し、それに沿って日本語レポートを出力する。

- 「安全である」と断定せず、「確認できた範囲では」と「未確認事項」を分ける
- `ALLOW_WITH_CONDITIONS` は対象成果物が `resolved` の場合にのみ使い、運用可能な条件を書く
- 判定理由は原則 2-4 点。独立理由がそれ以上ある場合は主要理由に畳む
- `NEEDS_HUMAN_REVIEW` は不足情報と確認主体を明示する
- `REJECT` は拒否理由を `policy` / `vulnerability` / `provenance` / `behavior` / `privilege` に分類する
