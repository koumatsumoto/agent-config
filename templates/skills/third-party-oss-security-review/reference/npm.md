# npm Adapter

npm package の採用前レビューで共通 8 観点に加えて確認する項目。install / execute は行わず、registry metadata、raw `package.json`、GitHub ソース tree の静的確認だけで判断する。

## artifact 解決

- `name@version` が特定できていること。latest の暗黙採用は不可
- scoped name の場合は `@scope/name` 形式が正しく解釈できていること
- registry 上の version entry が存在し、`version`、`dist.tarball`、`dist.integrity`、`_npmUser`、`repository` を確認したこと

## registry metadata 整合性

- registry metadata 上の `repository.url` と GitHub repository の対応が取れるか
- `homepage`、`bugs`、`author`、`maintainers` が一致するか
- publisher が突如変わっていないか（publishers の履歴が参照可能な場合）

## lifecycle scripts

- `scripts` に `preinstall` / `install` / `postinstall` / `prepare` / `prepublish` の有無を確認する
- lifecycle script 内で外部取得（`curl`、`wget`、`fetch` 相当）、shell 実行、ソースの自動書き換え、難読化された blob 起動の兆候があるか
- 兆候がある場合は `execution / privilege surface` を高リスク側に振る

## entry surface

- `bin`、`main`、`module`、`exports` で公開される entry file を確認する
- entry file に外部通信、子プロセス起動、eval / `Function` / 動的 import、環境変数の exfil 兆候がないか
- TypeScript / bundler 出力の場合は対応するソースを repository 側で確認する

## 依存 / supply-chain

- `dependencies`、`peerDependencies`、`optionalDependencies`、`bundledDependencies` の範囲を確認する
- bundle された依存がある場合は bundle 経由でも typosquatting や危険 package が含まれないかを確認する
- npm provenance statement の有無を確認する。存在する場合、対象 version の statement が有効か
- provenance statement が ecosystem 的に期待できる新規 package で欠落している場合は保守側に倒す

## distribution integrity

- 対象 version が `deprecated` / `unpublished` になっていないか
- `dist.integrity` が登録されているか
- tag（`dist-tags`）と version の対応に不自然な変更がないか（例: `latest` の指す version が古い、直近に rollback されている）
- GitHub 上に対応 tag / release があるか

## policy / ライセンス

- `license` フィールドと LICENSE ファイルの整合性
- 社内禁止ライセンスに該当しないか

## 判定への反映

- ここで確認した結果は、共通 8 観点のうち `identity / provenance` / `execution / privilege surface` / `dependency / supply-chain surface` / `release / distribution integrity` / `license / policy fit` の証跡として使う
