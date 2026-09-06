# Third-Party OSS Security Review Framework

採用前に確認する共通8観点。括弧内の固定IDを保ち、日本語名で評価する。ecosystem固有の手順で補強する。

## 情報源と証跡

一次情報はGitHubのrepository・tags・releases・commits・SECURITY.md・Actions状態・Security Advisories、npmのregistry・package page・provenance、PyPIのproject page・JSON API・Trusted Publishersメタデータ、VS Code Marketplaceのlisting・API、raw manifest・metadata。OpenSSF Scorecard、deps.dev、GitHub Advisory Database APIは補助二次ソースとして分ける。
証跡にはURLと確認日（`YYYY-MM-DD`）を付ける。遡れない証跡は根拠にせずReview Confidenceを下げる。取得失敗は`unknown`とし、未確認事項と判定への影響を`decision-rules.md`に従って残す。

不在はアクセス可否と取得範囲を確かめて判断する。

- `404`だけでrelease / tag不在を断定しない。権限・URL等との区別がつかなければ取得失敗（`unknown`）とする。
- `GET /repos/{owner}/{repo}/releases/latest`は公開済みの非draft・非prereleaseが対象。正式releaseの不在をprereleaseや全tagの不在へ広げない。
- releases / tags一覧は、正常取得したアクセス範囲・フィルタ・ページを確認し、その範囲だけで不在を判断する。末尾の空ページだけでは全件不在としない。
- registry / marketplaceが明示した`yanked` / `deprecated` / `unpublished`は確定状態として扱う。

確認できた不在・公開状態は`unknown`と分けて「公開・配布の整合性」へ反映し、判定は`decision-rules.md`に従う。
GitHub仕様：[404の扱い](https://docs.github.com/en/rest/using-the-rest-api/troubleshooting-the-rest-api#404-not-found-for-an-existing-resource)、[latest releaseの対象](https://docs.github.com/en/rest/releases/releases#get-the-latest-release)。

## 1. 提供元と由来（`identity/provenance`）

registry / marketplaceの`repository`・`homepage`・publisher・maintainerから成果物とGitHubの対応を確かめ、入力URLとの矛盾、typosquatting・impersonation（類似名、作者や人気package派生の偽装）の兆候を確認する。

## 2. 既知の脆弱性（`vulnerabilities`）

GitHub Security Advisories・ecosystem固有advisory・deps.devで対象成果物を確認し、未解決Critical / High advisoryが対象version / tagに当たるか調べる。

## 3. 実行権限と影響範囲（`execution/privilege-surface`）

lifecycle hook（npm scripts、pip build backend、VS Code activationEvents）と主要entrypoint（bin、main、console_scripts等）を確認する。外部取得・通信、shell・子プロセス、自己更新、import時副作用、eval・動的読込、難読化blobを対象とする。`.pth`注入、`workspaceContains`広域起動、postinstallなど固有機構も確認する。

## 4. メンテナーとリポジトリの健全性（`maintainer/repo-health`）

最新release日・commit日と乖離、SECURITY policy、CI・release automation、メンテナ構成、最近のpublisher変更・所有者交代・コミット頻度の急変、未メンテ期間の方針適合を確認する。日付の乖離が大きい場合（目安1年以上）は、配布artifactに未反映の変更が累積している可能性を示す。

## 5. 依存関係と供給網（`dependency/supply-chain-surface`）

直接・任意・peer・ビルド依存の規模と用途に対する過剰さ、既知の問題を確認する。npm provenance・SLSA・PyPI Trusted Publishers・VS Code signing等の証明があるか、ある場合は対象成果物に有効かを確かめる。

## 6. 公開・配布の整合性（`release/distribution-integrity`）

yanked・deprecated・unpublished、version tagとGitHub tag / commitの対応、バイナリ・wheel・vsixとソースの対応、過去の公開停止・version hijackの兆候を確認する。

## 7. ライセンスと方針適合（`license/policy-fit`）

宣言ライセンス・SPDX・ソースツリーのLICENSEの整合と、社内禁止ライセンスへの該当を確認する。

## 8. 利用環境への影響（`usage-context-impact`）

production / development、実行形態（特にeditor-extension / ci / cliのIDE・実行基盤への権限）、`secrets_access=true`、`data_sensitivity=high`を反映する。高権限・高機密な文脈の厳格化は`decision-rules.md`に従う。
