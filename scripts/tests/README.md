# Tests

`scripts/cli.py`（install / clean / verify / merge と fs ヘルパ）の unittest。
サポート対象は Linux / macOS / Windows。

## 実行

`scripts/` を import のトップレベルに指定して discover する:

```bash
# Linux / macOS
python3 -m unittest discover -s scripts/tests -t scripts
```

```powershell
# Windows
python -m unittest discover -s scripts/tests -t scripts
```

CI (`.github/workflows/tests.yml`) は `ubuntu-latest` / `macos-latest` / `windows-latest` の Python 3.9 / 3.12 / 3.13 マトリクスで、unittest と bash wrapper の smoke test を実行する。
