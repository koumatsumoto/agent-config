---
paths:
  - "**/*.{ts,tsx,js,jsx}"
---

# コーディングスタイル

前提: Node.js 24+ / TypeScript 6+ / ES2025。
型安全・コードスタイルは tsc strict (`erasableSyntaxOnly`, `isolatedDeclarations`) と ESLint `strictTypeChecked` に委譲する。本ルールはツールで強制できない設計判断のみ記載。

## 設計ルール

- 状態の分岐は Discriminated Union + exhaustiveness check で表現する
- オブジェクト/配列はイミュータブルに扱う（`readonly`, `Readonly<T>`, `as const`）
- 引数が 3 つ以上 or オプション引数がある場合はオプションオブジェクトパターンを使う
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

## テスト

- テストファイルは `tests/` ディレクトリに `src/` と対称的な構造で配置する（プロジェクト指定があればそちらを優先）
- テスト名は「何を」「どういう条件で」「どうなるか」を記述する
- 1 テスト 1 アサーションを目安にし、テストの独立性を保つ
