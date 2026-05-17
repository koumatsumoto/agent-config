# Routing Rubric

`km:review` と関連 skill の入口判定および Phase 起動を評価する rubric。

## Pass 条件

- 期待した primary skill が最初の入口になる
- `km:review` が target / level / change composition に応じて Phase を選別する
- 引数パース (Phase 1a) が flag-first → token classify の順で動く
- `pr:<n>` / `<base>..<head>` / `<sha>` / `--repo <subtree>` / `--uncommitted` / level / `--skip-gating` のすべてが順序不問で解釈される
- 裸の数字 (`42` など) は曖昧入力として警告される (`km:github-workflow` の `[issue-number]` と混同しない)
- `docs-only` で Phase 2 / Phase 3 を起動せず Phase 4 full のみ実行する
- `code-only` で Phase 4 が need-check モードで起動する
- `config / chore` / `test` 単独で Phase 3 と Phase 4 を起動しない
- `thorough` が docs-only や config/chore/test-only を Phase 3 (3 専門家) に拡張しない
- `thorough` 指定時、3 専門家 (architect / qa / security) が **同一 turn 内に並列発行** される
- `--skip-gating` 指定時、CRITICAL/HIGH 残置でも Phase 進行ゲートをスキップする

## Fail 条件

- 期待 skill が起動しない
- 下位 Phase (`code-review.md` / `doc-review.md` / `experts/<role>.md`) を **slash skill として直接** 起動してしまう (これらは skill registry に登録されないため、本来起動できない)
- `docs-only` で Phase 2 / Phase 3 に流れる
- `code-only` で Phase 4 の need-check モードが起動しない
- `thorough` で Phase 3 が起動しない / 一部 expert しか起動しない
- 3 専門家が sequential 発行されている (並列発行されていない)
- `--skip-gating` 指定時に Phase 進行ゲートが動いている (escape されるべき)
- 裸の数字を target として解釈してしまう (`/km:review 42` が PR 42 を試行)
- `--repo` 単独で warning なくレビューを開始する (サブツリー指定が必要)
- existing PR があるのに新規 PR を作ろうとする (これは `km:github-workflow` 側の Pass 条件だが、`km:plan` 等から委譲される際に守られているか確認)

## 記録テンプレート

```md
### <scenario id>
- expected:
- actual:
- pass/fail:
- notes:
```
