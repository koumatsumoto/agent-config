---
paths:
  - "**/*.{ts,tsx,js,jsx}"
---

# コーディングスタイル

前提: Node.js 24+ / TypeScript 5.9+ / ES2025。

## 基本方針

- 破壊的変更より小さな差分を優先する
- 既存コードの規約に合わせる

## 命名規則

- 変数・関数: `camelCase`
- 型・クラス: `PascalCase`
- 定数: `UPPER_SNAKE_CASE`
- ファイル名: `kebab-case.ts`
- 命名はドメイン語彙を優先する

## 型安全

- `any` は使わない。外部データは `unknown` + 型ガード or Zod で絞り込む
- `enum` / `namespace` は使わない。`as const satisfies` / ES モジュールで代替する
- Non-null assertion `!` / Type assertion `as` は使わない。型ガード or `satisfies` で代替する
- `@ts-ignore` / `@ts-expect-error` は原則禁止。使う場合は理由をコメントする
- 型のみのインポートには `import type` を使う
- 状態の分岐は Discriminated Union + exhaustiveness check で表現する

## 設計ルール

- オブジェクト/配列はイミュータブルに扱う（`readonly`, `Readonly<T>`, `as const`）
- 引数が 3 つ以上 or オプション引数がある場合はオプションオブジェクトパターンを使う
- 公開 API は戻り値型を明示する。内部実装は型推論に任せる
- 非同期処理は `async/await` を使う。Promise チェーン (`.then`) より優先する
- 目安: 1 ファイル 300 行以内（最大 800 行）

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
- ユーザー入力は Zod 等のスキーマバリデーションで検証する

## テスト

- テストファイルは `tests/` ディレクトリに `src/` と対称的な構造で配置する（プロジェクト指定があればそちらを優先）
- テスト名は「何を」「どういう条件で」「どうなるか」を記述する
- 1 テスト 1 アサーションを目安にし、テストの独立性を保つ
