---
name: doc-review
description: Reviews uncommitted document changes with focus on intra-document structural consistency, cross-document coherence, and primary source verification. Use when the user asks to review docs or says "ドキュメントを確認して", "READMEをレビューして", "ドキュメントに問題ないか見て". Also triggers proactively after creating or updating documentation.
---

# Document Review

未コミットのドキュメント変更を対象に、整合性と正確性を重視したレビューを行う。

## Workflow

1. `git diff --name-only` で変更されたドキュメントファイルを収集する
2. 以下の3観点で順にレビューする
3. 問題を重大度順に報告する。`CRITICAL/HIGH` があればコミットをブロックする

## 重点レビュー観点

### 1. ドキュメント内整合性

変更差分だけでなく、変更されたドキュメントの全体を読む。部分的な追記・修正によって以下が崩れていないか検証する:

- セクション構成の論理的な流れ（順序、粒度の統一）
- 目次・見出しと実際の内容の対応
- ドキュメント内での用語・表記の統一
- 前後のセクションとの整合性（前提の矛盾、説明の重複・欠落）

### 2. ドキュメント間整合性

変更内容に関連する他のドキュメントを探索し、以下を検出する:

- 同じ情報が複数ドキュメントに重複して記載されていないか
- ドキュメント間で矛盾する記述がないか
- 一方を更新して他方が古いまま放置されていないか

### 3. 一次情報による正確性検証

IMPORTANT: ドキュメントの記述内容を鵜呑みにせず、一次情報まで遡って正確性を検証する。

- **システム仕様・API 仕様**: 実装コードを読んで記述と一致するか確認する
- **設定・コマンド**: 実際の設定ファイルやヘルプ出力と照合する
- **外部参照**: リンク先の存在と内容の妥当性を確認する

多少冗長になっても一次情報の確認を省略しない。
