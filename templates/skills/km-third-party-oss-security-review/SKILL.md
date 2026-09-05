---
name: km-third-party-oss-security-review
description: npmパッケージ、Pythonパッケージ、VS Code拡張機能、GitHubリポジトリを採用前に安全性評価する。対象を明示した依頼で使う。
argument-hint: "[npm:pkg@ver | pip:pkg==ver | vscode:publisher.ext | <repo-url>]"
disable-model-invocation: true
---

# Third-Party OSS Security Review

GitHubでホストされる第三者OSSの社内採用可否を、対象の特定、根拠収集、評価、判定、報告の順に確認する。対象を明示した依頼でのみ使う。

未コミット差分・PRレビュー（`km-review`）、継続監視、動的解析、GitHub外のsource host、closed-source binary配布物は対象外。

## Inputs

対応入力:

- npm package: `name`、`name@version`、scoped は `@scope/name@version` も可
- pip package: `name`、`name==version`、`name@version`
- VS Code extension: `publisher.extension-id`、または Marketplace URL
- GitHub repository URL: `https://github.com/<owner>/<repo>`（任意で `@tag` や `#commit` を追加）

必須の利用文脈:

- `production`: true（production）/ false（development）
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

各referenceは必要になる直前に読む。**解決したecosystem以外の確認手順は読まない。**

1. **対象成果物の特定** — registry / marketplace入力からは配布対象成果物とGitHub repository、repo URLからはecosystemと配布対象成果物を解決する。npmなら`reference/npm.md`、pipなら`reference/pip.md`、VS Code extensionなら`reference/vscode-extension.md`を読み、各「対象成果物の特定」の要件を確認する
2. **根拠収集** — 収集前に`reference/review-framework.md`を読み、情報源の扱いと共通8観点に従って証跡を集める
3. **評価** — 共通8観点を、読み込み済みのecosystem固有の確認結果で補強・反映する。ソース間の不整合は無理に統合せず報告する
4. **判定** — `reference/decision-rules.md`の順序と利用文脈による厳格化に従う
5. **報告** — `report-format.md`に従って日本語レポートを出力する

### 特定結果

`Artifact Resolution Status`は次で表す。

- `resolved`: version / tag / commit / marketplace versionのいずれかが一意に解決済み
- `candidate`: 複数候補があるが一次ソースで列挙できる
- `unresolved`: 対象成果物が解決できていない（repo-only入力でtagが取れない等）

複数候補は推測で絞らず列挙する。ecosystem不明・曖昧（monorepoで複数種のmanifestが併存する場合など）ならecosystem referenceを読まない。特定できなくても判定・報告へ進み、許可しない条件は`decision-rules.md`を適用する。

## 安全境界

- install / execute / sandbox実行は行わない。manifestとソースを静的に確認する
- 最新の一次情報を根拠にし、補助情報と区別する。LLMの記憶だけ、非公式mirror、信頼不明なblog、キャッシュだけを根拠にしない
- HEADだけを配布対象成果物とみなさない
- 不確実な状態を`ALLOW`へ倒さない
- `gh`コマンドを必須依存にしない
