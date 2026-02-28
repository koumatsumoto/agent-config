---
name: continuous-learning
description: Use when you want to extract reusable patterns automatically from completed sessions.
---

# Continuous Learning

セッション終了時に再利用可能なパターンを抽出するためのスキル。
ここでは運用フローのみ定義し、細かい判定ロジックはスクリプトと設定ファイルに委譲する。

## Use When

- セッション終了時に学びを自動抽出したい
- 手動 `/learn` だけでは取りこぼしがある

## Workflow

1. Stop hook で `evaluate-session.sh` を 1 回実行する
2. メッセージ数と設定を確認して抽出可否を判定する
3. 抽出候補がある場合、保存先へ出力する

## Configuration

- `skills/continuous-learning/config.json`
- 主な設定値:
  - `min_session_length`
  - `learned_skills_path`
  - `patterns_to_detect`
  - `ignore_patterns`

## Hook Example

環境ごとのスキル配置先に合わせてコマンドパスを指定する。

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "<skills-root>/continuous-learning/evaluate-session.sh"
          }
        ]
      }
    ]
  }
}
```

## Notes

- セッションごとの抽出は軽量化のため終端でのみ実行する
- 些末な修正の自動抽出は避ける
- 抽出候補の品質は `/learn` と組み合わせて定期レビューする
