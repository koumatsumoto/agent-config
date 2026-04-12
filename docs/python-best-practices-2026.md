# Python 厳格コーディング ベストプラクティス 2026

> Reference only. Not a runtime contract. 実際の運用契約は `templates/rules/` と各テンプレートを正とする。


2026年3月時点の Python 3.12+ / 3.13 / 3.14 標準を踏まえ、最も厳格に型安全なコードを書くためのリファレンス。

> **前提**: このドキュメントはモダンな書き方のみを扱う。レガシーパターン（`typing.List`, `Any`, 旧式フォーマット等）は§9「アンチパターン」で代替手段とともに記載する。

---

## 目次

1. [型チェッカー設定（最厳格構成）](#1-型チェッカー設定最厳格構成)
2. [Ruff 設定（最厳格構成）](#2-ruff-設定最厳格構成)
3. [プロジェクト設定](#3-プロジェクト設定)
4. [型安全パターン](#4-型安全パターン)
5. [Python 3.12-3.14 モダン機能の活用](#5-python-312-314-モダン機能の活用)
6. [関数・データモデル設計](#6-関数データモデル設計)
7. [エラーハンドリング](#7-エラーハンドリング)
8. [非同期パターン](#8-非同期パターン)
9. [アンチパターン（避けるべき書き方）](#9-アンチパターン避けるべき書き方)
10. [出典](#10-出典)

---

## 1. 型チェッカー設定（最厳格構成）

### 1.1 Pyright（推奨）

`pyproject.toml` に設定:

```toml
[tool.pyright]
pythonVersion = "3.12"
typeCheckingMode = "strict"
reportUnnecessaryTypeIgnoreComment = "error"
reportDeprecated = "error"
```

Pyright は TypeScript ベースの高速な型チェッカーで、VS Code (Pylance) に統合されている。

### 1.2 `typeCheckingMode` の段階

| モード | 用途 |
|---|---|
| `off` | 型チェック無効 |
| `basic` | 最低限のチェック。レガシーコードベースの段階的移行向け |
| `standard` | **デフォルト**。実用的なバグ検出。新規プロジェクトの出発点 |
| `strict` | **推奨**。約30の追加ルールを有効化。ライブラリや重要なコードに |

`standard` → `strict` で報告エラーが約10倍増加する。新規プロジェクトでは最初から `strict` を設定し、既存コードベースでは段階的に移行する。

### 1.3 主要な strict モード追加ルール

| オプション | 効果 |
|---|---|
| `reportMissingTypeStubs` | 型スタブのないライブラリ使用を報告 |
| `reportUnknownParameterType` | 型が `Unknown` の引数を報告 |
| `reportUnknownMemberType` | 型が `Unknown` のメンバーアクセスを報告 |
| `reportMissingParameterType` | 型注釈のない関数引数を報告 |
| `reportUntypedFunctionDecorator` | 型情報のないデコレータ使用を報告 |
| `reportPrivateUsage` | `_` プレフィックスのプライベートメンバーへの外部アクセスを報告 |
| `reportUnnecessaryCast` | 不要な `cast()` 呼び出しを報告 |

### 1.4 mypy（代替）

```toml
[tool.mypy]
python_version = "3.12"
strict = true
warn_unreachable = true
enable_error_code = ["ignore-without-code", "redundant-cast", "truthy-bool"]
```

---

## 2. Ruff 設定（最厳格構成）

Ruff は Rust 製の高速リンター/フォーマッタで、flake8 + isort + Black を単一ツールに統合する。

### 2.1 推奨構成

```toml
[tool.ruff]
target-version = "py312"
line-length = 88

[tool.ruff.lint]
select = [
  "E",    # pycodestyle errors
  "W",    # pycodestyle warnings
  "F",    # Pyflakes
  "I",    # isort（import ソート）
  "N",    # pep8-naming（命名規則）
  "UP",   # pyupgrade（レガシー構文の検出・自動修正）
  "ANN",  # flake8-annotations（型注釈の強制）
  "S",    # flake8-bandit（セキュリティ）
  "B",    # flake8-bugbear（バグの温床となるパターン）
  "A",    # flake8-builtins（組み込み名のシャドウイング防止）
  "C4",   # flake8-comprehensions（内包表記の最適化）
  "DTZ",  # flake8-datetimez（タイムゾーン意識の強制）
  "T10",  # flake8-debugger（デバッガ残留検出）
  "ICN",  # flake8-import-conventions（import 規約）
  "PIE",  # flake8-pie（不要コードの検出）
  "PT",   # flake8-pytest-style（pytest 規約）
  "RSE",  # flake8-raise（raise 文の改善）
  "RET",  # flake8-return（return 文の改善）
  "SLF",  # flake8-self（プライベートメンバーアクセス検出）
  "SIM",  # flake8-simplify（コード簡略化）
  "TC",   # flake8-type-checking（TYPE_CHECKING ガード）
  "ARG",  # flake8-unused-arguments（未使用引数検出）
  "PTH",  # flake8-use-pathlib（os.path → pathlib）
  "ERA",  # eradicate（コメントアウトされたコード検出）
  "PL",   # Pylint（一般的なコード品質）
  "PERF", # Perflint（パフォーマンス最適化）
  "FURB", # refurb（リファクタリング提案）
  "RUF",  # Ruff 独自ルール
]

[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["S101", "ARG", "PLR2004"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
docstring-code-format = true
```

### 2.2 `select` vs `extend-select`

| 設定 | 動作 |
|---|---|
| `select` | デフォルト（`E4`, `E7`, `E9`, `F`）を**置き換える**。ルールセットが明示的になる |
| `extend-select` | デフォルトに**追加する**。親設定の `ignore` も引き継ぐ |

新規プロジェクトでは `select` でルールセットを明示的に定義する。`ALL` は非推奨（ルール間の競合、アップグレード時の予期しない変更）。

### 2.3 主要ルールセットの役割

| ルールセット | 役割 |
|---|---|
| `E` / `W` / `F` | 基本的なコード正当性（pycodestyle + Pyflakes） |
| `I` | import の自動ソート（isort 互換） |
| `UP` | Python 3.12+ で不要なレガシー構文を検出・自動修正 |
| `ANN` | 関数の型注釈を強制 |
| `S` | セキュリティ上の問題を検出（bandit 互換） |
| `B` | バグの温床となりやすいパターン（ミュータブルデフォルト引数等）を検出 |
| `TC` | 型チェック専用 import を `TYPE_CHECKING` ブロックに移動 |
| `PTH` | `os.path` を `pathlib` に置き換え |
| `PL` | Pylint 互換の一般的なコード品質ルール |
| `PERF` | パフォーマンスに関する最適化ヒント |
| `FURB` | モダンな Python への書き換え提案 |
| `RUF` | Ruff 独自の追加ルール |

---

## 3. プロジェクト設定

### 3.1 `pyproject.toml`（推奨構成）

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "myproject"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = []

[dependency-groups]
dev = ["pyright", "ruff", "pytest"]
```

`pyproject.toml` にすべてのツール設定を集約する。`setup.py`, `setup.cfg`, `requirements.txt` は不要。

### 3.2 uv（パッケージマネージャ）

Rust 製の高速パッケージマネージャ。pip + pip-tools + pyenv + virtualenv を統合する。

```bash
# プロジェクト作成
uv init myproject
cd myproject

# 依存関係の追加
uv add requests
uv add --group dev pyright ruff pytest

# ロックファイルから再現可能なインストール
uv sync

# Python バージョン管理（pyenv 不要）
uv python install 3.13
uv python pin 3.12

# スクリプト実行
uv run python main.py
uv run pytest
```

`uv.lock` で依存関係を固定し、再現可能なビルドを保証する。`uv.lock` はバージョン管理に含める。

### 3.3 プロジェクト構成例

```
myproject/
  pyproject.toml
  uv.lock
  src/
    myproject/
      __init__.py
      py.typed          # PEP 561: 型情報の提供を宣言
      main.py
      models.py
  tests/
    __init__.py
    test_main.py
```

`src/` レイアウトを推奨。テストがソースを直接インポートする事故を防ぐ。ライブラリの場合は `py.typed` マーカーファイルを配置する。

---

## 4. 型安全パターン

### 4.1 新しいジェネリクス構文（PEP 695 / Python 3.12）

`TypeVar` の明示的な宣言が不要:

```python
# Python 3.12+ の新構文
def first[T](items: list[T]) -> T | None:
    return items[0] if items else None

class Stack[T]:
    def __init__(self) -> None:
        self._items: list[T] = []

    def push(self, item: T) -> None:
        self._items.append(item)

    def pop(self) -> T:
        return self._items.pop()
```

### 4.2 `type` 文による型エイリアス（PEP 695 / Python 3.12）

```python
# 遅延評価され、前方参照の問題がない
type Vector = list[float]
type Matrix = list[Vector]
type UserId = int
type Handler[T] = Callable[[T], None]
```

### 4.3 型パラメータのデフォルト値（PEP 696 / Python 3.13）

```python
class Response[T = dict[str, str]]:
    def __init__(self, data: T) -> None:
        self.data = data

# T のデフォルトは dict[str, str]
resp = Response({"key": "value"})  # Response[dict[str, str]]
resp2 = Response(42)                # Response[int]
```

### 4.4 `TypeIs` による型の絞り込み（PEP 742 / Python 3.13）

`TypeGuard` と異なり、`True` / `False` 両方の分岐で型が絞り込まれる:

```python
from typing import TypeIs

def is_string(value: object) -> TypeIs[str]:
    return isinstance(value, str)

def process(value: str | int) -> None:
    if is_string(value):
        print(value.upper())   # value: str
    else:
        print(value + 1)       # value: int（False 分岐でも絞り込まれる）
```

`TypeIs` を型ナローイング関数のデフォルトの選択肢にする。`TypeGuard` は True 分岐でのみ型を絞り込む。

### 4.5 Protocol（構造的部分型）

継承なしでインターフェースを定義する:

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class Renderable(Protocol):
    def render(self) -> str: ...

class HtmlWidget:
    def render(self) -> str:
        return "<div>widget</div>"

class JsonView:
    def render(self) -> str:
        return '{"view": true}'

def display(item: Renderable) -> None:
    # HtmlWidget, JsonView は Renderable を明示的に継承していないが、
    # render() メソッドを持つため型チェックを通過する
    print(item.render())
```

`@runtime_checkable` を付けると `isinstance()` チェックが可能になるが、メソッドシグネチャの検証はされない。型の正確性は Pyright/mypy に委ねる。

### 4.6 `Self` / `override`

```python
from typing import Self, override

class Base:
    def copy(self) -> Self:
        return self.__class__()

    def process(self) -> str:
        return "base"

class Child(Base):
    @override
    def process(self) -> str:
        # @override により、親クラスに process() がなければ型エラー
        return "child"
```

`@override`（PEP 698）はメソッドのオーバーライドを明示し、親クラスの変更による暗黙の破壊を防ぐ。

### 4.7 `Never` と exhaustiveness check

```python
from typing import Never, assert_never

type Shape = Circle | Rect

def area(shape: Shape) -> float:
    match shape:
        case Circle(radius=r):
            return 3.14159 * r ** 2
        case Rect(width=w, height=h):
            return w * h
        case _ as unreachable:
            assert_never(unreachable)  # 新しい variant 追加時に型エラー
```

### 4.8 `TYPE_CHECKING` ガード

型チェック時のみ必要なインポートをランタイムから除外する:

```python
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import User

def create_user(name: str) -> User:
    from .models import User
    return User(name=name)
```

`from __future__ import annotations` により、すべての型注釈が文字列として遅延評価される。

> **Python 3.14 以降**: PEP 649/749 により注釈の遅延評価が言語レベルでサポートされる。`from __future__ import annotations` は不要になり、前方参照も引用符なしで動作する。

---

## 5. Python 3.12-3.14 モダン機能の活用

### 5.1 f-string の改善（PEP 701 / Python 3.12）

f-string 内での制約が大幅に緩和:

```python
# ネストされたクォートが自由に使える
name = "world"
print(f"{'hello'} {f"{name}"}")

# 複数行の式
result = f"{
    sum(
        x ** 2
        for x in range(10)
    )
}"

# バックスラッシュも使用可能
items = ["a", "b", "c"]
print(f"joined: {'\n'.join(items)}")
```

### 5.2 `itertools.batched()`（Python 3.12）

イテラブルを固定サイズのチャンクに分割:

```python
from itertools import batched

data = range(10)
for batch in batched(data, 3):
    print(batch)
# (0, 1, 2)
# (3, 4, 5)
# (6, 7, 8)
# (9,)
```

### 5.3 パターンマッチング（Python 3.10+）

```python
def handle_command(command: dict[str, object]) -> str:
    match command:
        case {"action": "greet", "name": str(name)}:
            return f"Hello, {name}!"
        case {"action": "add", "x": int(x), "y": int(y)}:
            return f"Result: {x + y}"
        case {"action": str(action)}:
            return f"Unknown action: {action}"
        case _:
            return "Invalid command"
```

### 5.4 Exception Groups と `except*`（Python 3.11+）

複数の例外を同時に扱う:

```python
def validate(data: dict[str, str]) -> None:
    errors: list[ValueError] = []
    if "name" not in data:
        errors.append(ValueError("name is required"))
    if "email" not in data:
        errors.append(ValueError("email is required"))
    if errors:
        raise ExceptionGroup("Validation failed", errors)

try:
    validate({})
except* ValueError as eg:
    for err in eg.exceptions:
        print(f"Validation error: {err}")
```

### 5.5 テンプレート文字列 t-string（PEP 750 / Python 3.14）

f-string と同様の構文で、文字列ではなく `Template` オブジェクトを返す。SQL インジェクション防止や HTML エスケープなど、カスタム文字列処理に有用:

```python
from string.templatelib import Template, Interpolation

def html_escape(template: Template) -> str:
    parts: list[str] = []
    for part in template:
        if isinstance(part, Interpolation):
            parts.append(str(part.value).replace("&", "&amp;").replace("<", "&lt;"))
        else:
            parts.append(part)
    return "".join(parts)

user_input = "<script>alert('xss')</script>"
safe_html = html_escape(t"<p>{user_input}</p>")
# <p>&lt;script&gt;alert('xss')&lt;/script&gt;</p>
```

### 5.6 Free-threaded Python（Python 3.13 実験的 → 3.14 サポート）

GIL を無効化した真の並列実行。Python 3.14 で「実験的」タグが除去されサポート対象に（PEP 779）。ただしデフォルトビルドではなく、オプション扱い:

```python
# python3.14t（free-threaded ビルド）で実行
import threading

def cpu_bound(n: int) -> int:
    return sum(i * i for i in range(n))

threads = [threading.Thread(target=cpu_bound, args=(10_000_000,)) for _ in range(4)]
for t in threads:
    t.start()
for t in threads:
    t.join()
```

シングルスレッドで約5-10%のオーバーヘッドがある。サードパーティ C 拡張の互換性は要確認。

### 5.7 注釈の遅延評価（PEP 649/749 / Python 3.14）

型注釈がデフォルトで遅延評価され、`from __future__ import annotations` や前方参照の引用符が不要になる:

```python
# Python 3.14: 前方参照がそのまま動作する
def create() -> User:  # User がこの時点で未定義でも OK
    ...

class User:
    name: str
```

### 5.8 サブインタプリタ（PEP 734 / Python 3.14）

プロセス内で独立したインタプリタを起動し、マルチコア並列処理を実現する:

```python
from concurrent.interpreters import Interpreter

interp = Interpreter()
interp.run("print('hello from subinterpreter')")
```

multiprocessing よりオーバーヘッドが小さく、プロセスのような分離を提供する。

---

## 6. 関数・データモデル設計

### 6.1 `dataclass` による不変データモデル

```python
from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class User:
    id: str
    name: str
    email: str

user = User(id="u1", name="Alice", email="alice@example.com")
# user.name = "Bob"  # FrozenInstanceError
```

| オプション | 効果 |
|---|---|
| `frozen=True` | 不変性を保証。ハッシュ可能になり `dict` のキーや `set` に使用可能 |
| `slots=True` | `__slots__` を生成しメモリ効率・属性アクセス速度を向上（Python 3.10+） |

### 6.2 データモデルの使い分け

| モデル | 用途 |
|---|---|
| `@dataclass(frozen=True, slots=True)` | **内部ドメインモデル**。型が保証されたデータの表現 |
| `TypedDict` | **外部入力の型定義**。静的型チェックのみ、ランタイム検証なし |
| Pydantic `BaseModel` | **外部入力のバリデーション**。API リクエスト、設定ファイル等 |
| `NamedTuple` | **不変の軽量レコード**。タプルの代替。関数の多値返却に |

### 6.3 Protocol によるインターフェース設計

```python
from typing import Protocol

class Repository[T](Protocol):
    def get(self, id: str) -> T | None: ...
    def save(self, entity: T) -> None: ...
    def delete(self, id: str) -> None: ...

class InMemoryUserRepo:
    def __init__(self) -> None:
        self._store: dict[str, User] = {}

    def get(self, id: str) -> User | None:
        return self._store.get(id)

    def save(self, entity: User) -> None:
        self._store[entity.id] = entity

    def delete(self, id: str) -> None:
        self._store.pop(id, None)

def process_users(repo: Repository[User]) -> None:
    # InMemoryUserRepo は Repository[User] を継承していないが、
    # 構造的に一致するため受け入れられる
    user = repo.get("u1")
```

### 6.4 `Sequence` / `Mapping` による読み取り専用の表現

```python
from collections.abc import Sequence, Mapping

def summarize(items: Sequence[int]) -> int:
    # items.append(1)  # Sequence には append がない
    return sum(items)

def lookup(config: Mapping[str, str], key: str) -> str | None:
    # config["new_key"] = "value"  # Mapping には代入がない
    return config.get(key)
```

引数には `list` / `dict` ではなく `Sequence` / `Mapping` を使い、不変性を型で表現する。

### 6.5 オプションオブジェクトパターン

```python
@dataclass(frozen=True, slots=True)
class FetchOptions:
    timeout: float = 5.0
    retries: int = 3
    headers: Mapping[str, str] | None = None

async def fetch_data(url: str, options: FetchOptions | None = None) -> bytes:
    opts = options or FetchOptions()
    ...
```

引数が3つ以上、またはオプション引数がある場合はオブジェクトパターンを使う。

### 6.6 bounded 型パラメータ

```python
from typing import Protocol, Self

class Comparable(Protocol):
    def __lt__(self, other: Self) -> bool: ...

def max_item[T: Comparable](items: Sequence[T]) -> T:
    result = items[0]
    for item in items[1:]:
        if result < item:
            result = item
    return result
```

### 6.7 戻り値型の使い分け

```python
# 公開 API: 戻り値型を明示（契約として機能する）
def create_user(name: str) -> User:
    return User(id=uuid4().hex, name=name, email="")

# 内部実装: 型推論に任せてもよい
def _build_query(filters: dict[str, str]):
    return "&".join(f"{k}={v}" for k, v in filters.items() if v)
```

---

## 7. エラーハンドリング

### 7.1 カスタム例外クラス

```python
class AppError(Exception):
    def __init__(self, message: str, code: str, status_code: int) -> None:
        super().__init__(message)
        self.code = code
        self.status_code = status_code

class NotFoundError(AppError):
    def __init__(self, resource: str, id: str) -> None:
        super().__init__(f"{resource} not found: {id}", "NOT_FOUND", 404)

# 原因チェーンで元のエラーを保持
try:
    db.query("...")
except Exception as e:
    raise AppError("DB query failed", "DB_ERROR", 500) from e
```

`raise ... from e` で `__cause__` チェーンを構成し、元のエラーを保持する。

### 7.2 `Result[T, E]` パターン

例外を投げずに戻り値でエラーを表現する:

```python
@dataclass(frozen=True, slots=True)
class Ok[T]:
    value: T

@dataclass(frozen=True, slots=True)
class Err[E]:
    error: E

type Result[T, E = Exception] = Ok[T] | Err[E]

def parse_json(raw: str) -> Result[dict[str, object], str]:
    try:
        return Ok(json.loads(raw))
    except json.JSONDecodeError as e:
        return Err(str(e))

result = parse_json(raw_input)
match result:
    case Ok(value):
        print(value)
    case Err(error):
        print(f"Parse error: {error}")
```

### 7.3 Pydantic によるランタイムバリデーション

コンパイル時の型安全とランタイムのバリデーションを統合する:

```python
from pydantic import BaseModel, EmailStr, Field

class UserInput(BaseModel):
    id: str = Field(pattern=r"^[a-f0-9-]{36}$")
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    role: Literal["admin", "editor", "viewer"]

def process_request(body: dict[str, object]) -> UserInput:
    return UserInput.model_validate(body)  # 失敗時は ValidationError
```

Pydantic v2 は Rust コアにより高速。外部入力のバリデーション（API 境界）に使い、内部データモデルには `dataclass` を使う。

---

## 8. 非同期パターン

### 8.1 `TaskGroup` による構造化並行処理（Python 3.11+）

```python
import asyncio

async def fetch_user(user_id: str) -> User: ...
async def fetch_orders(user_id: str) -> list[Order]: ...

async def get_user_dashboard(user_id: str) -> Dashboard:
    async with asyncio.TaskGroup() as tg:
        user_task = tg.create_task(fetch_user(user_id))
        orders_task = tg.create_task(fetch_orders(user_id))

    # ブロック終了時に全タスクが完了している保証がある
    return Dashboard(user=user_task.result(), orders=orders_task.result())
```

`TaskGroup` は `asyncio.gather()` の上位互換。いずれかのタスクが失敗すると、他のタスクを自動キャンセルし `ExceptionGroup` として送出する。

### 8.2 ExceptionGroup との統合

```python
async def process_batch(items: list[str]) -> list[str]:
    async with asyncio.TaskGroup() as tg:
        tasks = [tg.create_task(process_item(item)) for item in items]

    return [t.result() for t in tasks]

try:
    results = await process_batch(items)
except* ValueError as eg:
    for err in eg.exceptions:
        print(f"Validation error: {err}")
except* ConnectionError as eg:
    for err in eg.exceptions:
        print(f"Connection error: {err}")
```

### 8.3 キャンセル安全なパターン

```python
async def resilient_operation() -> None:
    try:
        await long_running_work()
    except asyncio.CancelledError:
        # クリーンアップ後に再送出（キャンセルを握り潰さない）
        await cleanup()
        raise
```

### 8.4 `asyncio.gather()` からの移行

| | `asyncio.gather()` | `asyncio.TaskGroup()` |
|---|---|---|
| エラー時の挙動 | `return_exceptions=True` で握り潰しがち | ExceptionGroup として構造的に処理 |
| キャンセル | 手動で他タスクをキャンセルする必要あり | 自動キャンセル |
| スコープ | タスクのライフタイムが曖昧 | `async with` ブロックで明確 |

---

## 9. アンチパターン（避けるべき書き方）

### 9.1 `Any` の乱用

**問題**: 型チェックを完全にバイパスし、型安全性が伝播的に崩壊する。

**代替**: `object`（任意の値を受け取るが操作不可）、ジェネリクス、または具体的な Union 型。

### 9.2 レガシー型ヒント（`typing.List`, `typing.Dict` 等）

**問題**: Python 3.9 以降は組み込み型で直接型パラメータを指定可能。冗長なインポートになる。

**代替**: `list[int]`, `dict[str, int]`, `tuple[int, ...]`, `set[str]`。

```python
# 避ける
from typing import List, Dict, Optional
def process(items: List[Dict[str, int]]) -> Optional[str]: ...

# 推奨
def process(items: list[dict[str, int]]) -> str | None: ...
```

Ruff の `UP` ルールセットで自動検出・修正できる。

### 9.3 ミュータブルデフォルト引数

**問題**: デフォルト値は関数定義時に一度だけ生成され、呼び出し間で共有される。

**代替**: `None` を使い、関数内で生成する。

```python
# 避ける
def add_item(item: str, items: list[str] = []) -> list[str]:
    items.append(item)
    return items

# 推奨
def add_item(item: str, items: list[str] | None = None) -> list[str]:
    if items is None:
        items = []
    items.append(item)
    return items
```

Ruff の `B006`（flake8-bugbear）で検出できる。

### 9.4 旧式文字列フォーマット

**問題**: `%` 演算子と `.format()` は可読性が低く、型安全でない。

**代替**: f-string。

```python
# 避ける
"Hello %s, you are %d years old" % (name, age)
"Hello {}, you are {} years old".format(name, age)

# 推奨
f"Hello {name}, you are {age} years old"
```

Ruff の `UP031` / `UP032` で自動検出・修正できる。

### 9.5 `type()` による型チェック

**問題**: 継承関係を無視する。

**代替**: `isinstance()` または Protocol。

```python
# 避ける
if type(value) == int: ...

# 推奨
if isinstance(value, int): ...
```

### 9.6 素の `except:`

**問題**: `KeyboardInterrupt`, `SystemExit` を含むすべての例外を捕捉する。

**代替**: 具体的な例外型を指定する。

```python
# 避ける
try:
    risky_operation()
except:
    pass

# 推奨
try:
    risky_operation()
except SpecificError as e:
    logger.error("Operation failed", exc_info=e)
    raise
```

Ruff の `E722`（pycodestyle）/ `BLE001`（flake8-blind-except）で検出できる。

### 9.7 `# type: ignore` の乱用

**問題**: 型エラーを握り潰し、根本原因の修正を妨げる。

**代替**: 型を正しく修正する。どうしても必要な場合はエラーコードを指定し、理由コメントを付記する。

```python
# 避ける
result = unsafe_call()  # type: ignore

# やむを得ない場合
result = unsafe_call()  # type: ignore[no-any-return]  # ライブラリの型定義が不完全
```

Pyright の `reportUnnecessaryTypeIgnoreComment = "error"` で不要な `type: ignore` を検出できる。

### 9.8 レガシー `TypeVar` 宣言

**問題**: 冗長で、名前の重複が必要。スコープが明示的でない。

**代替**: PEP 695 の新構文（Python 3.12+）。

```python
# 避ける
from typing import TypeVar
T = TypeVar("T")
def first(items: list[T]) -> T | None: ...

# 推奨
def first[T](items: list[T]) -> T | None: ...
```

---

## 10. 出典

### 公式ドキュメント

- [What's New In Python 3.12](https://docs.python.org/3/whatsnew/3.12.html) - Python Software Foundation
- [What's New In Python 3.13](https://docs.python.org/3/whatsnew/3.13.html) - Python Software Foundation
- [What's New In Python 3.14](https://docs.python.org/3/whatsnew/3.14.html) - Python Software Foundation
- [PEP 695 - Type Parameter Syntax](https://peps.python.org/pep-0695/) - Python Enhancement Proposals
- [PEP 696 - Type Defaults for Type Parameters](https://peps.python.org/pep-0696/) - Python Enhancement Proposals
- [PEP 742 - Narrowing types with TypeIs](https://peps.python.org/pep-0742/) - Python Enhancement Proposals
- [PEP 698 - Override Decorator for Static Typing](https://peps.python.org/pep-0698/) - Python Enhancement Proposals
- [PEP 654 - Exception Groups and except*](https://peps.python.org/pep-0654/) - Python Enhancement Proposals
- [PEP 701 - Syntactic formalization of f-strings](https://peps.python.org/pep-0701/) - Python Enhancement Proposals
- [PEP 750 - Template Strings](https://peps.python.org/pep-0750/) - Python Enhancement Proposals
- [PEP 649 - Deferred Evaluation Of Annotations](https://peps.python.org/pep-0649/) - Python Enhancement Proposals
- [PEP 734 - Multiple Interpreters in the Stdlib](https://peps.python.org/pep-0734/) - Python Enhancement Proposals
- [PEP 779 - Free-threading in 3.14](https://peps.python.org/pep-0779/) - Python Enhancement Proposals
- [Pyright Configuration](https://github.com/microsoft/pyright/blob/main/docs/configuration.md) - Microsoft
- [Ruff Documentation](https://docs.astral.sh/ruff/) - Astral
- [Ruff Rules](https://docs.astral.sh/ruff/rules/) - Astral
- [uv Documentation](https://docs.astral.sh/uv/) - Astral

### 参考記事

- [Python Typing in 2025: A Comprehensive Guide](https://khaled-jallouli.medium.com/python-typing-in-2025-a-comprehensive-guide-d61b4f562b99) - Khaled Jallouli
- [Modern Python 3.12+ Features: Type Hints, Generics, and Performance](https://dasroot.net/posts/2026/01/modern-python-312-features-type-hints-generics-performance/) - dasroot.net
- [Python Type Hints: The Complete Guide for 2026](https://devtoolbox.dedyn.io/blog/python-type-hints-complete-guide) - DevToolbox
- [TypeIs does what I thought TypeGuard would do in Python](https://rednafi.com/python/typeguard-vs-typeis/) - Redowan Delowar
- [Protocols and structural subtyping](https://typing.python.org/en/latest/reference/protocols.html) - typing documentation
- [How to configure recommended Ruff defaults](https://pydevtools.com/handbook/how-to/how-to-configure-recommended-ruff-defaults/) - Python Developer Tooling Handbook
- [Python Dataclasses: The Complete Guide for 2026](https://devtoolbox.dedyn.io/blog/python-dataclasses-guide) - DevToolbox

---

*最終更新: 2026-03-07*
