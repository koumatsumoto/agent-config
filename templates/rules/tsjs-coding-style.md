---
paths:
  - "**/*.{ts,tsx,js,jsx}"
---

# コーディングスタイル

前提: Node.js 24+ / TypeScript 6+ / ES2025。
型安全・コードスタイルは tsc strict (`erasableSyntaxOnly`, `isolatedDeclarations`) と ESLint `strictTypeChecked` に委譲する。本ルールはツールで強制できない設計判断のみ記載。

まず対象リポジトリの実際の実行環境、依存関係、既存コードの書き方に合わせる。前提バージョンは新規実装の基準であり、対象環境が対応していない機能（例: `Temporal`）は使わない。

## 型の境界

- 外部データ（APIレスポンス、`localStorage`、`postMessage`）は`unknown`として受け取り、検証後に型を確定する。二重型アサーションを検証の代わりに使わない
- Zod 等のバリデーションは `safeParse` を使う。`parse` は例外を投げるため制御フローが複雑になる
- guard clause で型を絞り込む。`if (!x) throw` / `if (!x) return` の後は安全にアクセスできる
- `as const` でリテラル型に絞り込む（例: `state: "open" as const`, `override readonly name = "Foo" as const`）

## イミュータブル設計

- interface のプロパティには `readonly` を付ける
- 配列の型は `readonly string[]` / `ReadonlyMap` / `ReadonlySet` を優先する
- 引数オブジェクトのプロパティも `readonly` にする
- 関数の戻り値はイミュータブルな型で返す

## 設計ルール

- 既存リポジトリがライブラリ・パターンの方針を定めていればそれに従う。未定の場合の既定として以下を推奨する
- 状態の分岐は判別可能なユニオン型 + 網羅性検査で表現する。任意プロパティより Union を優先する
- 引数が三つ以上、または任意引数があり、呼び出しの明確さが増す場合はオプションオブジェクトパターンを使う
- エラーは用途別のクラス階層で設計する。`instanceof` で判別し、`override readonly name` で識別可能にする
- 凝集度を優先し、行数は分割を検討する目安にとどめる（おおよそ 300 行、800 行で肥大化を警戒）

## Reactとフックのパターン

- 複雑な状態管理（入力検証、遅延実行、楽観的更新）はカスタムフックへ分離する
- 完了を待たない処理のPromise には `void` 演算子を使う（`void navigate(...)`, `void queryClient.invalidateQueries(...)`）
- コールバック内で最新の値を参照する必要がある場合は ref パターンを使う（`ref.current = latestValue` を毎レンダーで更新）

## ES2025 / 最新ランタイム機能

対象環境が対応している場面では、以下をレガシーな書き方より優先する（対応していない機能は使わず既存コードに合わせる）:

- `using` / `await using` でリソースを確定的に解放する
- Iterator Helpers (`.map()`, `.filter()`, `.take()`) をイテレータに直接適用する
- Set メソッド (`union`, `intersection`, `difference`) をネイティブで使う
- `Promise.try()` で同期/非同期エラーを統一的に扱う
- `Error.isError()`で異なる実行領域のエラー判定をする
- 動的に組み立てる正規表現は `RegExp.escape()` でメタ文字をエスケープする（注入・誤マッチ防止）
- ランタイムが対応していれば、日付・時刻は `Date` でなく `Temporal`（`esnext.temporal` lib）を使う（タイムゾーン・期間・不変性を型で扱える）。未対応環境では `Date` か既存の日時ライブラリに合わせる

## エラー処理

- エラーメッセージは英語で書く
- 例外は握り潰さず、`cause` チェーンで元のエラーを保持する
- catchではエラー型を `instanceof` で判別し、型ごとに適切に処理する。汎用的な一括捕捉は避ける

## テスト

- テストファイルは `tests/` ディレクトリに `src/` と対称的な構造で配置する（プロジェクト指定があればそちらを優先）
- テスト名は「何を」「どういう条件で」「どうなるか」を記述する
- 一つのテストでは一つの振る舞いを確認する。必要な検証は同じテストにまとめてよい。テストの独立性は保つ
