---
name: config-review
description: >-
  Review CLAUDE.md, rules, skills, or agent definitions against
  best practices. Use when adding, modifying, or auditing
  Claude Code configuration files.
disable-model-invocation: true
---

# Config Review

設定ファイル (CLAUDE.md / Rules / Skills / Agents) をベストプラクティスに照らしてレビューする。

## Use When

- CLAUDE.md や rules を追加・変更した
- skills や agents の定義を新規作成・修正した
- 設定ファイル全体の品質監査をしたい

## Workflow

1. レビュー対象を特定する (`$ARGUMENTS` またはカレントディレクトリの設定ファイル)
2. 対象の種別を判定する (CLAUDE.md / Rule / Skill / Agent)
3. `references/review-checklist.md` の該当セクションでチェックする
4. `docs/claude-code-best-practices-2026.md` を参照基準として使う
5. 問題を重大度順に整理して報告する
6. 改善後の構成案を提示する

## Severity Guide

- `HIGH`: ベストプラクティスに明確に違反 (重複記載、上限超過、必須要素欠如)
- `MEDIUM`: 改善で品質向上が見込める (構成の最適化、@import 活用)
- `LOW`: 微小な改善 (表現の改善、順序の調整)

## Output Format

各指摘に以下を含める。

- 重大度
- 位置 (ファイル + 行)
- 問題の説明
- 推奨修正

レビュー末尾に改善後の構成案を提示する。

## References

- `references/review-checklist.md` - 設定種別ごとのチェックリスト
- `../../docs/claude-code-best-practices-2026.md` - ベストプラクティス参照基準
