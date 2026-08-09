# Third-Party OSS Security Review Framework

採用前レビューで確認する 8 観点。初出の括弧内は出力契約で使う固定 ID である。ecosystem を問わず日本語名で評価し、対象種別ごとの確認手順で補強する。

## 1. 提供元と由来（`identity/provenance`）

- registry / marketplace metadata の `repository` / `homepage` / publisher / maintainer 情報を確認したか
- 対象成果物と GitHub リポジトリの対応が一次ソースで自然に説明できるか
- repository URL が入力で渡された場合、registry metadata と矛盾していないか
- typosquatting / impersonation の兆候がないか（類似名、作者なりすまし、人気 package の派生を装う名前）
- 対応が曖昧、欠落、不整合なら `ALLOW` と判定しない

## 2. 既知の脆弱性（`vulnerabilities`）

- advisory の情報源（GitHub Security Advisories / ecosystem 固有 advisory / deps.dev）で対象成果物を確認したか
- 未解決の `Critical` / `High` advisory が対象 version / tag に当たるか
- advisory の情報源を取得できなければ `ALLOW` と判定しない
- 未解決 Critical が対象成果物に当たる場合は `REJECT` を検討する

## 3. 実行権限と影響範囲（`execution/privilege-surface`）

- lifecycle hook（npm `scripts`、pip build backend、VS Code `activationEvents`）に外部取得・shell 実行・自己更新の兆候があるか
- 主要 entrypoint（`bin`、`main`、`console_scripts`、extension `main`）に外部通信、子プロセス起動、import 時副作用、eval / 動的コード読み込み、難読化された blob の兆候があるか
- ecosystem 固有の高リスク機構（pip の `.pth` 注入、VS Code extension の `workspaceContains` 広域起動、npm の postinstall）を確認したか
- インストールや実行は行わず、manifest とソースツリーの静的確認で判断する
- 明確に危険な挙動があるなら `REJECT` を検討する

## 4. メンテナーとリポジトリの健全性（`maintainer/repo-health`）

- 最新 release 日と最新 commit 日を確認したか
- 最新 release 日と最新 commit 日の乖離を確認したか。大きな乖離（目安: 1 年以上）は「配布済 artifact に未反映の変更が累積している」可能性として記述する
- `SECURITY.md` / SECURITY policy の有無を確認したか
- CI / release automation の有無を確認したか
- メンテナ構成、最近の publisher 変更（突然の所有者交代、コミット頻度の急変）を確認したか
- 利用方針に対して未メンテ期間が長すぎないか

## 5. 依存関係と供給網（`dependency/supply-chain-surface`）

- 直接依存、任意依存、peer dependency、ビルド依存の規模を確認したか
- 依存が用途に対して過剰でないか
- 供給網の証明の有無を確認したか（npm provenance statement / SLSA / PyPI Trusted Publishers / VS Code signing 情報）
- 証明が存在する場合、対象成果物に対して有効か
- 依存関係に既知の問題があるパッケージが含まれていないか

## 6. 公開・配布の整合性（`release/distribution-integrity`）

- registry / marketplace 上で対象成果物が yanked / deprecated / unpublished にされていないか
- version tag と GitHub tag / commit の対応が取れるか
- リリースバイナリ / wheel / vsix とリポジトリのソースとの対応関係を確認できるか
- 過去リリースの公開停止や version hijack の兆候がないか
- `yanked` / `deprecated` / `unpublished` に該当するなら `ALLOW` と判定しない

## 7. ライセンスと方針適合（`license/policy-fit`）

- 宣言されたライセンスと SPDX 表記を確認したか
- 実際のソースツリーにある LICENSE ファイルと宣言されたライセンスが整合しているか
- 社内禁止ライセンスに該当しないか
- 方針違反があるなら `REJECT` を検討する

## 8. 利用環境への影響（`usage-context-impact`）

- `production` / `development` の違いを反映しているか
- `実行形態` の違いによってリスクの意味が変わるか（`editor-extension` / `ci` / `cli` は IDE / 実行基盤への権限影響が大きい）
- `secrets_access=true` と `data_sensitivity=high` を判定に反映しているか
- 高権限・高機密な文脈では保守的に止めているか（`decision-rules.md` の降格表に従う）
