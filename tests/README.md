# Tests

このディレクトリは、この repo にあるテスト資産の入口。

## 役割

- `tests/agent_config/`
  - `agent_config` インストーラ / クリーナ / 検証 / fs ヘルパ / settings.json マージの unittest (POSIX + Windows 両対応)
- `tests/scripts/`
  - レガシーの `scripts/merge-settings-json.py` ラッパー smoke test

## 実行

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
