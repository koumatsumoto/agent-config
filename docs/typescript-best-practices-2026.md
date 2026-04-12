# TypeScript 厳格コーディング ベストプラクティス 2026

> Reference only. Not a runtime contract. 実際の運用契約は `templates/rules/` と各テンプレートを正とする。


2026年3月時点の TypeScript 5.9 / ES2025 標準を踏まえ、最も厳格に型安全なコードを書くためのリファレンス。

> **前提**: このドキュメントはモダンな書き方のみを扱う。レガシーパターン（`enum`, `namespace`, `any` 等）は§7「アンチパターン」で代替手段とともに記載する。

---

## 目次

1. [コンパイラ設定（最厳格構成）](#1-コンパイラ設定最厳格構成)
2. [ESLint 設定（最厳格構成）](#2-eslint-設定最厳格構成)
3. [型安全パターン](#3-型安全パターン)
4. [ES2025 モダン機能の活用](#4-es2025-モダン機能の活用)
5. [関数設計](#5-関数設計)
6. [エラーハンドリング](#6-エラーハンドリング)
7. [アンチパターン](#7-アンチパターン避けるべき書き方)
8. [出典](#8-出典)

---

## 1. コンパイラ設定（最厳格構成）

### 1.1 共通設定

すべてのプロジェクトで有効にすべきオプション:

```jsonc
{
  "compilerOptions": {
    // --- 厳格な型チェック ---
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "noPropertyAccessFromIndexSignature": true,
    "noImplicitOverride": true,
    "noFallthroughCasesInSwitch": true,

    // --- モジュール ---
    "verbatimModuleSyntax": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "erasableSyntaxOnly": true,

    // --- 互換性 ---
    "esModuleInterop": true,
    "skipLibCheck": true,
    "resolveJsonModule": true
  }
}
```

### 1.2 Node.js プロジェクト

```jsonc
{
  "compilerOptions": {
    "target": "es2025",
    "module": "node20",
    "lib": ["es2025"],
    "outDir": "dist",
    "sourceMap": true
  }
}
```

`module: "node20"` は Node.js v20 の動作を安定的にモデル化する（TS 5.9 で追加）。

### 1.3 フロントエンド（バンドラ使用）

```jsonc
{
  "compilerOptions": {
    "target": "es2025",
    "module": "preserve",
    "lib": ["es2025", "dom", "dom.iterable"],
    "noEmit": true,
    "jsx": "react-jsx"
  }
}
```

`module: "preserve"` はバンドラのモジュール解決に委ねる設定。`noEmit: true` でトランスパイルもバンドラに任せる。

### 1.4 各オプションの効果

| オプション | 効果 |
|---|---|
| `noUncheckedIndexedAccess` | `arr[0]` の型が `T \| undefined` になり、存在確認を強制 |
| `exactOptionalPropertyTypes` | `{ name?: string }` への `undefined` 代入を禁止。キーの不在のみ許可 |
| `noPropertyAccessFromIndexSignature` | `obj.key` ではなく `obj["key"]` を強制し、存在しないプロパティへのアクセスを明示化 |
| `verbatimModuleSyntax` | 型のみのインポートに `import type` を強制 |
| `erasableSyntaxOnly` | `enum`, `namespace`, パラメータプロパティなどランタイムに影響する TS 固有構文を禁止 |
| `isolatedModules` | ファイル単位のトランスパイルで安全でない構文を検出 |

---

## 2. ESLint 設定（最厳格構成）

### 2.1 推奨構成

```javascript
// eslint.config.mjs
import tseslint from "typescript-eslint";

export default tseslint.config(
  tseslint.configs.strictTypeChecked,
  tseslint.configs.stylisticTypeChecked,
  {
    languageOptions: {
      parserOptions: {
        projectService: true,
        tsconfigRootDir: import.meta.dirname,
      },
    },
  },
);
```

### 2.2 構成の階層

| 構成 | 内容 |
|---|---|
| `recommended` | 基本的なコード正当性ルール |
| `strict` | `recommended` + より厳格なルール |
| `strictTypeChecked` | `strict` + 型情報を使う追加ルール（**推奨**） |
| `stylisticTypeChecked` | 可読性・一貫性のための型情報ベースルール |

`strictTypeChecked` はセマンティックバージョニングの安定性保証外。ルールがマイナーバージョンで追加・変更される可能性があるが、最新のベストプラクティスが反映される利点がある。

---

## 3. 型安全パターン

### 3.1 `unknown` over `any`

外部データは `unknown` で受け取り、型ガードまたはスキーマバリデーションで絞り込む:

```typescript
function processInput(data: unknown): string {
  if (typeof data === "string") {
    return data.toUpperCase();
  }
  throw new TypeError(`Expected string, got ${typeof data}`);
}
```

### 3.2 Discriminated Union

識別フィールド（`type` / `kind`）で分岐し、exhaustiveness check を行う:

```typescript
type Shape =
  | { kind: "circle"; radius: number }
  | { kind: "rect"; width: number; height: number };

function area(shape: Shape): number {
  switch (shape.kind) {
    case "circle":
      return Math.PI * shape.radius ** 2;
    case "rect":
      return shape.width * shape.height;
    default:
      // exhaustiveness check: 新しい variant 追加時にコンパイルエラー
      throw new Error(`Unknown shape: ${shape satisfies never}`);
  }
}
```

### 3.3 `as const satisfies`

リテラル型を保持しつつ型制約を適用する:

```typescript
type Route = {
  path: string;
  method: "GET" | "POST" | "PUT" | "DELETE";
};

const routes = [
  { path: "/users", method: "GET" },
  { path: "/users", method: "POST" },
] as const satisfies readonly Route[];

// routes[0].method の型は "GET"（"GET" | "POST" | ... に広がらない）
```

### 3.4 Branded Types（名目型）

構造的に同じ型を区別する:

```typescript
type Brand<T, B extends string> = T & { readonly __brand: B };

type UserId = Brand<string, "UserId">;
type OrderId = Brand<string, "OrderId">;

function createUserId(id: string): UserId {
  // バリデーション後にブランド付与
  if (id.length === 0) throw new Error("Empty ID");
  return id as UserId;
}

function getUser(id: UserId): void {
  // OrderId を渡すとコンパイルエラー
}
```

### 3.5 Template Literal Types

文字列パターンを型レベルで制約する:

```typescript
type EventName = `${string}:${"created" | "updated" | "deleted"}`;

function on(event: EventName, handler: () => void): void {
  // "user:created" ✅, "user:modified" ❌
}
```

### 3.6 `import type`

`verbatimModuleSyntax: true` により、型のみのインポートには `import type` が必須になる:

```typescript
import type { User } from "./models.js";
import { createUser } from "./services.js";
```

### 3.7 `using`（Explicit Resource Management / ES2025）

`Symbol.dispose` / `Symbol.asyncDispose` を実装したオブジェクトを `using` で宣言すると、スコープ終了時に自動で解放される:

```typescript
function readConfig(path: string): string {
  using file = openFile(path); // スコープ終了時に file[Symbol.dispose]() が呼ばれる
  return file.readAll();
}

async function withTransaction(db: Database): Promise<void> {
  await using tx = await db.beginTransaction();
  await tx.execute("INSERT INTO ...");
  // 正常終了時は commit、例外時は rollback（dispose 実装による）
}
```

---

## 4. ES2025 モダン機能の活用

### 4.1 Iterator Helpers

イテレータに `.map()`, `.filter()`, `.take()` 等を直接チェーン:

```typescript
function* fibonacci(): Generator<number> {
  let [a, b] = [0, 1];
  while (true) {
    yield a;
    [a, b] = [b, a + b];
  }
}

// 配列に変換せず、遅延評価のままフィルタリング
const evenFibs = fibonacci()
  .filter((n) => n % 2 === 0)
  .take(10);

for (const n of evenFibs) {
  console.log(n);
}
```

### 4.2 Set Methods

数学的な集合演算をネイティブでサポート:

```typescript
const admins = new Set(["alice", "bob"]);
const editors = new Set(["bob", "charlie"]);

admins.union(editors);               // Set {"alice", "bob", "charlie"}
admins.intersection(editors);         // Set {"bob"}
admins.difference(editors);           // Set {"alice"}
admins.symmetricDifference(editors);  // Set {"alice", "charlie"}
admins.isSubsetOf(editors);           // false
admins.isDisjointFrom(editors);       // false
```

### 4.3 `Promise.try()`

同期関数を安全に Promise チェーンに組み込む:

```typescript
// fn が同期的に throw しても rejected Promise として扱われる
const result = await Promise.try(() => JSON.parse(rawInput));
```

### 4.4 `Array.fromAsync()`

非同期イテラブルから配列を生成:

```typescript
async function* fetchPages(url: string): AsyncGenerator<Page> {
  // ページネーション処理
}

const allPages = await Array.fromAsync(fetchPages("/api/items"));
```

### 4.5 `Error.isError()`

cross-realm（iframe, Worker 等）でも正確にエラーを判定:

```typescript
try {
  riskyOperation();
} catch (e: unknown) {
  if (Error.isError(e)) {
    console.error(e.message); // 型が Error に絞られる
  }
}
```

### 4.6 `import defer`（TS 5.9）

モジュールの評価を初回アクセスまで遅延する:

```typescript
import defer * as heavyModule from "./heavy-module.js";

// この時点ではモジュールは評価されていない
function handleRareCase(): void {
  heavyModule.process(); // ここで初めてモジュールが評価される
}
```

起動パフォーマンスの改善に有効。名前空間インポート（`* as`）のみサポート。

---

## 5. 関数設計

### 5.1 `readonly` による不変性の保証

```typescript
function sum(numbers: readonly number[]): number {
  // numbers.push(1); // コンパイルエラー
  return numbers.reduce((acc, n) => acc + n, 0);
}

function updateUser(user: Readonly<User>): User {
  // user.name = "new"; // コンパイルエラー
  return { ...user, updatedAt: new Date() };
}
```

### 5.2 オプションオブジェクトパターン

```typescript
type FetchOptions = {
  timeout?: number;
  retries?: number;
  signal?: AbortSignal;
};

async function fetchData(url: string, options?: FetchOptions): Promise<Response> {
  const { timeout = 5000, retries = 3, signal } = options ?? {};
  // ...
}
```

引数が3つ以上、またはオプション引数がある場合はオブジェクトパターンを使う。

### 5.3 ジェネリクスの制約

```typescript
function getProperty<T, K extends keyof T>(obj: T, key: K): T[K] {
  return obj[key];
}

function merge<T extends Record<string, unknown>>(a: T, b: Partial<T>): T {
  return { ...a, ...b };
}
```

### 5.4 戻り値型の使い分け

```typescript
// 公開 API: 戻り値型を明示（契約として機能する）
export function createUser(name: string): User {
  return { id: crypto.randomUUID(), name, createdAt: new Date() };
}

// 内部実装: 型推論に任せる（冗長な型注釈を避ける）
function buildQuery(filters: Filters) {
  return Object.entries(filters)
    .filter(([, v]) => v !== undefined)
    .map(([k, v]) => `${k}=${encodeURIComponent(String(v))}`)
    .join("&");
}
```

---

## 6. エラーハンドリング

### 6.1 カスタムエラークラス

```typescript
class AppError extends Error {
  constructor(
    message: string,
    readonly code: string,
    readonly statusCode: number,
    options?: ErrorOptions,
  ) {
    super(message, options);
    this.name = "AppError";
  }
}

class NotFoundError extends AppError {
  constructor(resource: string, id: string, options?: ErrorOptions) {
    super(`${resource} not found: ${id}`, "NOT_FOUND", 404, options);
    this.name = "NotFoundError";
  }
}

// cause チェーンで元のエラーを保持
try {
  await db.query("...");
} catch (e: unknown) {
  throw new AppError("DB query failed", "DB_ERROR", 500, { cause: e });
}
```

### 6.2 `Result<T, E>` パターン

例外を投げずに戻り値でエラーを表現する:

```typescript
type Result<T, E = Error> =
  | { ok: true; value: T }
  | { ok: false; error: E };

function parseJson<T>(input: string): Result<T, SyntaxError> {
  try {
    return { ok: true, value: JSON.parse(input) as T };
  } catch (e: unknown) {
    return { ok: false, error: e as SyntaxError };
  }
}

const result = parseJson<Config>(rawInput);
if (!result.ok) {
  console.error(result.error.message);
  return;
}
// result.value の型は Config
```

### 6.3 Zod によるランタイムバリデーション

コンパイル時の型安全とランタイムのバリデーションを統合する:

```typescript
import { z } from "zod";

const UserSchema = z.object({
  id: z.string().uuid(),
  name: z.string().min(1).max(100),
  email: z.string().email(),
  role: z.enum(["admin", "editor", "viewer"]),
});

// スキーマから型を導出（型定義の重複を排除）
type User = z.infer<typeof UserSchema>;

function processRequest(body: unknown): User {
  return UserSchema.parse(body); // 失敗時は ZodError を throw
}
```

---

## 7. アンチパターン（避けるべき書き方）

### 7.1 `any`

**問題**: 型チェックを完全にバイパスし、型安全性が伝播的に崩壊する。

**代替**: `unknown` + 型ガード、またはジェネリクス。

### 7.2 `enum`

**問題**: ランタイムにオブジェクトを生成する TS 固有構文。`erasableSyntaxOnly: true` で禁止される。Tree-shaking が効かない場合がある。

**代替**: `as const satisfies` で Union 型を定義:

```typescript
const Role = {
  Admin: "admin",
  Editor: "editor",
  Viewer: "viewer",
} as const satisfies Record<string, string>;

type Role = (typeof Role)[keyof typeof Role]; // "admin" | "editor" | "viewer"
```

### 7.3 `namespace`

**問題**: ES モジュール以前の名前空間管理手法。`erasableSyntaxOnly: true` で禁止される。

**代替**: ES モジュール（`export` / `import`）。

### 7.4 Non-null assertion `!`

**問題**: `null | undefined` でないことをコンパイラに嘘をつく。ランタイムエラーの原因になる。

**代替**: 型ガード、Optional chaining (`?.`)、Nullish coalescing (`??`)。

```typescript
// ❌ 避ける
const name = map.get("key")!;

// ✅ 推奨
const name = map.get("key");
if (name === undefined) {
  throw new Error("Key not found");
}
```

### 7.5 `@ts-ignore` / `@ts-expect-error`

**問題**: 型エラーを握り潰す。根本原因の修正を妨げる。

**代替**: 型を正しく修正する。どうしても必要な場合は `@ts-expect-error` に理由コメントを付記し、PR レビューで妥当性を確認する。

### 7.6 Type assertion `as`

**問題**: コンパイラの型推論を上書きする。実際の値と型が乖離するリスクがある。

**代替**: 型ガード、`satisfies`、ジェネリクス。`as` が必要な場面は Branded Types の生成など限定的。

---

## 8. 出典

### 公式ドキュメント

- [TypeScript TSConfig Reference](https://www.typescriptlang.org/tsconfig/) - Microsoft
- [Announcing TypeScript 5.8](https://devblogs.microsoft.com/typescript/announcing-typescript-5-8/) - Microsoft DevBlogs
- [Announcing TypeScript 5.9](https://devblogs.microsoft.com/typescript/announcing-typescript-5-9/) - Microsoft DevBlogs
- [typescript-eslint Shared Configs](https://typescript-eslint.io/users/configs/) - typescript-eslint
- [ECMAScript 2025 Language Specification](https://tc39.es/ecma262/2025/) - TC39
- [TC39 Finished Proposals](https://github.com/tc39/proposals/blob/main/finished-proposals.md) - TC39

### 参考記事

- [The TSConfig Cheat Sheet](https://www.totaltypescript.com/tsconfig-cheat-sheet) - Total TypeScript (Matt Pocock)
- [The Strictest TypeScript Config](https://whatislove.dev/articles/the-strictest-typescript-config/) - Vladyslav Zubko
- [ECMAScript 2025 Finalized with Iterator Helpers, Set Methods](https://socket.dev/blog/ecmascript-2025-finalized) - Socket
- [Yes, you should upgrade to TypeScript 5.9](https://blog.logrocket.com/upgrade-to-typescript-5-9/) - LogRocket Blog
- [TypeScript Style Guide](https://mkosir.github.io/typescript-style-guide/) - Marko Kosir

---

*最終更新: 2026-03-07*
