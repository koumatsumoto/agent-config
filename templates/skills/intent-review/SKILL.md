---
name: km:intent-review
description: Verifies that uncommitted changes satisfy the user's original request and agreed design decisions. Use only when the relevant conversation context exists.
disable-model-invocation: true
---

# Intent Review

会話履歴をもとに、未コミット変更が最初の依頼と合意済み判断を満たしているか確認する。

## Success Criteria

- 明示要求と合意事項を構造化して復元する
- 推測と事実を分ける
- 実装漏れ、スコープ外変更、合意違反を見落とさない

## いつ実行するか

- 自分がこの会話で実装した変更: 実行する
- 他者の変更レビュー、または会話文脈が使えない場合: スキップする

要求が十分に復元できない場合は、推測せずスキップ理由を明記する。

## Workflow

1. 変更の対象と規模を把握する
2. 会話履歴から要求を復元する
3. 変更内容と照合する
4. 偽陽性を落として報告する

## Phase 1: 変更把握

`git diff --name-only` と `git diff --stat` で変更ファイルと規模を把握する。

## Phase 2: 要求の復元

要求は次の 3 区分で整理する:

- **明示的な要求**: ユーザーが直接依頼した内容
- **合意された設計判断**: 会話で明示的に決めた方針
- **暗黙的な期待**: 文脈から合理的に推測した内容

構造化出力は次を維持する:

```md
### 要求リスト
1. [明示的] ...
2. [合意] ...
3. [暗黙的/推測] ...

### 合意された設計判断
- ...
```

## Phase 3: 充足判定

以下を確認する:

- 実装漏れ
- スコープ外変更
- 境界条件の考慮漏れ
- 回帰的影響
- 合意事項との不整合

## Phase 4: 偽陽性フィルタリング

以下は除外する:

- 明示的に延期または除外された項目
- 段階実装として合意済みの未実装部分
- ユーザーが限定したスコープ外の要求

## 判定

- `HIGH`: 明示要求の未実装、合意事項との不整合
- `MEDIUM`: スコープ外変更、境界条件の考慮漏れ
- `LOW`: 暗黙的期待への未対応

`HIGH` があればコミットをブロックする。出力形式は `report-format.md` を参照。
