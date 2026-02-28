# Claude Code ベストプラクティス 2026

2026年2月時点の公式ドキュメントおよびコミュニティ記事を調査・精査し、CLAUDE.md / Rules / Skills の設定に関するベストプラクティスを統合整理したリファレンス。

> **最重要原則**: コンテキストウィンドウは公共財である。CLAUDE.md、Rules、Skills はすべてこの有限リソースを共有する。各設定ファイルのすべてのトークンが、会話履歴・ファイル内容・コマンド出力と競合することを常に意識する。

---

## 目次

1. [CLAUDE.md のベストプラクティス](#1-claudemd-のベストプラクティス)
2. [Rules のベストプラクティス](#2-rules-のベストプラクティス)
3. [Skills のベストプラクティス](#3-skills-のベストプラクティス)
4. [Subagents のベストプラクティス](#4-subagents-のベストプラクティス)
5. [コンテキスト管理](#5-コンテキスト管理)
6. [よくある失敗パターンと対策](#6-よくある失敗パターンと対策)
7. [出典](#7-出典)

---

## 1. CLAUDE.md のベストプラクティス

CLAUDE.md は Claude Code がセッション開始時に自動で読み込む特殊ファイルで、コードから推測できない永続的なコンテキスト（ビルドコマンド、コードスタイル、ワークフロー規則）を提供する。

### 1.1 核心原則: 少なく・絞って書く

LLM が安定して従える指示数には限界がある。研究によれば、フロンティアモデルで約 150-200 個の指示が上限とされる。Claude Code のシステムプロンプト自体が約 50 個の指示を含むため、CLAUDE.md に使える「予算」はさらに少ない。

**判断基準**: 各行について「この行を削除したら Claude が間違いを犯すか？」と問い、答えが No なら削除する。

### 1.2 推奨する長さ

| 目安 | 説明 |
|------|------|
| 理想: 60行以下 | HumanLayer の実例。大規模 SaaS でも 100行程度で対応可能 |
| 許容: 300行以下 | これを超えると指示の無視が顕著に増加する |
| 上限: 150行程度 | 公式の推奨。詳細は別ファイルに分離する |

### 1.3 含めるべき3要素: WHAT / WHY / HOW

| 要素 | 内容 | 例 |
|------|------|------|
| **WHAT** | 技術スタック、プロジェクト構造、コードベースマップ | `apps/web/ - Next.js 15`, `packages/db/ - Drizzle ORM` |
| **WHY** | プロジェクトの目的、各コンポーネントの役割 | `DDD採用、ドメインロジックは packages/domain/ に集約` |
| **HOW** | ビルド・テスト・検証コマンド、ワークフロー | `bun run build`, `bun run test` |

### 1.4 含めるべきもの / 除外すべきもの

公式ドキュメントに基づく判断基準:

| 含めるべきもの | 除外すべきもの |
|----------------|----------------|
| Claude が推測できない Bash コマンド | コードを読めば分かること |
| デフォルトと異なるコードスタイル規則 | Claude が既に知っている標準的な言語規約 |
| テスト方法と推奨テストランナー | 詳細な API ドキュメント（リンクで済ませる） |
| リポジトリ運用ルール（ブランチ命名、PR規約） | 頻繁に変わる情報 |
| プロジェクト固有のアーキテクチャ決定 | 長い説明やチュートリアル |
| 開発環境の癖（必要な環境変数など） | ファイルごとのコードベース説明 |
| よくあるハマりポイント | 自明な実践（「きれいなコードを書け」など） |

### 1.5 コードスタイルは CLAUDE.md に書かない

コードスタイル（インデント、クォート、import順序）は Linter / Formatter で機械的に強制する。LLM は「比較的高コストで非常に遅いリンター」であり、この用途には適さない。代わりに Claude Code の Hooks を使って、ファイル編集後に自動でフォーマッターを実行する。

### 1.6 配置場所と優先順位

上位（組織ポリシー）から下位（ローカル設定）へ、より具体的な指示が優先される:

| 配置場所 | パス | 用途 | 共有範囲 |
|----------|------|------|----------|
| 組織ポリシー | `/Library/Application Support/ClaudeCode/CLAUDE.md` (macOS) | 全社共通ルール | 全ユーザー |
| プロジェクト | `./CLAUDE.md` or `./.claude/CLAUDE.md` | チーム共有の指示 | チーム（Git経由） |
| プロジェクトルール | `./.claude/rules/*.md` | モジュラーなトピック別指示 | チーム（Git経由） |
| ユーザー | `~/.claude/CLAUDE.md` | 個人設定（全プロジェクト） | 自分のみ |
| ローカル | `./CLAUDE.local.md` | 個人的なプロジェクト固有設定 | 自分のみ |
| Auto Memory | `~/.claude/projects/<project>/memory/` | Claude の自動メモ | 自分のみ |

- 親ディレクトリの CLAUDE.md は起動時にフル読み込みされる
- 子ディレクトリの CLAUDE.md はオンデマンドで読み込まれる
- `CLAUDE.local.md` は自動的に `.gitignore` に追加される

### 1.7 @import による段階的開示

詳細情報は CLAUDE.md に詰め込まず、別ファイルに分離して `@path` で参照する:

```markdown
See @README.md for project overview and @package.json for available commands.

# Additional Instructions
- Architecture: @docs/architecture.md
- Git workflow: @docs/git-instructions.md
- Personal overrides: @~/.claude/my-project-instructions.md
```

- 相対パスはインポート元ファイルからの相対
- 再帰的インポートに対応（最大深度5ホップ）
- コードブロック内の `@` はインポートとして評価されない
- コードスニペットではなく `file:line` 形式の参照を使い、情報の陳腐化を防ぐ

### 1.8 強調による遵守率の向上

重要な指示には `IMPORTANT` や `YOU MUST` などの強調を付けると遵守率が向上する。ただし乱用すると効果が薄れるため、本当に重要なルールにのみ使う。

### 1.9 指示が無視される理由

- LLM は入力の**先頭と末尾**を強く重み付けする傾向がある（Lost in the Middle 問題）
- Claude Code は CLAUDE.md の内容に「タスクに関連する場合もしない場合もある」とシステムリマインダーを付加する
- ファイルが長すぎると、重要なルールが雑音に埋もれる

**対策**: 最重要情報をファイル先頭に配置し、普遍的に適用できる情報のみ含める。

### 1.10 `/init` の使いどころ

`/init` はプロジェクト構造を分析してスターター CLAUDE.md を生成するが、自動生成に頼りすぎない。生成結果は出発点として使い、手動で精査・剪定する。

### 1.11 チェックリスト

- [ ] 300行以下に収まっているか
- [ ] 非汎用的な指示が混在していないか
- [ ] コードスニペットではなくファイル参照を使っているか
- [ ] コードスタイル指示が不要に含まれていないか
- [ ] 最重要情報がファイル先頭にあるか
- [ ] 定期的に見直し・更新されているか
- [ ] Claude のミス発見時に逐次更新しているか

---

## 2. Rules のベストプラクティス

Rules は `.claude/rules/*.md` に配置するモジュラーなトピック別指示ファイル。CLAUDE.md を肥大化させずにプロジェクト固有のルールを管理できる。

### 2.1 基本構造

```
.claude/rules/
├── frontend/
│   ├── react.md
│   └── styles.md
├── backend/
│   ├── api.md
│   └── database.md
└── general.md
```

すべての `.md` ファイルが再帰的に検出・読み込みされる。

### 2.2 パス固有ルール（YAML フロントマター）

特定のファイルパスにのみ適用するルールを定義できる:

```yaml
---
paths:
  - "src/api/**/*.ts"
---
# API Development Rules
- All API endpoints must include input validation
- Use the standard error response format
```

`paths` フィールドがないルールは無条件にすべてのファイルに適用される。

サポートされるパターン:

| パターン | マッチ対象 |
|----------|-----------|
| `**/*.ts` | 全ディレクトリの TypeScript ファイル |
| `src/**/*` | src/ 配下の全ファイル |
| `src/**/*.{ts,tsx}` | ブレース展開による複数拡張子 |

### 2.3 ユーザーレベルルール

`~/.claude/rules/` に個人用ルールを配置できる。プロジェクトルールより低い優先度で読み込まれる。

### 2.4 Symlink によるチーム共有

チーム共通ルールを symlink で共有できる:

```bash
ln -s ~/shared-claude-rules .claude/rules/shared
```

循環 symlink は検出され安全に処理される。

### 2.5 推奨事項

- **1ファイル1トピック**: テスト、API設計、セキュリティなど焦点を絞る
- **説明的なファイル名**: 内容が分かる名前を付ける（`doc2.md` ではなく `form_validation_rules.md`）
- **条件付きルールは控えめに**: 本当に特定のファイルタイプにのみ適用する場合のみ `paths` を使う
- **サブディレクトリで整理**: 関連ルールをグループ化する

---

## 3. Skills のベストプラクティス

Skills は Claude の知識をプロジェクト・チーム・ドメイン固有の情報で拡張する仕組み。関連する場面で自動的に適用されるか、`/skill-name` で直接呼び出せる。

### 3.1 SKILL.md の基本構造

```yaml
---
name: my-skill
description: What this skill does and when to use it
---

# Skill Instructions
...
```

必須フィールドは `description` のみ（推奨）。`name` を省略するとディレクトリ名が使われる。

### 3.2 主要フロントマターフィールド

| フィールド | 説明 |
|-----------|------|
| `name` | 小文字・数字・ハイフンのみ。最大64文字 |
| `description` | 何をするか、いつ使うかを記述。最大1024文字 |
| `disable-model-invocation` | `true` で Claude の自動呼び出しを禁止（手動のみ） |
| `user-invocable` | `false` で `/` メニューから非表示（Claude のみ使用） |
| `allowed-tools` | スキル実行時に許可するツール |
| `context` | `fork` でサブエージェントとして分離実行 |
| `agent` | `context: fork` 時のエージェントタイプ指定 |

### 3.3 命名規約

- **kebab-case** を使用（フォルダ名にスペースを含めるとロードが壊れる）
- **動名詞形（gerund）を推奨**: `processing-pdfs`, `analyzing-spreadsheets`, `testing-code`
- 曖昧な名前を避ける: `helper`, `utils`, `tools`
- 予約語を含めない: `anthropic-*`, `claude-*`

### 3.4 description の書き方

description は Claude がスキルを選択する際の判断材料。100以上のスキルから適切なものを選ぶ必要があるため、具体的に書く。

**ルール**:
- **三人称で書く**（description はシステムプロンプトに注入されるため）
  - Good: "Processes Excel files and generates reports"
  - Bad: "I can help you process Excel files"
- **何をするか + いつ使うか** の両方を含める
- キーワードを具体的に含める

**良い例**:
```yaml
description: Extract text and tables from PDF files, fill forms, merge documents. Use when working with PDF files or when the user mentions PDFs, forms, or document extraction.
```

**悪い例**:
```yaml
description: Helps with documents
```

### 3.5 Progressive Disclosure（段階的開示）

SKILL.md は概要と参照ポインタに留め、詳細は別ファイルに分離する。Claude は必要な時だけ参照ファイルを読み込む。

```
my-skill/
├── SKILL.md              # 概要とナビゲーション（必須）
├── reference.md          # API リファレンス（必要時のみ読み込み）
├── examples.md           # 使用例（必要時のみ読み込み）
└── scripts/
    └── helper.py         # ユーティリティスクリプト（実行用）
```

**重要**: 参照は SKILL.md から1階層のみ。深いネストは避ける。

```markdown
# Bad: 深すぎるネスト
SKILL.md -> advanced.md -> details.md -> actual info

# Good: 1階層の参照
SKILL.md -> advanced.md
SKILL.md -> reference.md
SKILL.md -> examples.md
```

### 3.6 SKILL.md のサイズ制限

- **500行以下** を推奨（公式）
- 超える場合は別ファイルに分離

### 3.7 呼び出し制御

| 設定 | ユーザー呼出 | Claude 自動呼出 | 用途 |
|------|:-----------:|:--------------:|------|
| デフォルト | Yes | Yes | 一般的なスキル |
| `disable-model-invocation: true` | Yes | No | `/deploy`, `/commit` など副作用のあるワークフロー |
| `user-invocable: false` | No | Yes | レガシーシステムの知識など、バックグラウンド知識 |

### 3.8 コンテキストコスト

- **コマンド（手動呼出）**: 呼び出されるまでトークンコストゼロ。description がコンテキストに含まれない
- **スキル（自動呼出）**: description が常にコンテキストに含まれる。スキル数が多いと文字予算（コンテキストウィンドウの2%、フォールバック16,000文字）を超える場合がある（`/context` で確認可能）
- 使用頻度の低い自動スキルは、定期的にコマンド（手動呼出）に変換することを検討する

### 3.9 ワークフロースキルとフィードバックループ

複雑な操作はチェックリスト形式のステップに分解する:

```markdown
## Workflow
1. Analyze the input
2. Create plan file (validate before executing)
3. Execute changes
4. **Validate immediately**: run validation script
5. If validation fails: fix and re-validate
6. Only proceed when validation passes
```

「実行 -> 検証 -> 修正 -> 再検証」のフィードバックループが品質を大幅に向上させる。

### 3.10 テンプレートパターンと例示パターン

**テンプレート**: 出力形式を制御したい場合に使用

```markdown
## Report Structure
ALWAYS use this exact template:
# [Title]
## Executive summary
## Key findings
## Recommendations
```

**例示**: 入出力ペアを示して期待するスタイルを伝える

```markdown
## Examples
Input: Added user authentication with JWT
Output: feat(auth): implement JWT-based authentication
```

### 3.11 反復開発プロセス

1. スキルなしでタスクを完了し、繰り返し提供した情報を特定
2. その情報をスキルとして構造化
3. 別の Claude インスタンスでテスト
4. 実際の使用を観察し、改善を繰り返す
5. Haiku / Sonnet / Opus すべてでテスト

---

## 4. Subagents のベストプラクティス

Subagents は独自のコンテキストとツールセットで動作する専門エージェント。メインの会話を汚染せずに調査や検証を行える。

### 4.1 定義方法

```markdown
# .claude/agents/security-reviewer.md
---
name: security-reviewer
description: Reviews code for security vulnerabilities
tools: Read, Grep, Glob, Bash
model: opus
---

You are a senior security engineer. Review code for:
- Injection vulnerabilities (SQL, XSS, command injection)
- Authentication and authorization flaws
- Secrets or credentials in code
- Insecure data handling
```

### 4.2 主な用途

- **調査の分離**: コードベースの探索をサブエージェントに委譲し、メインコンテキストを保護
- **実装後の検証**: 別コンテキストでのコードレビュー（書いたコードへのバイアスを排除）
- **並列実行**: 独立したタスクを複数のサブエージェントで同時処理

### 4.3 Skills との連携

スキルに `context: fork` を設定するとサブエージェントとして分離実行される:

```yaml
---
name: deep-research
description: Research a topic thoroughly
context: fork
agent: Explore
---
Research $ARGUMENTS thoroughly...
```

### 4.4 設計指針

- **汎用ロールより特化ロール**: 「バックエンドエンジニア」ではなく「認証フローレビュアー」
- **1タスク1主担当**: 過剰な分割を避ける
- **出力に判断根拠と次アクションを明示させる**

---

## 5. コンテキスト管理

コンテキストウィンドウは Claude Code で管理すべき最も重要なリソース。

### 5.1 セッション管理の原則

| 状況 | アクション |
|------|----------|
| 無関係なタスクに移る | `/clear` でコンテキストをリセット |
| 長いセッションで性能低下 | `/compact <焦点>` で圧縮 |
| 同じ問題で2回以上修正失敗 | `/clear` して初期プロンプトを改善してやり直す |
| 大量のファイル読み取りが必要な調査 | サブエージェントに委譲 |
| コンテキスト使用率 70% 到達 | 手動で `/compact` を実行 |

### 5.2 検証手段の提供

Claude に自分の作業を検証させることが、最もレバレッジの高い実践。

- テストスイートの実行指示
- スクリーンショット比較
- 期待される出力の明示
- Linter / 型チェック

検証手段がない場合、出荷しない。

### 5.3 探索 -> 計画 -> 実装 -> コミット

1. **Explore**: Plan Mode でファイルを読み、現状を理解
2. **Plan**: 実装計画を作成（`Ctrl+G` でエディタ編集可能）
3. **Implement**: Normal Mode でコーディング + テスト
4. **Commit**: 説明的なメッセージでコミット

スコープが明確で小さい修正ではこのフローをスキップしてよい。

---

## 6. よくある失敗パターンと対策

| パターン | 症状 | 対策 |
|----------|------|------|
| **キッチンシンクセッション** | 1つのセッションで無関係なタスクを混在 | タスク間で `/clear` |
| **CLAUDE.md の肥大化** | 指示が多すぎて Claude が半分を無視 | 定期的に剪定。正しく動作している指示は削除し、Hook に変換 |
| **無限修正ループ** | 同じ修正を繰り返し、コンテキストが汚染 | 2回失敗したら `/clear` してプロンプトを改善 |
| **検証なし出荷** | もっともらしいがエッジケースを扱わない実装 | 必ずテスト・検証手段を提供 |
| **無限探索** | スコープなしの調査で大量のファイルを読み込み | 調査範囲を限定するか、サブエージェントに委譲 |
| **自動生成への過度な依存** | `/init` の出力をそのまま使用 | 自動生成は出発点。手動で精査・剪定する |
| **時間依存の情報** | 「2025年8月以前は旧APIを使う」のような記述 | 事実ベースの記述に変える。旧情報は `<details>` で折りたたむ |

---

## 7. 出典

### 公式ドキュメント（一次情報）

- [Best Practices for Claude Code](https://code.claude.com/docs/en/best-practices) - Anthropic 公式
- [Extend Claude with Skills](https://code.claude.com/docs/en/skills) - Anthropic 公式
- [Manage Claude's Memory](https://code.claude.com/docs/en/memory) - Anthropic 公式
- [Skill Authoring Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) - Anthropic API Docs

### コミュニティ記事（実践検証あり）

- [Writing a Good CLAUDE.md](https://www.humanlayer.dev/blog/writing-a-good-claude-md) - HumanLayer Blog
- [Claude Code を使いこなすためのベストプラクティス（実践検証付き）](https://tech.enechange.co.jp/entry/2026/02/16/195000) - ENECHANGE Developer Blog
- [claude-code-best-practice](https://github.com/shanraisshan/claude-code-best-practice) - GitHub (shanraisshan)
- [Claude Skill vs Command: 2026 Best Practices](https://oneaway.io/blog/claude-skill-vs-command) - OneAway

### コミュニティ記事（参考情報）

- [CLAUDE.md 運用のベストプラクティス: 失敗しないための7つの原則](https://zenn.dev/imohuke/articles/claude-code-best-practices-2026) - Zenn
- [CLAUDE.md や AGENTS.md のベストプラクティスな書き方](https://izanami.dev/post/47b08b5a-6e1c-4fb0-8342-06b8e627450a) - izanami.dev

---

*最終更新: 2026-02-28*
