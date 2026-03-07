# Claude Code ベストプラクティス 2026

2026年3月時点の公式ドキュメントおよびコミュニティ記事を調査・精査し、CLAUDE.md / Rules / Skills / Subagents / Hooks の設定に関するベストプラクティスを統合整理したリファレンス。

> **最重要原則**: コンテキストウィンドウは公共財である。CLAUDE.md、Rules、Skills はすべてこの有限リソースを共有する。各設定ファイルのすべてのトークンが、会話履歴・ファイル内容・コマンド出力と競合することを常に意識する。

---

## 目次

1. [CLAUDE.md のベストプラクティス](#1-claudemd-のベストプラクティス)
2. [Rules のベストプラクティス](#2-rules-のベストプラクティス)
3. [Skills のベストプラクティス](#3-skills-のベストプラクティス)
4. [Subagents のベストプラクティス](#4-subagents-のベストプラクティス)
5. [Hooks のベストプラクティス](#5-hooks-のベストプラクティス)
6. [コンテキスト管理](#6-コンテキスト管理)
7. [よくある失敗パターンと対策](#7-よくある失敗パターンと対策)
8. [出典](#8-出典)

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

コードスタイル（インデント、クォート、import順序）は Linter / Formatter で機械的に強制する。LLM は「比較的高コストで非常に遅いリンター」であり、この用途には適さない。代わりに Claude Code の Hooks を使って、ファイル編集後に自動でフォーマッターを実行する（具体的な設定例は §5.5 を参照）。

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
| `argument-hint` | オートコンプリート時のヒント（例: `[issue-number]`） |
| `disable-model-invocation` | `true` で Claude の自動呼び出しを禁止（手動のみ） |
| `user-invocable` | `false` で `/` メニューから非表示（Claude のみ使用） |
| `allowed-tools` | スキル実行時に許可するツール |
| `model` | スキル実行時に使用するモデル指定 |
| `context` | `fork` でサブエージェントとして分離実行 |
| `agent` | `context: fork` 時のエージェントタイプ指定（`Explore`, `Plan`, `general-purpose`, カスタム） |
| `hooks` | スキルのライフサイクルに紐づくフック定義（§5 参照） |

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

**重要**: 参照は SKILL.md から1階層のみ。深いネストは避ける。`--add-dir` で追加したディレクトリの `.claude/skills/` も自動ロードされ、ライブ変更検知にも対応している。

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

| 設定 | ユーザー呼出 | Claude 自動呼出 | description のコンテキスト負荷 | 用途 |
|------|:-----------:|:--------------:|:---:|------|
| デフォルト | Yes | Yes | 常時 | 一般的なスキル |
| `disable-model-invocation: true` | Yes | No | なし | `/deploy`, `/commit` など副作用のあるワークフロー |
| `user-invocable: false` | No | Yes | 常時 | レガシーシステムの知識など、バックグラウンド知識 |

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

### 3.11 動的コンテキスト注入

SKILL.md 内で `` !`command` `` 構文を使うと、スキル呼び出し時にシェルコマンドの出力を動的に注入できる:

```yaml
---
name: pr-summary
description: Summarize changes in a pull request
context: fork
agent: Explore
---

## Pull request context
- PR diff: !`gh pr diff`
- PR comments: !`gh pr view --comments`
```

コマンドはスキル読み込み時に即時実行（前処理）され、出力がプレースホルダーを置換する。

### 3.12 反復開発プロセス

1. スキルなしでタスクを完了し、繰り返し提供した情報を特定
2. その情報をスキルとして構造化
3. 別の Claude インスタンスでテスト
4. 実際の使用を観察し、改善を繰り返す
5. Haiku / Sonnet / Opus すべてでテスト

---

## 4. Subagents のベストプラクティス

Subagents は独自のコンテキストとツールセットで動作する専門エージェント。メインの会話を汚染せずに調査や検証を行える。v2.1.41 以降、Worktree Isolation・Agent Memory・Agent Teams が追加され、マルチエージェントプラットフォームとしての機能が大幅に強化された。

### 4.1 定義方法

```markdown
# .claude/agents/security-reviewer.md
---
name: security-reviewer
description: Reviews code for security vulnerabilities
tools: Read, Grep, Glob, Bash
model: sonnet
memory: project
---

You are a senior security engineer. Review code for:
- Injection vulnerabilities (SQL, XSS, command injection)
- Authentication and authorization flaws
- Secrets or credentials in code
- Insecure data handling
```

### 4.2 フロントマターフィールド

| フィールド | 必須 | 説明 |
|-----------|:----:|------|
| `name` | Yes | 一意識別子（小文字+ハイフン） |
| `description` | Yes | いつ委譲するかの判断材料 |
| `tools` | No | 許可するツール（省略時は親から継承） |
| `disallowedTools` | No | 禁止するツール（拒否リスト） |
| `model` | No | `sonnet` / `opus` / `haiku` / `inherit`（デフォルト: inherit） |
| `permissionMode` | No | `default` / `acceptEdits` / `dontAsk` / `bypassPermissions` / `plan` |
| `maxTurns` | No | 最大ターン数 |
| `skills` | No | プリロードするスキル（全文がコンテキストに注入される） |
| `mcpServers` | No | 利用可能な MCP サーバー |
| `hooks` | No | ライフサイクルフック（`PreToolUse`, `PostToolUse`, `Stop`/`SubagentStop`） |
| `memory` | No | 永続メモリのスコープ: `user` / `project` / `local` |
| `background` | No | `true` でバックグラウンド実行（デフォルト: false） |
| `isolation` | No | `worktree` で git worktree による分離実行 |

### 4.3 配置スコープと優先順位

同名のエージェントが複数存在する場合、上位が優先される:

| 配置場所 | スコープ | 優先度 | 作成方法 |
|----------|---------|:------:|----------|
| `--agents` CLI フラグ | セッション限定 | 1（最高） | JSON をインラインで指定 |
| `.claude/agents/` | プロジェクト | 2 | Git 管理可、チーム共有 |
| `~/.claude/agents/` | 全プロジェクト | 3 | 個人用 |
| プラグインの `agents/` | プラグイン有効時 | 4（最低） | プラグインに同梱 |

- `claude agents` コマンドで設定済みエージェントを一覧表示
- `/agents` でセッション内から対話的に作成・編集・削除

### 4.4 Worktree Isolation

`isolation: worktree` を設定すると、エージェントは一時的な git worktree で動作し、他のエージェントやメインの作業ディレクトリと干渉しない:

```yaml
---
name: batch-worker
description: Process tasks in isolation
isolation: worktree
---

You are a worker that handles isolated tasks.
```

- 各エージェントが独自のブランチと作業ディレクトリを持つ
- 変更がなければ worktree は自動クリーンアップされる
- `WorktreeCreate` / `WorktreeRemove` フックで git 以外の VCS にも対応可能（§5 参照）

### 4.5 Agent Memory

`memory` フィールドで永続メモリを有効化すると、セッションを跨いで知識を蓄積できる:

```yaml
memory: project  # user | project | local
```

- `MEMORY.md` の先頭200行がシステムプロンプトに自動注入される
- **ユースケース**: コードレビュアーがパターンを学習、アーキテクトがコードベースの知識を蓄積

### 4.6 Agent Teams（実験的機能）

Subagents はセッション内で動作するが、**Agent Teams** はセッションを跨いで複数の専門エージェントが並列に協調する仕組み。セキュリティ・パフォーマンス・テストカバレッジなど異なるレンズで並列レビューを行うケースに適する。

> **注意**: Agent Teams は実験的機能であり、デフォルトでは無効。`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` を settings.json または環境変数で有効化する必要がある。

詳細は [Agent Teams ドキュメント](https://code.claude.com/docs/en/agent-teams) を参照。

### 4.7 主な用途

- **調査の分離**: コードベースの探索をサブエージェントに委譲し、メインコンテキストを保護
- **実装後の検証**: 別コンテキストでのコードレビュー（書いたコードへのバイアスを排除）
- **並列実行**: `isolation: worktree` で独立したタスクを複数のサブエージェントで同時処理

### 4.8 Skills との連携

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

`agent` フィールドには組み込みエージェント（`Explore`, `Plan`, `general-purpose`）またはカスタムエージェント（`.claude/agents/` 配下）を指定できる。

### 4.9 設計指針

- **汎用ロールより特化ロール**: 「バックエンドエンジニア」ではなく「認証フローレビュアー」
- **1タスク1主担当**: 過剰な分割を避ける
- **出力に判断根拠と次アクションを明示させる**
- **並列処理には `isolation: worktree`**: マージコンフリクトを防ぐ

---

## 5. Hooks のベストプラクティス

Hooks はエージェントのライフサイクルの特定ポイントで実行されるカスタムロジック。CLAUDE.md にコードスタイル指示を書くより、Hooks で機械的に強制する方が確実で効率的。

### 5.1 フックタイプ

| タイプ | 説明 |
|--------|------|
| `command` | シェルコマンドを実行。stdin で JSON を受信 |
| `http` | URL に JSON を POST し、JSON レスポンスを受信。ヘッダーで環境変数展開対応 |
| `prompt` | Claude に評価を送信 |
| `agent` | 検証用サブエージェントを起動 |

### 5.2 フックイベント一覧（17種）

| カテゴリ | イベント | 発火タイミング |
|----------|---------|---------------|
| セッション | `SessionStart` | セッション開始/再開時 |
| | `SessionEnd` | セッション終了時 |
| | `InstructionsLoaded` | CLAUDE.md / rules 読み込み時 |
| ユーザー操作 | `UserPromptSubmit` | プロンプト送信時（Claude 処理前） |
| | `Stop` | メインエージェント応答完了時 |
| | `SubagentStart` | サブエージェント起動時 |
| | `SubagentStop` | サブエージェント完了時 |
| | `Notification` | 通知送信時 |
| ツール実行 | `PreToolUse` | ツール実行前（ブロック可能） |
| | `PostToolUse` | ツール実行成功後 |
| | `PostToolUseFailure` | ツール実行失敗後 |
| | `PermissionRequest` | 権限ダイアログ表示時 |
| Agent Teams | `TeammateIdle` | チームメイトがアイドルになる直前 |
| | `TaskCompleted` | タスク完了マーク時 |
| インフラ | `ConfigChange` | 設定ファイル変更時 |
| | `PreCompact` | コンテキスト圧縮前 |
| | `WorktreeCreate` / `WorktreeRemove` | Worktree の作成/削除時 |

### 5.3 設定場所

| 配置場所 | スコープ | 共有可否 |
|----------|---------|---------|
| `~/.claude/settings.json` | 全プロジェクト | 不可 |
| `.claude/settings.json` | プロジェクト | Git 管理可 |
| `.claude/settings.local.json` | プロジェクト | 不可（gitignored） |
| エージェント/スキルのフロントマター | コンポーネント有効時 | 定義次第 |

### 5.4 HTTP Hooks

シェルコマンドの代わりに外部サービスへ JSON を POST できる:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "http",
            "url": "http://localhost:8080/hooks/validate",
            "headers": {
              "Authorization": "Bearer $MY_TOKEN"
            },
            "allowedEnvVars": ["MY_TOKEN"],
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

- `allowedEnvVars` に列挙されていない環境変数は空文字に置換される
- 2xx + JSON レスポンスでツール実行をブロック可能
- 接続失敗/タイムアウトは非ブロッキングエラー（実行は継続）

### 5.5 実践的な活用パターン

**コードスタイルの自動強制**（§1.5 の具体的な実装）:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "jq -r '.tool_input.file_path' | xargs npx prettier --write"
          }
        ]
      }
    ]
  }
}
```

**品質ゲートの強制**（Agent Teams 向け）:

`TeammateIdle` でビルド成果物の存在を検証、`TaskCompleted` でテスト通過を強制できる。終了コード 2 でフィードバックを返すとエージェントは作業を継続する。

**サブエージェント出力の後処理**:

`SubagentStop` の `last_assistant_message` フィールドでサブエージェントの最終応答にアクセスし、ログ記録や通知に活用できる。

### 5.6 終了コードの意味

| コード | 意味 |
|:------:|------|
| 0 | 成功。JSON 出力がある場合は処理される |
| 2 | ブロッキングエラー。アクションを阻止し、stderr を Claude/ユーザーに表示 |
| その他 | 非ブロッキングエラー。verbose モードで表示 |

---

## 6. コンテキスト管理

コンテキストウィンドウは Claude Code で管理すべき最も重要なリソース。Opus 4.6 は 1M コンテキストに対応しているが、有限であることに変わりはない。

### 6.1 セッション管理の原則

| 状況 | アクション |
|------|----------|
| 無関係なタスクに移る | `/clear` でコンテキストをリセット |
| 長いセッションで性能低下 | `/compact <焦点>` で圧縮 |
| 同じ問題で2回以上修正失敗 | `/clear` して初期プロンプトを改善してやり直す |
| 大量のファイル読み取りが必要な調査 | サブエージェントに委譲 |
| コンテキスト使用率 70% 到達 | 手動で `/compact` を実行 |

### 6.2 検証手段の提供

Claude に自分の作業を検証させることが、最もレバレッジの高い実践。

- テストスイートの実行指示
- スクリーンショット比較
- 期待される出力の明示
- Linter / 型チェック

検証手段がない場合、出荷しない。

### 6.3 探索 -> 計画 -> 実装 -> コミット

1. **Explore**: Plan Mode でファイルを読み、現状を理解
2. **Plan**: 実装計画を作成（`Ctrl+G` でエディタ編集可能）
3. **Implement**: Normal Mode でコーディング + テスト
4. **Commit**: 説明的なメッセージでコミット

スコープが明確で小さい修正ではこのフローをスキップしてよい。

### 6.4 セッション転送と MCP 同期

- **`/teleport`**: ターミナルのセッションを claude.ai/code やモバイルアプリに転送できる。外出先からの監視や承認に便利
- **MCP サーバー同期**: claude.ai アカウントで設定した MCP サーバーが Claude Code でも自動的に利用可能

### 6.5 モデル選択

| モデル | 特徴 |
|--------|------|
| Opus 4.6 | 最高性能。1M コンテキスト対応。複雑なタスクに最適 |
| Sonnet 4.6 | 速度と品質のバランス。日常的なタスクに推奨 |
| Haiku 4.5 | 最速。軽量なタスクや大量並列処理に適する |

Opus 4 / 4.1 は Claude Code から削除済み。ピン留めしていたユーザーは Opus 4.6 に自動移行された。

---

## 7. よくある失敗パターンと対策

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

## 8. 出典

### 公式ドキュメント（一次情報）

- [Best Practices for Claude Code](https://code.claude.com/docs/en/best-practices) - Anthropic 公式
- [Extend Claude with Skills](https://code.claude.com/docs/en/skills) - Anthropic 公式
- [Create Custom Subagents](https://code.claude.com/docs/en/sub-agents) - Anthropic 公式
- [Hooks Reference](https://code.claude.com/docs/en/hooks) - Anthropic 公式
- [Automate Workflows with Hooks](https://code.claude.com/docs/en/hooks-guide) - Anthropic 公式
- [Manage Claude's Memory](https://code.claude.com/docs/en/memory) - Anthropic 公式
- [Skill Authoring Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) - Anthropic API Docs

### コミュニティ記事（実践検証あり）

- [Writing a Good CLAUDE.md](https://www.humanlayer.dev/blog/writing-a-good-claude-md) - HumanLayer Blog
- [Claude Code を使いこなすためのベストプラクティス（実践検証付き）](https://tech.enechange.co.jp/entry/2026/02/16/195000) - ENECHANGE Developer Blog
- [claude-code-best-practice](https://github.com/shanraisshan/claude-code-best-practice) - GitHub (shanraisshan)
- [Claude Skill vs Command: 2026 Best Practices](https://oneaway.io/blog/claude-skill-vs-command) - OneAway
- [Claude Code 2.1.41–2.1.63: Eight Releases, One Platform Shift](https://www.vibesparking.com/en/blog/ai/claude-code/changelog/2026-03-04-claude-code-2141-2163-multi-agent-platform/) - Vibe Sparking AI
- [Claude Skills and CLAUDE.md: A Practical 2026 Guide for Teams](https://www.gend.co/blog/claude-skills-claude-md-guide) - Gend Blog

### コミュニティ記事（参考情報）

- [CLAUDE.md 運用のベストプラクティス: 失敗しないための7つの原則](https://zenn.dev/imohuke/articles/claude-code-best-practices-2026) - Zenn
- [CLAUDE.md や AGENTS.md のベストプラクティスな書き方](https://izanami.dev/post/47b08b5a-6e1c-4fb0-8342-06b8e627450a) - izanami.dev

---

*最終更新: 2026-03-07*
