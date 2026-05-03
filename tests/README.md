# Tests

このディレクトリは、この repo にあるテスト資産の入口。

## 役割

- `tests/agent_config/`
  - `agent_config` インストーラ / クリーナ / 検証 / fs ヘルパ / settings.json マージの unittest (POSIX + Windows 両対応)
- `tests/skills/`
  - `templates/skills/` の静的 contract と canonical decision boundary を守る
- `tests/scripts/`
  - レガシーの `scripts/merge-settings-json.py` ラッパー smoke test
- `tests/docs/`
  - どの test をなぜ残すか、どの knowledge を rubric や docs に逃がしたかを説明する

この repo の skill テストは、実モデル eval ではなく **軽量な静的検証 + 必要時の手動 spot check** を前提にする。

## 読む順序

1. [tests/docs/skills-test-strategy.md](/home/kou/work/agent-config/tests/docs/skills-test-strategy.md)
2. [tests/docs/skills-test-catalog.md](/home/kou/work/agent-config/tests/docs/skills-test-catalog.md)
3. [tests/skills/README.md](/home/kou/work/agent-config/tests/skills/README.md)

## 実行

skill 静的検証 (POSIX 専用 — `bash` と `pyyaml` が必要):

```bash
python3 -c "import yaml"
bash scripts/verify-skill-tests.sh
python3 scripts/run-skill-tests.py list
python3 scripts/run-skill-tests.py dry-run --tag trigger
```

`agent_config` パッケージとレガシーラッパー両方の unittest (POSIX / Windows どちらでも):

```bash
# POSIX
python3 -m unittest discover -v
```

```powershell
# Windows (Windows には python3 コマンドが無いため python を使う)
python -m unittest discover -v
```

CI (`.github/workflows/tests.yml`) は `ubuntu-latest` と `windows-latest` の Python 3.12 / 3.13 マトリクスで unittest を実行する。
