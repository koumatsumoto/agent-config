---
paths:
  - "**/*.{ts,tsx,js,jsx}"
---

# コーディングスタイル

前提: Node.js 24+ / TypeScript 6+ / ES2025。
型安全・コードスタイルは tsc strict (`erasableSyntaxOnly`, `isolatedDeclarations`) と ESLint `strictTypeChecked` に委譲する。本ルールはツールで強制できない設計判断のみ記載。

## 型の境界

- 外部データ（API レスポンス、localStorage、postMessage）は `as unknown as T` で境界を明示する。直接 `as T` は使わない
- Zod 等のバリデーションは `safeParse` を使う。`parse` は例外を投げるため制御フローが複雑になる
- guard clause で型を絞り込む。`if (!x) throw` / `if (!x) return` の後は安全にアクセスできる
- `as const` でリテラル型に絞り込む（例: `state: "open" as const`, `override readonly name = "Foo" as const`）

## イミュータブル設計

- interface のプロパティには `readonly` を付ける
- 配列の型は `readonly string[]` / `ReadonlyMap` / `ReadonlySet` を優先する
- 引数オブジェクトのプロパティも `readonly` にする
- 関数の戻り値はイミュータブルな型で返す

## 設計ルール

- 状態の分岐は Discriminated Union + exhaustiveness check で表現する。optional fields より Union を優先する
- 引数が 3 つ以上 or オプション引数がある場合はオプションオブジェクトパターンを使う
- エラーは用途別のクラス階層で設計する。`instanceof` で判別し、`override readonly name` で識別可能にする
- 目安: 1 ファイル 300 行以内（最大 800 行）

## React / Hooks パターン

- 複雑なステート管理ロジック（バリデーション、デバウンス、楽観的更新）はカスタム hooks に抽出する
- fire-and-forget の Promise には `void` 演算子を使う（`void navigate(...)`, `void queryClient.invalidateQueries(...)`）
- コールバック内で最新の値を参照する必要がある場合は ref パターンを使う（`ref.current = latestValue` を毎レンダーで更新）

## ES2025 モダン機能

以下が使える場面ではレガシーな書き方より優先する:

- `using` / `await using` でリソースを確定的に解放する
- Iterator Helpers (`.map()`, `.filter()`, `.take()`) をイテレータに直接適用する
- Set メソッド (`union`, `intersection`, `difference`) をネイティブで使う
- `Promise.try()` で同期/非同期エラーを統一的に扱う
- `Error.isError()` で cross-realm のエラー判定をする

## エラーハンドリング

- エラーメッセージは英語で書く
- 例外は握り潰さず、`cause` チェーンで元のエラーを保持する
- catch ではエラー型を `instanceof` で判別し、型ごとに適切に処理する。汎用的な catch-all は避ける

## テスト

- テストファイルは `tests/` ディレクトリに `src/` と対称的な構造で配置する（プロジェクト指定があればそちらを優先）
- テスト名は「何を」「どういう条件で」「どうなるか」を記述する
- 1 テスト 1 アサーションを目安にし、テストの独立性を保つ
