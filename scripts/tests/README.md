# Tests

`scripts/cli.py` の `install`、`clean`、`verify`、`merge` と、ファイル操作ヘルパーを対象とする単体テスト。
サポート対象は Linux / macOS / Windows。

## 実行

`scripts/` をインポートの基点に指定して、テストを自動検出する。

```bash
# Linux / macOS
python3 -m unittest discover -s scripts/tests -t scripts
```

```powershell
# Windows
python -m unittest discover -s scripts/tests -t scripts
```

CI（[tests.yml](../../.github/workflows/tests.yml)）はPRごとに`ubuntu-latest`でPython 3.9 / 3.12 / 3.13の単体テストとシェルラッパーの基本動作を確認する。macOS / Windowsは`workflow_dispatch`でOSを指定した場合だけ実行する（`all`で全OS）。
