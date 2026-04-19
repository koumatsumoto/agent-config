# Third-Party OSS Security Review Framework

採用前レビューで確認する 8 観点。ecosystem を問わず共通で評価し、adapter 側でさらに補強する。

## 1. identity / provenance

- registry / marketplace metadata の `repository` / `homepage` / publisher / maintainer 情報を確認したか
- artifact と GitHub repository の対応が一次ソースで自然に説明できるか
- repository URL が入力で渡された場合、registry metadata と矛盾していないか
- typosquatting / impersonation の兆候がないか（類似名、作者なりすまし、人気 package の派生を装う名前）
- 対応が曖昧、欠落、不整合なら `ALLOW` を止める

## 2. known vulnerabilities

- advisory source（GitHub Security Advisories / ecosystem 固有 advisory / deps.dev）で対象 artifact を確認したか
- 未解決の `Critical` / `High` advisory が対象 version / tag に当たるか
- advisory source が取得不能なら `ALLOW` を止める
- 未解決 Critical が対象 artifact に当たる場合は `REJECT` を検討する

## 3. execution / privilege surface

- lifecycle hook（npm `scripts`、pip build backend、VS Code `activationEvents`）に外部取得・shell 実行・自己更新の兆候があるか
- 主要 entrypoint（`bin`、`main`、`console_scripts`、extension `main`）に外部通信、子プロセス起動、import 時副作用、eval / 動的コード読み込み、難読化された blob の兆候があるか
- ecosystem 固有の高リスク機構（pip の `.pth` 注入、VS Code extension の `workspaceContains` 広域起動、npm の postinstall）を確認したか
- install / execute は行わず、manifest とソース tree の静的確認で判断する
- 明確に危険な挙動があるなら `REJECT` を検討する

## 4. maintainer / repo health

- 最新 release 日と最新 commit 日を確認したか
- `SECURITY.md` / SECURITY policy の有無を確認したか
- CI / release automation の有無を確認したか
- メンテナ構成、最近の publisher 変更（突然の所有者交代、コミット頻度の急変）を確認したか
- 利用方針に対して未メンテ期間が長すぎないか

## 5. dependency / supply-chain surface

- direct dependency、optional / peer / build dependency の規模を確認したか
- 依存が用途に対して過剰でないか
- supply-chain attestation の有無を確認したか（npm provenance statement / SLSA / PyPI Trusted Publishers / VS Code signing 情報）
- attestation が存在する場合、対象 artifact に対して有効か
- 依存 chain に既知の問題 package が含まれていないか

## 6. release / distribution integrity

- registry / marketplace 上で対象 artifact が yanked / deprecated / unpublished にされていないか
- version tag と GitHub tag / commit の対応が取れるか
- リリースバイナリ / wheel / vsix と repository source の対応関係を確認できるか
- 過去リリースの公開停止や version hijack の兆候がないか
- `yanked` / `deprecated` / `unpublished` に該当するなら `ALLOW` を止める

## 7. license / policy fit

- declared license と SPDX 表記を確認したか
- 実ソース tree の LICENSE ファイルと declared license が整合しているか
- 社内禁止ライセンスに該当しないか
- policy violation があるなら `REJECT` を検討する

## 8. usage-context impact

- `production` / `development` の違いを反映しているか
- `runtime` の違いによってリスクの意味が変わるか（`editor-extension` / `ci` / `cli` は IDE / 実行基盤への権限影響が大きい）
- `secrets_access=true` と `data_sensitivity=high` を判定に反映しているか
- 高権限・高機密な文脈では保守的に止めているか（`decision-rules.md` の降格表に従う）
