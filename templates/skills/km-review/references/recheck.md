# recheck（BLOCKED 後の再確認）

**新しいフルレビューではない。** 未解決 blocker が解消したか、その修正が material regression を持ち込んでいないか、の 2 点だけを見る限定レビュー。**著者自身の「直しました」を根拠に `PASS` にしない。**

## 起動できる条件

「直前の km-review が `BLOCKED` で、修正差分を伴う再依頼」と判断できること。判断材料は同一セッションの会話文脈、または `<report dir>/integration.md`（セッション境界に依存しない）。次のいずれかなら通常実行へ切り替え、その旨を明記する（陳腐化した所見を推測で使わない）:

- 未解決 blocker の一覧を入手できない
- `integration.md` の判定が `BLOCKED` でない（別 run に上書きされた疑い）
- 所見が対象差分と噛み合わない

## 実行

1. main が blocker を修正し、関連する検証を再実行する
2. `integration.md` から未解決 blocker と review anchor を読み、修正差分を確定する
3. blocker を所有する role の **fresh subagent 1 名**を起動する。独立した 2 群の blocker を 1 role で確認できないときだけ 2 名
4. main が統合して判定する（`references/verdict.md`）

recheck レビュアには**対象 blocker と修正差分を明示的に渡す**（初回の blind contract とは異なる）。見るのは次の 3 つだけ。

- 各 blocker の解消 / 未解消
- 修正 hunk が持ち込んだ新しい material blocker
- 修正で変わった隣接契約

**探索を広げない** — 無関係な既存領域、前回通過済みの領域、新しい LOW、修正と直接関係しない MEDIUM は見ない。修正 hunk 外の回帰をフル再実行と同等には見ないトレードオフで、ユーザはいつでもフル再実行を明示指定できる。

未解決 blocker がゼロになれば `PASS`（defer していたドキュメント同期があればここで実施して確定する）。**non-blocking finding のために次ラウンドへ進まない。**

同じ blocker が修正を重ねても解消しない、または設計トレードオフ・要件判断が必要な場合は、レビュアを足して解決したふりをしない。`BLOCKED` のまま、ユーザ判断が必要な論点と選択肢を提示する。

出力は `references/verdict.md` のレポート形式で、各 blocker を**解消済み / 未解消 / 新規**に区別する。未解消・新規には、サマリー件数とは別に個別の `file:line` を付す（位置情報を欠いた「新規 1 件」が積もると実体を追えなくなる）。
