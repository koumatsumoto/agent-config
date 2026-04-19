# VS Code Extension Adapter

VS Code extension の採用前レビューで共通 8 観点に加えて確認する項目。`.vsix` のダウンロード・インストール・実行は行わず、Marketplace listing、`package.json` manifest、GitHub ソース tree の静的確認だけで判断する。

## artifact 解決

- `publisher.extension-id` と target version（Marketplace 上の正式 version）が特定できていること
- Marketplace listing と GitHub repository の対応を確認したこと

## Marketplace identity

- Marketplace 上の publisher 名と GitHub organization / user の対応が自然か
- publisher が `Verified Domain` を保有しているか
- Marketplace 上の repository link と実 GitHub repository が一致するか
- 人気 extension 名の混同を狙う命名になっていないか

## 配布 / lifecycle 注記

- Marketplace で配布される `.vsix` は pre-built された成果物であり、インストール時に `scripts.postinstall` / `preinstall` / `prepare` 等の npm lifecycle scripts は実行されない。`package.json` の lifecycle scripts は開発者向けと見なし、extension の runtime 挙動の証拠としては直接使わない
- 静的解析の対象は「`.vsix` に実際に含まれる成果物」に置く。対応 tag / release が特定できればその commit、特定できない場合は master または最新 commit を暫定対象とし、その旨をレポートに明記する
- Marketplace version と GitHub tag / commit の対応が一次ソースで検証できない場合は、`release / distribution integrity` と `decision-rules.md` の hard rule（source-correlation 未確認なら `ALLOW` 不可）を適用する

## subdir / language server manifest

- extension が language server を同梱する場合（`vscode-languageclient` / `vscode-languageserver` に依存）、client 側と server 側で別プロセスが動作する
- root の `package.json` に加えて、`client/` / `server/` / `gclient/` / `gserver/` 等の subdir `package.json` を全て列挙し、それぞれの `dependencies` / `devDependencies` / `main` を `dependency / supply-chain surface` と `execution / privilege surface` の両方に反映する
- subdir が存在するが内容が取得できない場合は、その旨を「不確実性 / 未確認事項」に残したうえで `NEEDS_HUMAN_REVIEW` 方向に倒す

## Marketplace 開示欠落

- Marketplace listing 上に license / privacy / telemetry の記載が無い場合は `identity / provenance` の signal として記録する
- license は repository 側の `LICENSE` / `package.json.license` で代替確認してよいが、Marketplace 表示欠落そのものは「不確実性 / 未確認事項」に残す
- Marketplace に `Verified Domain` バッジが無い publisher は identity/provenance の confidence を一段下げる

## manifest（`package.json`）解析

- `main` / `activationEvents` / `contributes` / `capabilities` を確認する
- `activationEvents` に広域トリガ（`*`、`onStartupFinished`、`workspaceContains:**` 等）が使われていないか
- `contributes` が次に該当する場合は `execution / privilege surface` を高リスクに倒す
  - `commands` がファイル書き換えや外部プロセス起動を伴う
  - `configuration` に secrets / tokens の保存を要求する
  - `languages` / `debuggers` / `taskDefinitions` / `terminal` を登録する
  - `jsonValidation` / `yamlValidation` の override で任意 URL を読み込む

## 実装挙動の静的推定

extension ソース（`src/` / `out/` 以下）で次の呼び出しの有無を確認する:

- `vscode.workspace.fs` や Node.js の `fs` / `child_process` による広域 I/O、外部プロセス起動
- `fetch` / `http` / `https` / `axios` 等による外部通信
- `vscode.authentication.getSession` 等による secrets access
- `FileSystemWatcher` の広域 watch、`onDidSaveTextDocument` 等での副作用
- 自己更新、extension 外 binary の download、IDE 外 shell 起動

bundler 出力だけが公開されている場合は、該当 bundle のソース（repository 上）に遡って確認する。確認不能な場合は `NEEDS_HUMAN_REVIEW` に倒す。

## 依存 / supply-chain

- `dependencies` / `devDependencies` を確認する。extension は通常 bundle されるため、bundled dependency の範囲も評価する
- 参照している大きなライブラリが extension 用途に対して過剰でないか
- Marketplace 側で signing 情報 / code signing の有無が表示されている場合はそれを確認する

## distribution integrity

- 対象 version が Marketplace 上で unpublished / deprecated になっていないか
- 直近の version が publisher 変更や所有者変更を伴っていないか
- GitHub 上に対応 tag / release があるか

## policy / ライセンス

- `license` フィールドと LICENSE ファイルの整合
- 社内で許可されていない license でないか
- Marketplace 上の "Privacy" / "License" 記載と実 license が一致するか

## 判定への反映

- 上記の結果は、共通 8 観点のうち `identity / provenance` / `execution / privilege surface` / `dependency / supply-chain surface` / `release / distribution integrity` / `license / policy fit` の証跡として使う
- `runtime=editor-extension` は降格表の対象なので、高リスク兆候があれば `usage-context impact` も強化する
