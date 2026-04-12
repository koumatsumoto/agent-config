# Routing Rubric

`km:review` と workflow skill の入口判定を評価する rubric。

## Pass 条件

- 期待した primary skill が最初の入口になる
- `should_not_trigger` に列挙した skill が入口にならない
- `km:review` が change type と conversation context に応じて child skill を選別する
- `km:review` が review level に応じて child skill を追加ではなく絞り込み方向に制御する
- `docs-only` で code/quality review を不必要に起動しない
- `config / chore` が未定義タイプとして扱われない
- `intent-review` を使えない場合、推測せず skip reason を明示する
- expert review が変更タイプと level の組み合わせに応じて正しく実行/スキップされる
- `thorough` が docs-only や config/chore/test-only を code/expert review に拡張しない

## Fail 条件

- 期待 skill が起動しない
- `should_not_trigger` に列挙した skill が起動する
- 下位 review skill をデフォルト入口として使ってしまう
- docs-only で code review に流れる
- code-only の docs update check が消える
- existing PR があるのに新規 PR を作ろうとする
- expert review が不要な変更タイプ（config/chore/test/docs-only）で実行される
- `quick` が quality-review や expert review を不要に残す

## 記録テンプレート

```md
### <scenario id>
- expected:
- actual:
- pass/fail:
- notes:
```
