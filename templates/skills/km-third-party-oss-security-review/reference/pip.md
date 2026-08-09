# pip の確認手順

pip（PyPI）パッケージの採用前レビューで共通 8 観点に加えて確認する項目。インストール、ビルド、実行は行わず、PyPI JSON API、sdist / wheel メタデータ、GitHub のソースツリーを静的に確認して判断する。

## 対象成果物の特定

- `name==version` または `name@version` が特定できていること。latest / `>=x` の暗黙採用は不可
- PyPI 上の release が存在し、`info.version`、`info.home_page`、`info.project_urls`、`urls[]` を確認したこと
- sdist / wheel が両方存在する場合は両方の metadata を確認する

## PyPI metadata 整合性

- PyPI metadata 上の `Home-page` / `project_urls`（`Source`、`Repository`）と GitHub repository の対応が取れるか
- `Author` / `Maintainer` / `License` 情報が GitHub 上の表記と整合するか
- PyPI Trusted Publishers が使われているか、使われている場合 GitHub Actions のワークフローは対象 repository の管理下にあるか

## ビルドバックエンドとライフサイクル

- `pyproject.toml` の `build-system.requires` と `build-system.build-backend` を確認する
- `setup.py` が存在する場合、import 時コード実行、外部取得、環境変数参照の兆候がないか
- ビルド時に実行される custom script（`cffi`、`cython`、`meson` 等）が安全な範囲に収まっているか
- `.pth` ファイルをインストールするパッケージは site-packages に広域副作用を与えるため、理由と内容を確認する

## 公開される処理の入口

- `[project.scripts]` / `[project.gui-scripts]` / `console_scripts` で公開される entry を確認する
- 主要 module の `__init__.py` / entry module に外部通信、subprocess 呼び出し、eval / `exec` / 動的 import、難読化 blob の兆候がないか
- ネイティブ拡張（C / Rust / Cython）を含む場合は「実行権限と影響範囲」を一段高いリスクとして扱う

## 依存関係と供給網

- `dependencies`、`optional-dependencies`、`extras` の範囲を確認する
- `requires-dist` と PyPI 側で表示される依存が一致するか
- 依存 chain に既知の問題 package が含まれていないか
- SLSA / in-toto attestation が公開されている場合、対象 version に対して有効か

## 配布の整合性

- 対象 version が yanked になっていないか（`yanked` / `yanked_reason` を確認）
- wheel / sdist の hash（`sha256`）が PyPI 上で参照できるか
- version tag と GitHub tag / commit の対応が取れるか
- GitHub Release の tarball と PyPI 上の sdist 内容が大きく乖離していないか

## 方針とライセンス

- `license` フィールド、classifier、LICENSE ファイルの整合性
- GPL 系ライセンスと社内方針の適合を確認する

## 判定への反映

- ここで確認した結果は、共通 8 観点のうち「提供元と由来」「実行権限と影響範囲」「依存関係と供給網」「公開・配布の整合性」「ライセンスと方針適合」の証跡として使う
- ネイティブ拡張 / `.pth` 注入 / ビルド時ネットワーク取得のいずれかを確認した場合は、「利用環境への影響」でさらに厳しい判定を選ぶ
