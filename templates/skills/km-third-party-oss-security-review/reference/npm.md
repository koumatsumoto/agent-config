# npm の確認手順

npm パッケージの採用前レビューで共通 8 観点に加えて確認する項目。registry metadata、raw `package.json`、GitHubのソースツリーを確認する。

## 対象成果物の特定

- `name@version` が特定できていること。latest の暗黙採用は不可
- scoped name の場合は `@scope/name` 形式が正しく解釈できていること
- registry 上の version entry が存在し、`version`、`dist.tarball`、`dist.integrity`、`_npmUser`、`repository` を確認したこと

## registry metadata 整合性

- `homepage`、`bugs`、`author`、`maintainers` が一致するか
- publisher が突如変わっていないか（publishers の履歴が参照可能な場合）

## ライフサイクルスクリプト

- `scripts` に `preinstall` / `install` / `postinstall` / `prepare` / `prepublish` の有無を確認する
- ライフサイクルスクリプト内で外部取得（`curl`、`wget`、`fetch` 相当）、シェル実行、ソースの自動書き換え、難読化された blob 起動の兆候があるか
- 兆候がある場合は「実行権限と影響範囲」を高リスクとして扱う

## 公開される処理の入口

- `bin`、`main`、`module`、`exports` で公開される entry file を確認する
- entry file に外部通信、子プロセス起動、eval / `Function` / 動的 import、環境変数の exfil 兆候がないか
- TypeScript / bundler 出力の場合は対応するソースを repository 側で確認する

## 依存 / 供給網

- `dependencies`、`peerDependencies`、`optionalDependencies`、`bundledDependencies` の範囲を確認する
- bundle された依存がある場合は bundle 経由でも typosquatting や危険 package が含まれないかを確認する
- npm provenance statement の有無を確認する。存在する場合、対象 version の statement が有効か
- provenance statement が期待される新規パッケージで欠落している場合など、不確実性が残る場合は、より厳しい判定を選ぶ

## 配布の整合性

- `dist.integrity` が登録されているか
- tag（`dist-tags`）と version の対応に不自然な変更がないか（例: `latest` の指す version が古い、直近に rollback されている）
