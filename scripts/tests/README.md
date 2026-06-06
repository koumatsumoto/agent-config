# Tests

`scripts/cli.py`（install / clean / verify / merge と fs ヘルパ）の unittest。

## 実行

`scripts/` を import のトップレベルに指定して discover する（POSIX / Windows 共通）:

```bash
# POSIX
python3 -m unittest discover -s scripts/tests -t scripts
```

```powershell
# Windows (python3 が無いため python を使う)
python -m unittest discover -s scripts/tests -t scripts
```

CI (`.github/workflows/tests.yml`) は `ubuntu-latest` と `windows-latest` の Python 3.12 / 3.13 マトリクスで実行する。
