---
name: strategic-compact
description: Use when you want manual compact timing aligned with workflow phases instead of arbitrary auto-compaction.
---

# Strategic Compact

コンテキスト圧縮を「任意タイミング」ではなく「論理的区切り」で行うためのスキル。

## Use When

- 探索フェーズが終わって実装に移る
- 1 つのマイルストーンが完了した
- 文脈が肥大化し、次フェーズへ切り替えたい

## Recommended Timing

- 調査完了直後（実装開始前）
- バグ解決直後（次の課題へ移る前）
- 大きな設計判断の確定直後

## Hook Behavior

`suggest-compact.sh` は以下を行う:

1. セッション単位でツール呼び出し回数を追跡
2. 閾値到達で `/compact` を提案
3. 以後は一定間隔で再提案

## Hook Example

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "tool == \"Edit\" || tool == \"Write\"",
        "hooks": [
          {
            "type": "command",
            "command": "<skills-root>/strategic-compact/suggest-compact.sh"
          }
        ]
      }
    ]
  }
}
```

## Environment Variables

- `COMPACT_THRESHOLD` (default: `50`)
- `COMPACT_REMINDER_INTERVAL` (default: `25`)
- `COMPACT_COUNTER_STALE_SECONDS` (default: `21600`)
