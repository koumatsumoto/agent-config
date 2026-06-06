# Claude Code ベストプラクティス 2026-04

> Reference only. Not a runtime contract. 実際の運用契約は `templates/CLAUDE.md`、`templates/rules/`、`templates/skills/` を正とする。
>
> 確認日: 2026-04-19
>
> 調査範囲: 2026年4月時点で参照できる Claude Code 公式 docs と、2026-04-16 公開の Claude Opus 4.7 / Claude Code 更新情報のみ

2026年4月時点の Claude Code 公式 docs と Opus 4.7 公開情報を基準に、`CLAUDE.md`、rules、skills、subagents、hooks、settings の設計判断だけを圧縮した参考資料。モデル前提は Claude Opus 4.7。

## 参照した一次情報

- Best Practices for Claude Code
- How Claude remembers your project
- Extend Claude with skills
- Create custom subagents
- Hooks reference
- Claude Code settings
- Customize keyboard shortcuts
- Output styles
- Introducing Claude Opus 4.7

## 1. CLAUDE.md と memory

- `CLAUDE.md` は常設の事実と運用ルールに寄せる
- 長い手順やチェックリストは skill へ逃がす
- トピック別の条件付き指示は `.claude/rules/*.md` に分離する
- Claude は `CLAUDE.md` を強制設定としてではなく文脈として読む。短く具体的な記述ほど守られやすい
- ルート `CLAUDE.md` は毎セッション読み込まれる。ネストした `CLAUDE.md` は該当ディレクトリのファイルを触るときに遅延読み込みされる
- `CLAUDE.local.md` は同階層で `CLAUDE.md` の後に読まれる
- HTML コメントは注入時に除去されるため、人間向けメモに使える
- Auto memory は `CLAUDE.md` の代替ではない。Claude が発見した学習メモの保存先として使う

### Opus 4.7 前提の補足

- Opus 4.7 は instruction following が強く、以前のモデル向けに曖昧に書いたプロンプトや skill 契約は、そのままだと過剰に文字どおり解釈されうる
- そのため `CLAUDE.md`、rules、skills は「短くする」だけでなく、「曖昧さを残さない」ことが重要になる

### 実務上の指針

- `CLAUDE.md` には WHAT / WHY / HOW のうち、コードから読めない内容だけを書く
- ビルド・テスト・デプロイ・review のような反復手順は skill 化を優先する
- モノレポで不要な `CLAUDE.md` が混ざるなら `claudeMdExcludes` を使う

## 2. Rules

- `.claude/rules/*.md` はトピック別、または path-scoped の指示に向く
- root の `CLAUDE.md` に全ルールを押し込まず、対象ファイルが限定される内容は rules に切り出す
- `InstructionsLoaded` hook があるため、どの理由で rules が読まれたか観測できる
- rules もコンテキスト予算を消費する。1ファイル1責務を守る

### 実務上の指針

- グローバル規約は `CLAUDE.md`
- 言語別・領域別・path 条件付きの規約は rules
- 人間向け補足や背景説明は rules に長く書かず、別 doc へ逃がす

## 3. Skills

- Claude Code では custom commands は skills に統合された
- skill は「説明されるまで毎回読む instruction」ではなく「必要時にだけロードされる playbook」として使う
- `SKILL.md` は entrypoint。補助資料、テンプレート、スクリプトは skill ディレクトリに置ける
- `description` が自動選択の起点になるため、「何をするか」だけでなく「いつ使うか」を前方で明示する
- procedure が長いとき、`CLAUDE.md` ではなく skill に逃がすのが基本

### 実務上の指針

- review・commit・release など multi-step workflow は skill 向き
- 参照用の長文知識は supporting files に分離し、`SKILL.md` は契約と入口に絞る
- 自動起動させたくない workflow は invocation policy を絞る
- skill 本体では stop condition、success criteria、expected output を明記する

### Opus 4.7 前提の推論

- これは公式仕様ではなく運用上の推論だが、Opus 4.7 の instruction following と長時間タスク適性を踏まえると、review や commit の skill では verification step を明文化した方が挙動が安定しやすい

## 4. Subagents

- Claude Code には built-in の Explore / Plan などがあり、必要に応じて自動委譲される
- custom subagent は markdown + frontmatter で定義できる
- subagent は専用の context window、tool 制限、model、permission mode を持てる
- 大量の探索ログを親コンテキストに流したくないときに有効
- foreground / background 実行を選べる
- subagent は side task を分離するためのもの。ネスト前提の複雑な orchestration には向かない

