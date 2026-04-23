# Tests

このディレクトリは、この repo にあるテスト資産の入口。

## 役割

- `tests/skills/`
  - `templates/skills/` の静的 contract と canonical decision boundary を守る
- `tests/docs/`
  - どの test をなぜ残すか、どの knowledge を rubric や docs に逃がしたかを説明する

この repo の skill テストは、実モデル eval ではなく **軽量な静的検証 + 必要時の手動 spot check** を前提にする。

## 読む順序

1. [tests/docs/skills-test-strategy.md](/home/kou/work/agent-config/tests/docs/skills-test-strategy.md)
2. [tests/docs/skills-test-catalog.md](/home/kou/work/agent-config/tests/docs/skills-test-catalog.md)
3. [tests/skills/README.md](/home/kou/work/agent-config/tests/skills/README.md)

## 実行

```bash
python3 -c "import yaml"
bash scripts/verify-skill-tests.sh
python3 scripts/run-skill-tests.py list
python3 scripts/run-skill-tests.py dry-run --tag trigger
```
