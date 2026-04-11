---
name: km:review
description: Reviews uncommitted changes end-to-end. Use when the user asks to review or check changes, or before commit. Prefer this skill over running review subskills one by one.
---

# Review

未コミット変更を対象に、intent/code/quality/doc-review をルーティングして統合するレビューオーケストレーター。レビュー系ではこれを既定の入口とし、下位 review skill は targeted review 用に扱う。

## Success Criteria

- 変更の種類に応じて必要なレビューだけを走らせる
- 下位レビューに同じ仕事を重複させない
- `CRITICAL` / `HIGH`、または intent-review の `HIGH` を見逃さずにブロックする
- 統合レポートは重複を減らし、次に何を直すべきかが分かる形にする

## Workflow

1. Phase 1: 変更把握とルーティング
2. Phase 2: intent-review 実行可否の判定
3. Phase 3: 必要な下位レビューの実行
4. Phase 4: 結果統合とコミット判定

## Phase 1: 変更把握とルーティング

`git diff --name-only` と `git diff --stat` で変更を把握し、以下を決める:

- 変更タイプ: `feat` / `fix` / `refactor` / `test` / `config` / `chore`
- 構成: `has_code` / `has_docs`
- 会話コンテキスト: 自己レビューか、第三者変更のレビューか
- 深度: `Full` / `Focused` / `Quick`

実行方針:

|変更の構成|intent-review|code-review|quality-review|doc-review|
|---|---|---|---|---|
|コード + ドキュメント（自己開発）|実行|実行|実行|実行|
|コード + ドキュメント（他者変更）|スキップ|実行|実行|実行|
|コードのみ（自己開発）|実行|実行|実行|更新必要性だけ確認|
|コードのみ（他者変更）|スキップ|実行|実行|更新必要性だけ確認|
|ドキュメントのみ|スキップ|スキップ|スキップ|実行|
|test / config / chore のみ|スキップ|Quick|Quick|スキップ|

## Phase 2: intent-review

会話履歴から要求を復元できる場合のみ `intent-review/SKILL.md` を使う。復元できない場合は推測せず、`intent-review skipped: no usable conversation context` と記録する。

intent-review の出力は以下の構造を維持する:

```md
### 要求リスト
1. [明示的] ...
2. [合意] ...

### 合意された設計判断
- ...
```

この構造化結果は、下位レビューの偽陽性フィルタリングに渡す。

## Phase 3: 下位レビュー

下位レビューには次の共通コンテキストを渡す:

- 変更ファイル一覧
- 変更タイプとレビュー深度
- intent-review の構造化結果（存在する場合のみ）

実行ルール:

- `intent-review`: `intent-review/SKILL.md` を読む
- `code-review`: `code-review/SKILL.md` を読んで担当範囲だけ実行する
- `quality-review`: `quality-review/SKILL.md` と `quality-review/quality-patterns.md` を読んで担当範囲だけ実行する
- `doc-review`: docs が変わるときだけ `doc-review/SKILL.md` を読んで実行する
- 並列実行できる環境では `code-review` / `quality-review` / `doc-review` を並列化する
- 各下位レビューは「重大度ごとの件数サマリー + 個別問題報告」で返させる

コードのみ変更では、フル doc-review はせず、少なくとも以下を確認する:

- パブリック API、CLI、設定、インターフェースの変更があるか
- `README.md`、`CLAUDE.md`、`AGENTS.md`、`docs/` に関連記述があるか
- 該当する場合は「ドキュメント更新推奨」を統合レポートに含める

下位レビューには Phase 1 をやり直させず、担当範囲だけを見させる。根拠の弱い推測、未変更行への一般論、単なる好みは報告させない。

## Phase 4: 結果統合

統合時のルール:

1. 重大度ごとの件数を合算する
2. 同一ファイル・近接行の類似指摘は重複の可能性を注記する
3. `CRITICAL` / `HIGH`、または intent-review の `HIGH` があれば `BLOCKED` とする
4. docs 更新推奨がある場合は末尾に独立セクションで追加する

出力形式は `report-format.md` を参照。
