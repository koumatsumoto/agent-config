---
name: km-third-party-oss-security-review
description: npm・Pythonパッケージ、VS Code拡張機能、GitHubリポジトリの採用前安全性を評価する。対象を明示した依頼で使う。
argument-hint: "[npm:pkg@ver | pip:pkg==ver | vscode:publisher.ext | <repo-url>]"
disable-model-invocation: true
---

# Third-Party OSS Security Review

GitHubでホストされる第三者OSSの社内採用可否を静的に評価する。対象を明示した依頼でだけ使い、差分・PRレビュー（`km-review`）、継続監視、動的解析、GitHub外のソース、closed-source binaryは扱わない。

## 入力と利用文脈

- npm：`name`、`name@version`、`@scope/name@version`。
- pip：`name`、`name==version`、`name@version`。
- VS Code：`publisher.extension-id`またはMarketplace URL。
- GitHub：`https://github.com/<owner>/<repo>`。任意で`@tag`または`#commit`を付ける。

必須の利用文脈は次のとおり。不足時は確認する。

- `production`：true（production）/ false（development）。
- `実行形態`：`node-server` / `browser` / `cli` / `build-tool` / `test-tool` / `ci` / `editor-extension` / `library`。
- `secrets_access`：true / false。
- `data_sensitivity`：low / medium / high。
- 社内ポリシー：禁止ライセンス、install scriptsの扱い、未メンテ許容期間。

確認不能で既定値が必要なら、`production=true`、`secrets_access=true`、`data_sensitivity=high`を使う。実行形態はnpm・pipなら`cli`、VS Codeなら`editor-extension`、GitHub入力ならecosystem解決後にその既定値を使う。既定値の採用は「不確実性 / 未確認事項」と「主要な判断理由」に明記する。

## 特定・評価・報告

referenceは必要になる直前に読み、解決したecosystem以外の確認手順は読まない。

1. registry / Marketplace入力からは配布成果物とGitHub repository、GitHub入力からはecosystemと配布成果物を特定する。npmは`reference/npm.md`、pipは`reference/pip.md`、VS Codeは`reference/vscode-extension.md`の特定要件に従う。
2. 収集前に`reference/review-framework.md`を読み、共通8観点をecosystem固有の確認結果で補強する。ソース間の不整合は統合せず報告する。
3. `reference/decision-rules.md`に従って判定し、利用文脈による厳格化を適用する。
4. `report-format.md`に従い、日本語で報告する。

`Artifact Resolution Status`は次の値にする。

- `resolved`：version / tag / commit / Marketplace versionのいずれかが一意。
- `candidate`：一次ソースで複数候補を列挙できる。
- `unresolved`：対象成果物を特定できていない。

複数候補を推測で絞らない。ecosystemが不明・曖昧ならecosystem referenceを読まず、特定できなくても判定・報告へ進む。許可しない条件は`reference/decision-rules.md`に従う。

## 安全境界

- install・execute・sandbox実行をせず、manifestとソースを静的に確認する。
- 最新の一次情報を根拠にし、補助情報と分ける。LLMの記憶、非公式mirror、信頼不明なblog、キャッシュだけを根拠にしない。
- HEADだけを配布成果物とみなさず、不確実な状態を`ALLOW`にしない。
- `gh`を必須依存にしない。