### 実務上の指針

- 読み取り専用探索は subagent 化しやすい
- 定型的な専門レビューは custom subagent 候補
- ただし「毎回必要な project rule」は subagent ではなく `CLAUDE.md` / rules / skill で表現する

### Opus 4.7 前提の補足

- 以下は一次情報からの直接記述ではなく、公開されたモデル特性と Claude Code 機能拡張を踏まえた運用上の推論
- Opus 4.7 は長時間の multi-step work と role fidelity が強く、subagent を使う場合も「役割」「停止条件」「返却形式」を雑にしない方がよい
- モデル性能が上がったぶん、曖昧な reviewer / planner を作るより、用途を狭めた subagent の方が扱いやすい

## 5. Hooks

- hooks は command / http / prompt / agent の4種類がある
- scope は user / project / local / plugin / session / built-in に分かれる
- 長時間処理は `async: true` でバックグラウンド化できる
- `InstructionsLoaded`、`PreToolUse`、`PostToolUse`、`TaskCompleted` など event が多いので、まずは目的を絞る
- hooks は自動化の威力が高い一方、誤設定時の副作用も大きい

### 実務上の指針

- formatter / test / policy check の自動化は hook の好適領域
- まず command hook で最小構成を作り、必要時だけ prompt / agent hook を使う
- command hook では PATH 固定、入力サニタイズ、タイムアウト設定を徹底する
- 非同期 hook は制御を返せないので、blocking validation と background observability を分ける

## 6. Settings / output styles

- `settings.json` と `~/.claude.json` の役割は異なる。global-only 設定を `settings.json` に書くと schema error になる
- `editorMode`、`outputStyle`、`tui`、`useAutoModeDuringPlan` などは settings 側の責務
- output styles は tone / role / output format の調整用であり、project convention の置き場ではない

### 実務上の指針

- project rule は `CLAUDE.md`
- 表現スタイルは output styles
- Claude の挙動そのものを変える設定は settings

## 7. 2026-04 時点での Claude Code 固有アップデート

- Opus 4.7 で Claude Code の plan 既定 effort は `xhigh` に引き上げられた
- 難しい coding / agentic task では `high` または `xhigh` から始めるのが推奨されている
- Claude Code には `/ultrareview` が追加され、慎重な reviewer 相当の dedicated review session を起動できる
- Max 向けには auto mode が拡張され、長時間タスクを少ない割り込みで回しやすくなった

### 実務上の指針

- ここから先は 2026-04 の一次情報を踏まえた運用上の整理であり、仕様そのものではない
- Opus 4.7 では review / plan / subagent の指示を以前より短くできる一方、曖昧な裁量指示は減らす
- 深い review を常設 instruction に埋め込まず、必要時に skill や `/ultrareview` へ切り出す
- 長時間タスク向けの設定は「無確認で危険操作する」こととは分けて設計する

## 8. 2026-04 時点で特に意識すること

- Plan Mode は「探索と実装を分離する」ために使う。明確な小変更では過剰になりうる
- 自動 checkpoint / rewind があるため、危険な試行の前に過度に保守的になる必要はない
- skills と subagents が役割分担できるようになり、`CLAUDE.md` に長い手順を書く必要はさらに薄くなった
- output styles は coding policy ではなく、会話の出力レイヤだと整理する
- hooks と subagents は強力だが、導入コストも高い。まずは短い `CLAUDE.md` と skill の整理から着手するのが安定する

## 9. 推奨チェックリスト

- `CLAUDE.md` に procedure が増えすぎていないか
- path 条件付きの知識が rules に分離されているか
- 長い workflow が skill に移されているか
- subagent は本当に context 分離の価値があるか
- hooks は最小権限・最小副作用で構成されているか
- output style に project rule を混ぜていないか

## 出典

- https://code.claude.com/docs/en/best-practices
- https://code.claude.com/docs/en/memory
- https://code.claude.com/docs/en/skills
- https://code.claude.com/docs/en/sub-agents
- https://code.claude.com/docs/en/hooks
- https://code.claude.com/docs/en/settings
- https://code.claude.com/docs/en/output-styles
- https://www.anthropic.com/news/claude-opus-4-7
