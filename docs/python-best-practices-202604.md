# Pythonベストプラクティス 2026-08

> 参考資料。実行時契約ではない。言語固有のcoding styleはAIの判断と対象リポジトリの設定に委ねる。
>
> 確認日: 2026-08-09

Python 3.14.6、Pyright、Ruffの公式情報を基準に、Pythonの静的品質と保守性に必要な判断を整理した。

## 参照した一次情報

- What’s New in Python 3.14
- Python 3.14 `typing`
- Python 3.14 `asyncio`
- Pyright configuration
- Ruff configuration

## 1. ベースライン

- 新規コードの検討基準はPython 3.14。実際の最低対応版は対象プロジェクトに従う
- 型検査は Pyright を基準にする
- lint / format は Ruff を基準にする
- 新規コードは `list[str]` のような組み込みジェネリック型を使い、旧 `typing.List` などは持ち込まない
- `Any` は境界面に限定し、内部実装へ漏らさない

## 2. 型チェック

- 新規コードは `typeCheckingMode = "strict"` を第一候補にする
- `pythonVersion` は実際の最低サポート版に固定する
- `pyproject.toml` の `[tool.pyright]` か `pyrightconfig.json` のどちらか一方を正本にする
- `strict` 運用時は `reportMissingTypeStubs`、`reportDeprecated`、`reportPrivateUsage` などの診断を積極的に有効化する
- `strictListInference`、`strictDictionaryInference`、`strictSetInference` は混在型の推論を緩めたくないときに有効

### 推奨例

```toml
[tool.pyright]
pythonVersion = "3.14"
typeCheckingMode = "strict"
reportDeprecated = "error"
reportUnnecessaryTypeIgnoreComment = "error"
```

## 3. typing の実務指針

- 型エイリアスは `type` 文を優先する
- 呼び出し可能型は`collections.abc.Callable`を使う
- 構造的部分型には`Protocol`を使い、不要な継承を減らす
- `TypedDict`、`Protocol`、`Literal`、`TypeGuard`、`TypeIs`などを使って型を絞り込み、境界の曖昧さを減らす
- `object` と `Any` を区別する。未知だが安全に扱いたい値は `object`
- `typing`の非推奨の別名は避け、`collections.abc`や組み込みジェネリック型へ寄せる

## 4. Python 3.14 で押さえる点

- Python 3.14では annotations の実行時の挙動が deferred evaluation ベースに変わった。annotation を読む側は `__annotations__` 直読みではなく `annotationlib` や対応 API を前提に設計する
- 前方参照のためだけの文字列化は減らせるが、`from __future__ import annotations` を使う既存コードの挙動自体は 3.14 でも変わらない。書き手側の移行と、annotation を読むライブラリ側の対応は分けて考える
- template string literals、標準ライブラリの更新、`compression.zstd` などの 3.14 追加機能は「必要な場面でだけ」使う
- 3.14 の機能を使うなら、ツールチェーンとデプロイ環境も同じ最低バージョンに揃える

## 5. 関数とデータモデル

- 関数境界では入出力型を省略しない
- `dataclass(slots=True)`、`frozen=True`、`kw_only=True` は不変性と API 明確化に有効
- validation や正規化が複雑ならコンストラクターに詰め込まず、専用の生成関数または解析関数を切る
- 戻り値は `dict[str, Any]`より名前付きデータ構造を優先する
- 例外で表現すべき失敗と `None` / `Result` で表現すべき失敗を混ぜない

## 6. 例外とエラー処理

- `except Exception:` は境界でのみ使い、内部実装では具体的な例外を捕まえる
- 例外を握り潰さず、再送出時は文脈を足す
- ライブラリ境界ではドメイン例外へ変換して表に出す
- 非同期並列処理では `ExceptionGroup` と `except*` を前提に設計する

## 7. asyncio

- 複数タスクのライフサイクル管理には `asyncio.TaskGroup` を優先する
- 完了を待たない処理を避け、キャンセルと失敗伝播の責務を明示する
- timeout は呼び出し側の契約として持たせる
- I/O 境界では async と sync を混在させない
- introspection が必要なら 3.14 時点の `asyncio` 追加機能を前提にするが、監視用途と本処理を分離する

## 8. Ruff

- Ruff を formatter と linter の単一入口として使う
- 設定は `pyproject.toml`、`ruff.toml`、`.ruff.toml` のいずれかに寄せる
- Ruff は親設定を自動マージしない。継承が必要なら `extend` を使う
- ノートブックも対象に入るため、除外方針を明示する

### 推奨例

```toml
[tool.ruff]
target-version = "py314"
line-length = 88

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "ANN", "SIM", "RUF"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
```

### 実務上の指針

- `UP` で古い構文を残さない
- `B`、`SIM`、`RUF` はバグ温床の検出に効く
- `ANN`は公開APIの型注釈を強制したいときに有効
- formatter 導入時は Black 互換前提を理解したうえで一本化する

## 9. 避けるもの

- `typing.List`, `typing.Dict`, `typing.Text` などの旧 alias
- `Any` の無制限な伝播
- 型注釈のない公開関数
- 例外を握り潰す広すぎる例外捕捉
- `asyncio.create_task()` を投げっぱなしにする設計
- 複数ツールに分かれた lint / format / import sort の過剰分散

## 10. 最小チェックリスト

- 最低 Python 版と `pythonVersion` が一致しているか
- strict type checking を前提にできるか
- 組み込みジェネリック型 / `collections.abc` に寄っているか
- `TaskGroup` と cancellation を前提に非同期処理を書いているか
- Ruff の責務が formatter / lint で分裂していないか

## 出典

- https://www.python.org/downloads/release/python-3146/
- https://docs.python.org/3.14/whatsnew/3.14.html
- https://docs.python.org/3.14/library/typing.html
- https://docs.python.org/3.14/library/asyncio-task.html
- https://github.com/microsoft/pyright/blob/main/docs/configuration.md
- https://docs.astral.sh/ruff/configuration/
