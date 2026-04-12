# npm Package Security Review 出力形式

## サマリー（必ず冒頭に出力）

```md
## レビュー結果

**対象**: lodash@4.17.21
**Repository**: https://github.com/lodash/lodash
**最終判定**: ALLOW_WITH_CONDITIONS
**Review Confidence**: Medium
```

## 必須セクション

以下をこの順で出力する。

1. `レビュー対象`
2. `利用文脈`
3. `最終判定`
4. `主要な判断理由`
5. `カテゴリ評価`
6. `主要な指摘`
7. `必要条件`
8. `人間確認が必要な点`
9. `主要な証跡`
10. `不確実性 / 未確認事項`

## 指摘形式

主要指摘は以下の形式に揃える。

```md
## HIGH: install script に外部取得の兆候がある

**観点**: install / runtime behavior
**問題**: install 時に外部取得や shell 実行につながる挙動が疑われる。
**根拠**: package metadata の `scripts` と repository 上の関連 entry file を確認したところ、`postinstall` が定義されていた。確認日: 2026-04-12
**推奨対応**: 本番採用は避け、少なくとも install scripts を無効化できる環境に限定して再評価する。
```

## 記述ルール

- レポート本文は日本語で書く
- 判定理由は 2-4 点に絞る
- 証跡には URL と絶対日付を付ける
- `ALLOW_WITH_CONDITIONS` は実施可能な条件を書く
- `NEEDS_HUMAN_REVIEW` は不足情報と確認主体を書く
- 「安全である」と断定せず、「確認できた範囲では」と「未確認事項」を分ける
