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
