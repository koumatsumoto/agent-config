# GitHub issue へのミラー

計画本文の正本は issue。`.plan/` はその作業コピーにすぎない。

## 新規に出す

1. **Secret Check**（SKILL.md）を最終本文と issue title に当てる。検出したら issue 化せず止め、masking / 再生成をユーザへ依頼する
2. `gh` が使えて GitHub 管理 repo であることを確かめる。不能なら原因（未インストール / 未認証 / 非 GitHub repo / ネットワーク）を区別して報告し、`.plan/` 出力で止める
3. `gh issue create --title "<title>" --body-file <plan-file>` で全文ミラーする。title は計画タイトルから作る（Conventional Commits 互換だと後続 PR と揃う）。title に backtick / `$(...)` を含めない
4. 返された URL を `.plan/` 本文の placeholder に書き込み、`gh issue edit <number> --body-file <plan-file>` で再同期する

## 既存 issue を更新する

ユーザが issue 番号 / 既存 issue の更新を明示したときだけ扱う（例: "issue #25 に反映して" / `/km-plan 25`）。

`gh issue view` で対象を確認し、body に `<!-- km:plan:managed -->` があれば `--body-file` で更新してよい。marker が無ければ km-plan 管理外の可能性があるため、全文置換の前にユーザへ確認する。title は原則触らず、齟齬が大きいときだけ可否を確認してから変える。

## 反映後の再同期

修正を反映したら `.plan/` を更新し、**Secret Check を通してから** `gh issue edit <number> --body-file <plan-file>` で再同期する（外部レビュー結果には log・認証情報が混じりやすい）。再レビューが未収束のまま公開 issue を更新しない。
