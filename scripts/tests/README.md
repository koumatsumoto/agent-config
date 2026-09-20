# Tests

配布CLIの`install`、`clean`、`verify`、`merge`とファイル操作、Skill helperの実行、HTMLテンプレートのrender・CSP、文書の参照・一覧を検査する。自然言語の意味やAIの判断品質は、文字列検査の合格では保証しない。
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

km-reviewのNode helper testはNode.js 24以上で実行する。

```bash
node --test scripts/tests/test_prepare_review_helper.js
```

CI（[tests.yml](../../.github/workflows/tests.yml)）はPRごとに`ubuntu-latest`でPython 3.9 / 3.13 / 3.14の単体テストとシェルラッパーの基本動作を確認し、独立したjobでNode helper testも実行する。macOS / Windowsは`workflow_dispatch`でOSを指定した場合だけ実行する（`all`で全OS）。
