# VS Code Extension 確認手順

VS Code 拡張機能の採用前レビューで共通 8 観点に加えて確認する項目。`.vsix` のダウンロード・インストール・実行は行わず、Marketplace の掲載情報、`package.json` manifest、GitHub のソースツリーを静的に確認して判断する。

## 対象の特定

- `publisher.extension-id` と対象 version（Marketplace 上の正式 version）が特定できていること
- Marketplace listing と GitHub repository の対応を確認したこと

## Marketplace上の提供元

- Marketplace 上の publisher 名と GitHub organization / user の対応が自然か
- publisher が `Verified Domain` を保有しているか
- Marketplace 上の repository link と実 GitHub repository が一致するか
- 人気 extension 名の混同を狙う命名になっていないか

## 配布工程の注記

- Marketplace で配布される `.vsix` はビルド済みの成果物であり、インストール時に `scripts.postinstall` / `preinstall` / `prepare` などの npm スクリプトは実行されない。`package.json` の配布工程用スクリプトは開発者向けと見なし、拡張機能の実行時挙動を示す直接の証拠には使わない
- 静的解析の対象は「`.vsix` に実際に含まれる成果物」に置く。対応 tag / release が特定できればその commit、特定できない場合は master または最新 commit を暫定対象とし、その旨をレポートに明記する
- Marketplace version と GitHub tag / commit の対応を一次ソースで検証できない場合は、「配布の整合性」と `decision-rules.md` の必須判定規則（ソースとの対応を確認できなければ `ALLOW` と判定しない）を適用する

## サブディレクトリと language server の manifest

- extension が language server を同梱する場合（`vscode-languageclient` / `vscode-languageserver` に依存）、client 側と server 側で別プロセスが動作する
- ルートの `package.json` に加えて、`client/` / `server/` / `gclient/` / `gserver/` などのサブディレクトリにある `package.json` をすべて列挙し、それぞれの `dependencies` / `devDependencies` / `main` を「依存関係と供給網」と「実行権限と影響範囲」の両方に反映する
- サブディレクトリが存在するものの内容を取得できない場合は、その旨を「不確実性 / 未確認事項」に残し、`NEEDS_HUMAN_REVIEW` と判定する

## Marketplace 開示欠落

- Marketplace の掲載情報に license / privacy / telemetry の記載がない場合は、提供元の信頼性を判断する不確実要素として記録する
- license は repository 側の `LICENSE` / `package.json.license` で代替確認してよいが、Marketplace 表示欠落そのものは「不確実性 / 未確認事項」に残す
- Marketplace に `Verified Domain` バッジがない publisher は、提供元の信頼性を判断する不確実要素として記録し、確信度を下げる

## manifest（`package.json`）解析

- `main` / `activationEvents` / `contributes` / `capabilities` を確認する
- `activationEvents` に広域トリガ（`*`、`onStartupFinished`、`workspaceContains:**` 等）が使われていないか
- `contributes` が次に該当する場合は「実行権限と影響範囲」を高リスクとして扱う
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

bundler 出力だけが公開されている場合は、該当 bundle のソース（リポジトリ上）に遡って確認する。ソースを確認できなければ `NEEDS_HUMAN_REVIEW` と判定する。

## 依存 / 供給網

- `dependencies` / `devDependencies` を確認する。extension は通常 bundle されるため、bundled dependency の範囲も評価する
- 参照している大きなライブラリが extension 用途に対して過剰でないか
- Marketplace 側で signing 情報 / code signing の有無が表示されている場合はそれを確認する

## 配布の整合性

- 対象 version が Marketplace 上で unpublished / deprecated になっていないか
- 直近の version が publisher 変更や所有者変更を伴っていないか
- GitHub 上に対応 tag / release があるか

## 方針 / ライセンス

- `license` フィールドと LICENSE ファイルの整合
- 社内で許可されていない license でないか
- Marketplace 上の "Privacy" / "License" 記載と実 license が一致するか

## 判定への反映

- 上記の結果は、共通 8 観点のうち「提供元と由来」「実行権限と影響範囲」「依存関係と供給網」「配布の整合性」「ライセンスと方針適合」の証跡として使う
- `実行形態=editor-extension` は判定を厳しくする条件の対象なので、高リスクの兆候があれば「利用環境への影響」にも反映する
