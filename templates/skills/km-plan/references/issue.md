# GitHub issue へのミラー

## 新規に出す

1. `gh`が使えてGitHub管理リポジトリであることを確かめる。実行できない場合は、未インストール、未認証、GitHub管理外、ネットワーク障害を区別して報告し、`.plan/`への出力で止める
2. `gh issue create --title "<title>" --body-file <plan-file>`で全文を反映する。タイトルは計画タイトルから作り、バッククォートや`$(...)`を含めない
3. 返された URL を `.plan/` 本文の書き込み先へ入れ、`gh issue edit <number> --body-file <plan-file>` で再同期する

## 既存 issue を更新する

ユーザーがissue番号または既存issueの更新を明示したときだけ扱う（例: 「issue #25に反映して」 / `/km-plan 25`）。

`gh issue view` で対象を確認し、次の対応関係を確かめる。

- 本文に管理マーカー `<!-- km:plan:managed -->` があれば、`--body-file` で更新してよい
- 管理マーカーがなければkm-plan管理外の可能性があるため、全文置換の前にユーザーへ確認する
- `.plan/` の書き込み先にある issue URL と、更新対象の URL が一致していることを確認する
- タイトルは原則変更せず、本文との不一致が大きい場合だけ可否を確認してから変える

## 反映後の再同期

修正を反映したら `.plan/` を更新し、`gh issue edit <number> --body-file <plan-file>` で再同期する。本文には現在の設計理由と変更後の姿だけを残し、レビューの往復や改版の経緯は書かない（共有したいなら issue comment へ）。
