# 統合と判定

先に`references/finding-contract.md`を読み、findingの採用・severity・blockingに適用する。メイン担当が全指摘の根拠を確認し、同じ原因と影響を統合する。レビュアの判定をそのまま採用しない。

## status

- `resolved`：以前のレビューで確定したfindingを、後続変更後のrecheckで解消済みと確認した
- `unresolved`：根拠が確定し、現在の対象では未修正
- `accepted-risk`：ユーザーが理由と条件を明示して受け入れた

誤検出・根拠不足は棄却し、最終件数に含めない。初回レビューの新規findingをその場で`resolved`にしない。

## レビューの判定

- `PASS`：必要なレビュー・検証が完了し、未解決blockerがない
- `BLOCKED`：未解決blocker、必要なレビュー・検証の未完了、または重大な不確実性がある
- `NOOP`：レビュー対象がない

## レポート

OSまたは実行環境の一時領域に実行ごとの一意なディレクトリを作り、`integration.md`を置く。固定パス・特定OSを前提にせず、リポジトリ、`.gitignore`、`.git/info/exclude`を変更しない。subagentへは絶対パスで渡し、一時ファイルをセッションをまたぐ正本にしない。

次を報告し、該当しない項目は省く。

- 対象・レビュー基準・変更概要、独立レビュアの構成と選択理由
- severity別件数とstatus内訳
- 各指摘のseverity・blocking・status・`file:line`・問題・成立経路と影響・根拠・最小の修正方針
- 未解決blockerを解消する最短方針、確認推奨、受け入れ済みリスク
- 実行した検証と判定

秘密情報・トークン・個人情報の値は引用しない。
