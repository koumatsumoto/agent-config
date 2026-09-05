# Tests

配布CLIの`install`、`clean`、`verify`、`merge`とファイル操作、Skill helperの実行、HTMLテンプレートのbuild・CSP、文書の参照・一覧を検査する。自然言語の意味やAIの判断品質は、文字列検査の合格では保証しない。
CLIのサポート対象はLinux / macOS / Windows。OSや実行依存に制約があるテストは、条件を満たさなければskipする。

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
