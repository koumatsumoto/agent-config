---
name: coding-standards
description: Use when writing or reviewing TypeScript/JavaScript/React/Node.js code and you need project coding standards.
---

# Coding Standards

このスキルは、実装やレビュー時に守るべき最小限のコーディング標準を提供する。
詳細な例や補足は参照ファイルへ分離し、ここでは判断基準だけを扱う。

## Use When

- TypeScript/JavaScript/React/Node.js の新規実装を行う
- 既存コードの改善やリファクタを行う
- レビュー時に規約逸脱を検知したい

## Core Workflow

1. 変更対象の言語・レイヤーを特定する
2. 必要な参照だけ読む（全体を一括で読まない）
3. 下記チェックリストを適用する
4. 指摘は「影響」「根拠」「修正案」をセットで返す

## Baseline Checklist

- 命名は役割が読める語彙を使う
- データ更新はイミュータブルをデフォルトにする
- エラーハンドリングは境界（I/O、外部 API、DB）で明示する
- ユーザー入力や外部入力は必ず検証する
- 関数は小さく保ち、深いネストを避ける
- ファイルは高凝集を維持する（目安 300 行、上限 800 行）

## Non-Goals

- 些末なスタイル差（空白、改行）を過剰に指摘しない
- 文脈依存の最適化を一律で強制しない
- ルール違反の列挙だけで終わらせない

## References

- `references/baseline.md` - 言語横断の具体例
- `../../rules/coding-style.md` - リポジトリ全体の既定ルール
