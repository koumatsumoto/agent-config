# templates 配下 Markdown のコンテキスト削減方針

> 2026-04-11 更新: skill の invocation policy と横断評価は [20260411-skill-authoring-review.md](./20260411-skill-authoring-review.md) を正とする。この文書は主に context 削減の観点を残す。運用判断では新文書を優先し、この文書は補助資料として扱う。

`templates/skills/` 配下の Markdown を、精度を維持しながらコンテキスト負荷を下げるための方針。最新の Claude Code skill 運用と `docs/claude-code-best-practices-2026.md` を前提とする。

## コンテキストコストモデル

スキルのコンテキスト消費は呼び出し方式で大きく異なる。最適化の前にこの構造を理解する必要がある。

| 呼び出し方式 | description コスト | SKILL.md コスト | 参照 |
|---|---|---|---|
| Auto-invocable（デフォルト） | 常時（2% budget 共有） | 呼び出し時のみ | §3.8/3.9 |
| `disable-model-invocation: true` | ゼロ | 呼び出し時のみ | §3.8 |
| `context: fork`（スキル自体を分離実行） | 親の方式に依存 | 分離コンテキスト | §4.9 |
| Agent ツール経由（orchestrator パターン） | 親の方式に依存 | サブエージェントが Read | §4 |

現在の review orchestrator は `context: fork` ではなく Agent ツールでサブエージェントを生成し、各レビュースキルの SKILL.md を Read させる設計。効果は類似するが、メカニズムが異なる。

現在のスキル構成:

| スキル | 呼び出し方式 | 備考 |
|---|---|---|
| `km:review` | Auto-invocable | オーケストレーター。description が常時コンテキストに存在 |
| `km:code-review` | Auto-invocable | 単独実行時はメインコンテキスト、orchestrator 経由はサブエージェント |
| `km:quality-review` | Auto-invocable | 同上 |
| `km:doc-review` | Auto-invocable | 同上 |
| `km:intent-review` | Auto-invocable | orchestrator 経由ではメインコンテキストで実行 |
| `km:commit` | Auto-invocable | 副作用あり。AI 自動呼び出しを維持（ワークフロー上の利便性） |

review orchestrator がサブエージェントで code/quality/doc-review を実行する場合、各 SKILL.md は分離コンテキストで消費される。SKILL.md サイズが影響するのは主に単独実行時。

最適化の優先順位はコスト影響度で決まる:

1. 呼び出し制御（description コストの排除）
2. description の精度と長さ
3. SKILL.md の progressive disclosure
4. スキル間の重複排除
5. supporting file の再構成
6. 機械的圧縮（空行等）

## 現状

### ファイルサイズ

| ファイル | 行数 | 備考 |
|---|---:|---|
| `quality-review/quality-patterns.md` | 223 | 最大。詳細パターン集 |
| `quality-review/SKILL.md` | 162 | 最重量の SKILL.md |
| `review/SKILL.md` | 149 | オーケストレーション説明 |
| `doc-review/SKILL.md` | 138 | Phase 説明が長い |
| `code-review/SKILL.md` | 127 | quality/doc と重複多い |
| `intent-review/SKILL.md` | 105 | 出力定型の比率高い |
| `commit/SKILL.md` | 75 | 動的コンテキスト注入使用 |
| **合計** | **979** | 全ファイル 500行未満（公式推奨内） |

### コスト源

- 同じ意味の導入文や workflow が複数スキルに重複
- 実行時に不要な背景説明が SKILL.md 本体に残っている
- 報告フォーマットや例が各スキルに重複
- 詳細パターン集が overview ではなく本文に近い重さで配置

### 重複パターン（実測: ~150行 / 979行 = ~15%）

| パターン | 影響ファイル | 推定行数 | 具体例 |
|---|---|---:|---|
| 重大度定義 | code-review L99-103, quality-review L134-138 | 10 | 4段階定義が完全一致 |
| Phase 1（変更把握・分類） | code/quality/doc-review 各 Phase 1 | 30 | `git diff --name-only` + 4段階深度 + テーブル |
| 偽陽性フィルタリング | 全4レビュースキル | 28 | 除外カテゴリの構造が同一 |
| 報告テンプレート | 全4レビュースキル | 40 | 形式が同一。SQL injection 例が code/quality で一致 |
| サマリー出力 | 全4レビュースキル | 32 | 構造が同一、ラベルのみ差異 |
| コミットブロックルール | 全4レビュースキル | 4 | `CRITICAL/HIGH → ブロック` |

## 修正方針

### 1. 呼び出し制御を見直す

最も効果が大きい。`disable-model-invocation: true` を設定すると description がコンテキストから完全に除外される（§3.8）。

対象候補:
- 4レビューサブスキル: orchestrator 経由が主な実行パスなら、手動のみにすることで description 4件分を節約できる。ただし単独の `/km:code-review` 実行も現在サポートしているため、トレードオフ
- `km:commit` は副作用があるが、ワークフロー上 AI が自動で呼び出せる利便性が高いため auto-invocable を維持する

### 2. description の精度を上げる

Auto-invocable スキルの description は常時コンテキストに存在する（§3.9: 全スキルの description 合計で 2% budget）。現在6スキルで合計約 2,000文字。1M コンテキストの 2% = 20,000文字なので budget 内だが、スキル追加時に注意が必要。

- いつ使うかを明記する
- いつ使わないかも必要なら明記する
- 三人称で書く（§3.5: description はシステムプロンプトに注入される）

良い例: `Use when the user requests a code review of uncommitted changes. Skip for docs-only changes.`
悪い例: `Comprehensive code review skill.`

### 3. SKILL.md を overview に寄せる

SKILL.md は詳細仕様書ではなく、実行の入口として設計する（§3.6 Progressive Disclosure）。

