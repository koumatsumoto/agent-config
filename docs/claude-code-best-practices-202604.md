# Claude Codeベストプラクティス 2026-08

> 参考資料。実行時契約ではない。実際の運用契約は`templates/CLAUDE.md`、`templates/rules/`、`templates/skills/`を正とする。
>
> 確認日: 2026-08-09
>
> 調査範囲: Claude Code公式文書、公式変更履歴、Claude Opus 4.7の公開情報

2026年8月9日にClaude Code公式文書とOpus 4.7の公開情報を再確認し、`CLAUDE.md`、Rules、Skills、Subagents、Hooks、Settingsの設計判断を簡潔に整理した。モデル前提はClaude Opus 4.7である。

## 参照した一次情報

- Best Practices for Claude Code
- How Claude remembers your project
- Extend Claude with skill
- Create custom subagents
- Hooks reference
- Claude Code 設定
- Customize keyboard shortcuts
- Output styles
- Introducing Claude Opus 4.7

## 1. CLAUDE.mdとメモリ

- `CLAUDE.md` は常設の事実と運用ルールに寄せる
- 長い手順やチェックリストは skill へ逃がす
- トピック別の条件付き指示は `.claude/rules/*.md` に分離する
- Claude は `CLAUDE.md` を強制設定としてではなく文脈として読む。短く具体的な記述ほど守られやすい
- ルート `CLAUDE.md` は毎セッション読み込まれる。ネストした `CLAUDE.md` は該当ディレクトリのファイルを触るときに遅延読み込みされる
- `CLAUDE.local.md` は同階層で `CLAUDE.md` の後に読まれる
- HTML コメントは注入時に除去されるため、人間向けメモに使える
- Auto memoryは`CLAUDE.md`の代替ではない。Claudeが発見した学習メモの保存先として使う

### Opus 4.7 前提の補足

- Opus 4.7は指示追従が強く、曖昧な指示や過剰な制約が、意図以上に厳密に適用される場合がある
- そのため `CLAUDE.md`、ルール、skill は「短くする」だけでなく、「曖昧さを残さない」ことが重要になる

### 実務上の指針

- `CLAUDE.md`には、動作、理由、手順のうち、コードだけでは分からない内容を書く
- ビルド、テスト、デプロイ、レビューのような反復手順はskill化を優先する
- モノレポで不要な `CLAUDE.md` が混ざるなら `claudeMdExcludes` を使う

## 2. Rules

- `.claude/rules/*.md`はトピック別、またはパスで適用範囲を限定する指示に向く
- 基点の`CLAUDE.md`に全ルールを押し込まず、対象ファイルが限定される内容はルールに切り出す
- `InstructionsLoaded` hookがあるため、どの理由でルールが読まれたか観測できる
- ルールもコンテキスト予算を消費する。1ファイル1責務を守る

### 実務上の指針

- グローバル規約は `CLAUDE.md`
- 言語別・領域別・path 条件付きの規約はルール
- 人間向け補足や背景説明はルールに長く書かず、別の文書へ移す

## 3. Skills

- Claude Codeではカスタムコマンドがskillに統合された
- skillは「毎回読み込む指示」ではなく、「必要なときだけ読み込む手順書」として使う
- `SKILL.md` は入口。補助資料、テンプレート、スクリプトは skill ディレクトリに置ける
- `description` が自動選択の起点になるため、「何をするか」だけでなく「いつ使うか」を前方で明示する
- 手順が長いとき、`CLAUDE.md`ではなく skill に逃がすのが基本

### 実務上の指針

- レビュー、コミット、リリースなど、複数段階の作業手順はskillに向く
- 参照用の長文知識は補助ファイルに分離し、`SKILL.md` は契約と入口に絞る
- 自動起動させたくない作業手順は起動条件を絞る
- skill本体では停止条件、成功条件、期待する出力を明記する

### Opus 4.7 前提の推論

- これは公式仕様ではなく運用上の推論だが、Opus 4.7の指示追従と長時間タスク適性を踏まえると、レビューやコミットのskillでは検証手順を明文化した方が挙動が安定しやすい

## 4. Subagents

- Claude Code には built-in の Explore / Plan などがあり、必要に応じて自動委譲される
- custom subagentはmarkdown + frontmatterで定義できる
- subagentは専用のcontext window、tool制限、model、permission modeを持てる
- 大量の探索ログを親コンテキストに流したくないときに有効
- foreground / background 実行を選べる
- subagentは副次的な作業を分離するためのもの。ネスト前提の複雑なオーケストレーションには向かない

