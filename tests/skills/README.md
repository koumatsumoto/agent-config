# Skills Test Kit

`templates/skills/` の静的 contract と canonical decision boundary を検証するテスト資産。

設計方針は [tests/docs/skills-test-strategy.md](/home/kou/work/agent-config/tests/docs/skills-test-strategy.md)、case 一覧は [tests/docs/skills-test-catalog.md](/home/kou/work/agent-config/tests/docs/skills-test-catalog.md) を参照。

## 構成

- `manifest.yaml`
  - canonical case の一覧
- `scenarios/`
  - canonical case の fixture
- `rubrics/`
  - Tier 3 の人間向け判断基準
- `runs/`
  - 手動 spot check を残したいときの run sheet 保存先

## 何を守るか

- trigger の優先度
- `km:commit` を含む workflow entrypoint
- `km:review` の routing
- workflow / plan の safety boundary
- AGENTS / CLAUDE / repo README / skill metadata の drift

## 機械的整合チェック

```bash
python3 -c "import yaml"
bash scripts/verify-skill-tests.sh
```

## Runner

runner は manifest を読んで一覧表示と dry-run を行う。手動 spot check を残したい場合だけ scaffold を使う。

```bash
python3 scripts/run-skill-tests.py list
python3 scripts/run-skill-tests.py dry-run --tag review
python3 scripts/run-skill-tests.py scaffold --label smoke --client Codex --model gpt-5.4
```
