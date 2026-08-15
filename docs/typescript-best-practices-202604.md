# TypeScriptベストプラクティス 2026-08

> 参考資料。実行時契約ではない。実際の運用契約は各テンプレートを正とする。
>
> 確認日: 2026-08-09

TypeScript 7.0、TSConfig、ESLint flat config、型情報を使うlintの公式情報を基準に、現在の推奨を整理した。

## 参照した一次情報

- Announcing TypeScript 7.0
- TSConfig reference
- ESLint flat config documentation
- typescript-eslint shared configs
- typescript-eslint 型情報を使うlint

## 1. ベースライン

- 新規プロジェクトの検討基準はTypeScript 7.0。対象プロジェクトの対応版を優先する
- ESMとバンドラーを基本とし、継続的に更新される実行環境を前提にする
- `tsconfig.json` を正本にする
- lint は ESLint flat config を前提にする
- 型情報を使う lint を有効にする

## 2. TypeScript 7.0でまず意識すること

- `strict` の既定が変わったため、意図的に緩める場合だけ `strict: false` を明記する
- `module` の既定は `esnext`、`target` の既定は current-year ES に寄った。暗黙既定に頼らず明示する
- `noUncheckedSideEffectImports` は既定で有効になる。side-effect import を雑に使わない
- `baseUrl` は非推奨。`paths` へ明示的に prefix を書く
- `moduleResolution: classic` は使わない。`bundler` か `nodenext` を選ぶ
- `outFile` は使わない。bundle は bundler に任せる
- `ignoreDeprecations: "6.0"` は移行猶予用であり、恒久設定にしない

## 3. TSConfig の推奨

### 共通

```jsonc
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "noPropertyAccessFromIndexSignature": true,
    "noImplicitOverride": true,
    "noFallthroughCasesInSwitch": true,
    "noUncheckedSideEffectImports": true,
    "verbatimModuleSyntax": true,
    "isolatedModules": true,
    "erasableSyntaxOnly": true,
    "skipLibCheck": true
  }
}
```

### Bundler / frontend

```jsonc
{
  "compilerOptions": {
    "module": "esnext",
    "moduleResolution": "bundler",
    "target": "es2025",
    "lib": ["es2025", "dom"],
    "noEmit": true,
    "jsx": "react-jsx"
  }
}
```

### Node.js

```jsonc
{
  "compilerOptions": {
    "module": "nodenext",
    "moduleResolution": "nodenext",
    "target": "es2025",
    "lib": ["es2025"]
  }
}
```

## 4. 7.0で押さえる追加点

- `es2025` target / lib が使える
- `RegExp.escape` は `es2025` lib で扱える
- `Temporal` の型は `esnext` / `esnext.temporal` で使える
- `stableTypeOrdering` は 6.0 から 7.0 への移行確認に有効
- TypeScript 6.0では `dom` lib が `dom.iterable` と `dom.asynciterable` を内包するため、古い lib 指定を惰性で残さない

## 5. 型設計

- `any`ではなく `unknown` を入口に使う
- index access の安全性を上げるため `noUncheckedIndexedAccess` を前提に書く
- オプションオブジェクトは `exactOptionalPropertyTypes` 前提で、`undefined` とプロパティが存在しない状態を区別する
- `enum` や namespace を新規導入しない
- ユニオン型、特に判別可能なユニオン型を主要な状態表現として使う
- import は `import type` を使い分ける

## 6. ESLint flat config

- `.eslintrc*`ではなく `eslint.config.*` を使う
- config は配列ベースの flat config で書く
- TypeScript 用 lintでは `typescript-eslint` の shared configs を使う

### 推奨例

```js
import js from "@eslint/js";
import { defineConfig } from "eslint/config";
import tseslint from "typescript-eslint";

export default defineConfig(
  js.configs.recommended,
  tseslint.configs.recommendedTypeChecked,
  tseslint.configs.stylisticTypeChecked,
  {
    languageOptions: {
      parserOptions: {
        projectService: true,
      },
    },
  },
);
```

## 7. 型情報を使うlint

- `projectService: true` を使う
- チームの型成熟度が高いなら `strictTypeChecked` を候補にする
- 実行時間は増えるが、型情報を使うlintは不具合の検出に役立つ
- CIでは型情報を使うlint、ローカルでは対象を限定したlintを併用してもよい

### 実務上の指針

- 小規模でも `recommendedTypeChecked` は前向きに検討する
- `strictTypeChecked` は初手から全採用せず、既存違反量を見て段階導入してよい
- 不要な型引数、常に真偽が決まる条件、安全でないメンバー参照などは、型情報を使うlintに任せる

## 8. 避けるもの

- `baseUrl`
- `moduleResolution: "classic"`
- `outFile`
- 暗黙既定への依存
- `.eslintrc*` 前提の古い ESLint 構成
- `any` の常用
- Node / bundler / browser の実行環境の前提を混ぜた `lib` 設定

## 9. 最小チェックリスト

- 対象プロジェクトのTypeScript対応版を確認したか
- `strict` と主要安全フラグを有効化しているか
- `bundler` または `nodenext` のどちらかに寄せているか
- `baseUrl` と `classic` を捨てているか
- ESLint flat config へ移行しているか
- 型情報を使うlint を少なくとも選択肢に入れているか

## 出典

- https://devblogs.microsoft.com/typescript/announcing-typescript-7-0/
- https://www.typescriptlang.org/tsconfig/moduleResolution.html
- https://www.typescriptlang.org/tsconfig/noUncheckedSideEffectImports.html
- https://eslint.org/docs/latest/use/configure/configuration-files
- https://typescript-eslint.io/users/configs
- https://typescript-eslint.io/getting-started/typed-linting/