残す内容: 何をするか / いつ使うか / どう進めるか / 何を出力するか
逃がす内容: 背景説明 / 長い例 / 詳細パターン

詳細はスキルディレクトリ内の supporting files に分離し、SKILL.md から「必要時にこのファイルを読む」と案内する。参照は1階層のみ（§3.6）。

```
skill-name/
├── SKILL.md        # overview + navigation
├── examples.md     # 報告サンプル
├── references.md   # 詳細パターン・定義
└── checklists.md   # 確認項目
```

### 4. 重複を構造で解消する

前節の重複パターン表を基に、以下を検討する:

**報告テンプレートとサマリー出力**: 4スキルで同一構造。共通の `review-common/report-format.md` に抽出するか、各 SKILL.md の examples.md に移して本体を短縮する。

**重大度定義**: code-review と quality-review で完全一致。共通 reference 化するか、意図的な重複として維持する（self-contained のため）。判断を明文化する。

**Phase 1（変更把握・分類）**: 3スキルで同構造。orchestrator が Phase 1 を担当し、サブスキルは Phase 2 以降のみ実行する現在の設計（review/SKILL.md Phase 3 参照）を徹底すれば、各サブスキルの Phase 1 は「単独実行時のみ参照」と位置づけて簡素化できる。

**workflow の二重説明**: 多くの SKILL.md で Workflow 節と各 Phase 節が同じ内容を繰り返している。Workflow にはフェーズ名だけ、各 Phase には実行ルールだけに統一する。

### 5. 「削除」より「分離」を優先する

例や詳細説明は削除より分離の方が精度を維持しやすい。

- 報告フォーマット例 → `examples.md`
- 重大度定義 → 共通 reference
- アンチパターン列挙 → checklist と examples に分割

### 6. 箇条書きは短く、抽象度をそろえる

1項目1意味。修飾語を減らし、同義語の並列を避ける。詳細な具体例は supporting file に寄せる。

### 7. 空行削減は最後に行う

効果は限定的だが安全。連続空行を1行に統一、見出し前後の過剰な空行を削除。

## SKILL.md に残すもの / 逃がすもの

**残す**: trigger 条件、非 trigger 条件、実行手順の骨子、ブロック/停止条件、出力要件、supporting files の参照条件

**逃がす**: 長い背景説明、重複する重大度定義、長い報告サンプル、詳細アンチパターン列挙、言語別の細かい補足

## ファイル別の修正案

### `commit/SKILL.md`（75行）

- Auto-invocable を維持（ワークフロー上 AI が自動で使えることが重要）
- 動的コンテキスト注入（`!`command``）は best practice（§3.12）。維持する
- サンプルコミットは2件あるが、1件に減らすか examples.md に移す

### `review/SKILL.md`（149行）

- オーケストレーターとして auto-invocable を維持。description の最適化が最重要（現在 ~350文字）
- Phase 3 のサブエージェント指示は各3行で簡潔。維持
- 統合レポート例（L111-149）は examples.md に分離可能

### `code-review/SKILL.md`（127行）

- `レビューの重心` を1段落に縮める
- 問題報告例（L121-127）は quality-review と SQL injection 例まで一致。examples.md に分離
- サマリー出力（L109-115）も定型。分離候補
- 重大度定義（L99-103）は quality-review L134-138 と完全一致。共通化 or 意図的重複を決める

### `quality-review/SKILL.md`（162行）

- 8特性の確認の問いが本体の大部分を占める。これは本スキルの中核価値であり、残す
- 報告テンプレート（L152-162）と サマリー（L142-150）は code-review と同一構造。分離候補
- `quality-patterns.md` を読む条件を明示する（現在 L37 にあるが、読むタイミングの条件が不明確）

### `quality-review/quality-patterns.md`（223行）

- 最大の削減余地。各特性を「必須観点」と「追加例」に分割する
- Python/TS 固有の記述は coding style rules に移すか reference 化
- 近い意味の例は抽象化して統合

### `doc-review/SKILL.md`（138行）

- Phase 2-4 の導入文を短くし、確認観点を主体にする
- `見落としやすいパターン` は代表例だけ残す
- 偽陽性フィルタリング（L95-104）は他スキルと同構造。簡素化候補

### `intent-review/SKILL.md`（105行）

- 構造化出力の詳細例（L66-74）を examples.md に分離
- 問題報告フォーマット（L97-105）も定型。分離候補
- CRITICAL を定義しない設計判断は意図的。維持する

### `templates/CLAUDE.md` と `templates/rules/*.md`

- スキル本体ほど優先度は高くない
- preload されやすいため、共通文や長い説明は短文化する

## 優先順位

効果が大きい順に進める:

1. **呼び出し制御**: レビューサブスキルの呼び出し方式を評価（orchestrator 経由が主なら `disable-model-invocation` を検討）
2. **description 精度**: 残る auto-invocable スキルの description を精査。trigger/除外条件を明確化
3. **SKILL.md overview 化**: 背景説明と長い例を supporting files に分離。Phase 1 共通部分の簡素化
4. **重複排除**: 報告テンプレート・サマリー・重大度定義の共通化方針を決定し、実行
5. **supporting file 再構成**: `quality-patterns.md` を必須観点/追加例に分割。言語固有の記述を rules に移動
6. **機械的圧縮**: 空行・箇条書きの長さを整える

## 補足

精度を落とさずに軽くするには、「何を削るか」より「何をどこに置くか」が重要。そして最も効果が大きいのは、description を常時コンテキストに載せるかどうかの判断（呼び出し制御）である。

参照: `docs/claude-code-best-practices-2026.md` §3.5-3.9（Skills）, §4.9（Subagent 連携）
