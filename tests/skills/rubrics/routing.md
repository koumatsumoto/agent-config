# Routing Rubric

`km:review` と workflow skill の入口判定を評価する rubric。

## Pass 条件

- 期待した primary skill が最初の入口になる
- `should_not_trigger` に列挙した skill が入口にならない
- `km:review` が change type と conversation context に応じて child skill を選別する
- `docs-only` で code/quality review を不必要に起動しない
- `config / chore` が未定義タイプとして扱われない
- `intent-review` を使えない場合、推測せず skip reason を明示する
- expert review が変更タイプに応じて正しく実行/スキップされる（feat/refactor: 実行、config/chore/test/docs-only: スキップ、fix: 条件付き）

## Fail 条件

- 期待 skill が起動しない
- `should_not_trigger` に列挙した skill が起動する
- 下位 review skill をデフォルト入口として使ってしまう
- docs-only で code review に流れる
- code-only の docs update check が消える
- existing PR があるのに新規 PR を作ろうとする
- expert review が不要な変更タイプ（config/chore/test/docs-only）で実行される

## 記録テンプレート

```md
### <scenario id>
- expected:
- actual:
- pass/fail:
- notes:
```
