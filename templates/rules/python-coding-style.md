---
paths:
  - "**/*.py"
---

# コーディングスタイル

前提: Python 3.12+ / Pyright strict / Ruff。

## 基本方針

- 破壊的変更より小さな差分を優先する
- 既存コードの規約に合わせる

## 命名規則

- 変数・関数・メソッド: `snake_case`
- クラス: `PascalCase`
- 定数: `UPPER_SNAKE_CASE`
- プライベート: `_` プレフィックス（`__` マングリングは避ける）
- 型エイリアス・型パラメータ: `PascalCase`（`type UserId = int`）
- 命名はドメイン語彙を優先する

## 型安全

- `Any` は使わない。`object` / ジェネリクス / 具体的な Union 型で代替する
- `typing.List`, `typing.Dict`, `typing.Optional` 等は使わない。`list`, `dict`, `X | None` を使う
- ジェネリクスは PEP 695 新構文で書く（`def first[T](items: list[T])` / `type` 文）
- `TypeVar` の明示的宣言は使わない。新構文の bounded 型パラメータで代替する
- `# type: ignore` は原則禁止。使う場合はエラーコードと理由をコメントする
- 型ナローイングには `TypeIs`（PEP 742）を優先する。`TypeGuard` は True 分岐のみ
- 状態の分岐は Union 型 + パターンマッチング + `assert_never` で exhaustiveness check する
- 型チェック専用 import は `TYPE_CHECKING` ガードに入れる

## 設計ルール

- データモデルは `@dataclass(frozen=True, slots=True)` をデフォルトにする
- 外部入力のバリデーションには Pydantic を使う。内部データには dataclass を使う
- インターフェースは Protocol（構造的部分型）で定義する。ABC 継承より優先する
- 引数の不変性は `Sequence` / `Mapping` で表現する（`list` / `dict` ではなく）
- 引数が 3 つ以上 or オプション引数がある場合はオプションオブジェクトパターンを使う
- 公開 API は戻り値型を明示する。内部実装は型推論に任せてもよい
- ミュータブルデフォルト引数は使わない。`None` + 関数内生成で代替する
- 目安: 1 ファイル 300 行以内（最大 800 行）

## Python 3.12+ モダン機能

以下が使える場面ではレガシーな書き方より優先する:

- f-string を使う。`%` / `.format()` は使わない
- `itertools.batched()` でチャンク分割する
- パターンマッチング (`match`/`case`) で複雑な条件分岐を表現する
- `ExceptionGroup` / `except*` で複数の例外を構造的に処理する
- `asyncio.TaskGroup` で構造化並行処理する（`asyncio.gather` より優先）

## エラーハンドリング

- 素の `except:` / `except Exception:` は使わない。具体的な例外型を指定する
- 例外は握り潰さず、`raise ... from e` で原因チェーンを保持する
- ユーザー入力は Pydantic 等のスキーマバリデーションで検証する

## テスト

- テストファイルは `tests/` ディレクトリに `src/` と対称的な構造で配置する（プロジェクト指定があればそちらを優先）
- テスト名は `test_何を_どういう条件で_どうなるか` の形式で記述する
- 1 テスト 1 アサーションを目安にし、テストの独立性を保つ
