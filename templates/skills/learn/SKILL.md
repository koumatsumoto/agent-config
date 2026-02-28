---
name: learn
description: Use when a session produced a reusable troubleshooting or implementation pattern worth saving as a skill.
disable-model-invocation: true
---

# Learn

現在のセッションから、再利用価値のあるパターンを手動抽出する。

## Use When

- 非自明な障害を解決した
- 今後も繰り返し発生し得る問題を整理したい
- チーム内で再利用可能な手順を残したい

## Extraction Criteria

- 問題の再現条件が明確
- 根本原因が説明できる
- 解決手順が一般化できる
- 将来の作業時間を削減できる

## Do Not Extract

- 単純なタイポ修正
- 一度限りの外部障害
- 背景説明だけで手順化できない内容

## Output Template

```markdown
---
name: <pattern-name>
description: <when to use and what it solves>
---

# <Pattern Title>

## Problem
<reproducible problem>

## Root Cause
<actual cause>

## Solution
<repeatable steps>

## Verification
<how to confirm success>
```

## Save Location

- 既定: `<skills-root>/learned/<pattern-name>/SKILL.md`
- 実運用では `continuous-learning/config.json` の保存先設定に合わせる