### 実務上の指針

- 読み取り専用探索はsubagentへ分離しやすい
- 定型的な専門レビューはcustom subagentの候補になる
- ただし「毎回必要なproject rule」はsubagentではなく`CLAUDE.md` / ルール / skillで表現する

### Opus 4.7 前提の補足

- 以下は一次情報からの直接記述ではなく、公開されたモデル特性と Claude Code 機能拡張を踏まえた運用上の推論
- Opus 4.7は長時間の複数段階作業と役割への忠実性が強く、subagentを使う場合も「役割」「停止条件」「返却形式」を明確にする
- モデル性能が上がったぶん、曖昧なレビュアや計画担当を作るより、用途を狭めたsubagentの方が扱いやすい

## 5. Hooks

- hookはcommand / http / prompt / agentの4種類がある
- scope は user / project / local / plugin / session / built-in に分かれる
- 長時間処理は `async: true` でバックグラウンド化できる
- `InstructionsLoaded`、`PreToolUse`、`PostToolUse`、`TaskCompleted` など event が多いので、まずは目的を絞る
- hookは自動化の威力が高い一方、誤設定時の副作用も大きい

### 実務上の指針

- formatter / test / policy check の自動化は hook の好適領域
- まず command hook で最小構成を作り、必要時だけ prompt / agent hook を使う
- command hookでは PATH 固定、入力サニタイズ、タイムアウト設定を徹底する
- 非同期 hook は制御を返せないので、blocking validation と background observability を分ける

## 6. Settings / Output Styles

- `settings.json` と `~/.claude.json` の役割は異なる。global-only 設定を `settings.json` に書くと schema error になる
- `editorMode`、`outputStyle`、`tui`、`useAutoModeDuringPlan` などは設定側の責務
- output styles は tone / role / output format の調整用であり、project convention の置き場ではない

### 実務上の指針

- project rule は `CLAUDE.md`
- 表現スタイルは output styles
- Claude の挙動そのものを変える設定は設定

## 7. 2026-04 時点での Claude Code 固有アップデート

- Opus 4.7 で Claude Code の plan 既定 effort は `xhigh` に引き上げられた
- 難しい coding / agentic taskでは `high` または `xhigh` から始めるのが推奨されている
- Claude Code には `/ultrareview` が追加され、慎重なレビュアに相当する専用レビューセッションを起動できる
- Max 向けには auto mode が拡張され、長時間タスクを少ない割り込みで回しやすくなった

### 実務上の指針

- ここから先は 2026-04 の一次情報を踏まえた運用上の整理であり、仕様そのものではない
- Opus 4.7ではレビュー、計画、subagentの指示を以前より短くできる一方、曖昧な裁量指示は減らす
- 深い review を常設 instruction に埋め込まず、必要時に skill や `/ultrareview` へ切り出す
- 長時間タスク向けの設定は「無確認で危険操作する」こととは分けて設計する

## 8. 2026-04 時点で特に意識すること

- Plan Mode は「探索と実装を分離する」ために使う。明確な小変更では過剰になりうる
- 自動 checkpoint / rewind があるため、危険な試行の前に過度に保守的になる必要はない
- skillとsubagentが役割分担できるようになり、`CLAUDE.md`に長い手順を書く必要はさらに薄くなった
- output styles は coding policyではなく、会話の出力レイヤだと整理する
- hookとsubagentは強力だが、導入コストも高い。まずは短い`CLAUDE.md`とskillの整理から着手するのが安定する

## 9. 推奨チェックリスト

- `CLAUDE.md` に手順が増えすぎていないか
- path 条件付きの知識がルールに分離されているか
- 長い作業手順をskillへ分離しているか
- subagentには本当にコンテキスト分離の価値があるか
- hookは最小権限・最小副作用で構成されているか
- output style に project rule を混ぜていないか

## 出典

- https://code.claude.com/docs/en/best-practices
- https://code.claude.com/docs/en/memory
- https://code.claude.com/docs/en/skills
- https://code.claude.com/docs/en/sub-agents
- https://code.claude.com/docs/en/hooks
- https://code.claude.com/docs/en/settings
- https://code.claude.com/docs/en/output-styles
- https://code.claude.com/docs/en/changelog
- https://www.anthropic.com/news/claude-opus-4-7
