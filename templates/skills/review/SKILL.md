---
name: km:review
description: >
  Reviews code changes (uncommitted, commits, PRs, subtrees) for bugs, design, security, and
  quality. Use when the user says "レビューして" or "PR をレビューして".
argument-hint: "[target] [level]"
---

# Review

複数の観点を統合する **単発診断** の review orchestrator。レビュー対象を引数 / 会話文脈から決め、レベルに応じて Phase を起動する。

## Success Criteria

- 変更タイプと対象スコープに応じた Phase / レビュアを正しく選ぶ
- コードレビュー層 (Phase 2 + Phase 3 の architect / security / adversary) を Phase 4 で統合し、CRITICAL または HIGH があれば BLOCKED とする
- `PASS` を出す前に、見落としが無いかを能動的に検証する (Phase 4 の能動的検証・PASS 反証)。ただし裏づけのない疑いで BLOCKED を量産しない
- doc-review (Phase 5) はコードが確定した最終状態に対して実施する
- 実行した Phase とスキップした Phase の両方が分かるレポートにする

## Phase 1: 引数解析 + 対象スコープ解決 + 変更タイプ/レベル決定

### Phase 1a. 引数パース仕様

`$ARGUMENTS` は単一文字列。flag 抽出 → 残り token 分類の順で解析する。

1. **flag 抽出 (位置不問)**: `--` プレフィックス token を先に取り出す
   - `--uncommitted`: 明示の未コミットモード (値なし)
   - `--repo <subtree>`: 直後の token を subtree value として同時消費。直後が無い / level token / 別 flag なら「サブツリー必須」エラー終了
   - `--recheck`: 再検証モード (値なし)。BLOCKED 後に修正差分を伴う再依頼のとき使う。scope 解決は通常どおり (修正差分を対象にする)。詳細と起動条件は「再検証モード (recheck)」節
2. **残り token を順序評価**: 先頭一致で以下に分類 (同種が複数あれば最後を有効)
   1. `^pr$` または `^pr:[0-9]+$` → PR モード
   2. `..` を含む → コミット範囲モード
   3. `^[0-9a-f]{7,40}$` → 単一コミットモード (sha)
   4. `^(quick|standard|thorough)$` → level 指定
   5. それ以外 → 曖昧入力として警告
   6. 全 token なし → 既定 (未コミット差分)
3. **裸の数字 `42` は曖昧入力として警告**。`km:github-workflow` の `[issue-number]` 引数との混同を防ぐ。明示的に `pr:42` を要求する
4. **`--repo` は他のモード flag (`pr` 系・`--uncommitted`) と同時指定できずエラー終了** (排他モード)。**`--recheck` は `--repo` と同時指定不可** (recheck は修正差分を前提とし、`--repo` は差分でなく現状コード全体を対象とするため)

### Phase 1b. 対象スコープ解決

| 対象 | コマンド |
|---|---|
| 未コミット (既定) | `git diff` + `git diff --name-only` |
| `<base>..<head>` | `git diff <base>..<head>` |
| `<sha>` | `git show <sha>` |
| `pr` / `pr:<n>` | `gh pr diff [<n>]` (失敗時は別スコープ指定を促す) |
| `--repo <subtree>` | `git ls-files <subtree>` で対象ファイル列挙し各ファイルを Read (diff ではなく現状コード全体が対象) |

base/head/sha が解決できなければエラー終了。下位コンポーネント (Phase 2 / Phase 3 reviewers / doc-review) は「解決済みのファイル一覧 + diff 内容」を共通コンテキストで受け取る (`--repo` 時は diff ではなく現状コード本文)。

**Context budget 防御 (`--repo` のみ)**: 対象テキスト (binary / lockfile / generated は除く) が Phase 3 並列レビュアの context に収まる規模か見積もる。超えるならレビュー品質が落ちるので、Phase 2 に進まずサブツリーを絞るよう促す。

### Phase 1c. 変更タイプ判定とレベル選択

変更タイプの判定入力:

| 対象 | 判定入力 |
|---|---|
| 未コミット | ファイル拡張子・変更パターン |
| `<base>..<head>` / `<sha>` | 拡張子・変更パターン + コミットメッセージ (`refactor:` 等の Conventional 接頭辞) |
| `pr` / `pr:<n>` | `gh pr view` のタイトル/ラベル + diff |
| `--repo <subtree>` | 常に `mixed` 扱い (判定省略) |

コミットメッセージ取得失敗 / `gh pr view` 失敗時は拡張子のみで判定し変更構成は `mixed` にフォールバック。

**挙動資産 (behavior asset) の判定**: ルーティングは拡張子でなく挙動への影響で決める。エージェント指示資産 (skill / rule / `CLAUDE.md`・`AGENTS.md` / エージェントに読み込まれて挙動を規定する prompt 定義) は「読まれて実行される」挙動定義であり、`.md` でも実質コードなので **`docs-only` にせずコード相当に分類する**。

- **第一級の判定基準**: 「エージェントに読み込まれて挙動を規定する prompt 定義か」。下の (a) パス・(b) 内容シグナルは **非網羅的な例** であり、リストに無い新種の prompt 資産 (別ディレクトリの output-style・persona 定義など) でもこの一般基準に立ち返って判定する
- **(a) パスシグナル (例)**: `**/skills/**`・`**/rules/**`・`**/commands/**`・`**/agents/**`・`**/output-styles/**`・`CLAUDE.md`・`AGENTS.md`・`.claude/`・`.agents/` 配下
- **(b) 内容シグナル (例)**: frontmatter に skill / agent / output-style 等の定義 (`name:` + `description:` 等) を持つ、本文がエージェントへの命令・手順として書かれている
- **除外と優先順位 (過剰包摂の防止)**: 人間向けの手順書・説明 (README・runbook・tutorial・設計 doc・CHANGELOG) は挙動資産でない。ただし **(a) または (b) に該当すれば挙動資産と判定し**、除外は **(a)(b) いずれにも該当しない場合にのみ** 適用する (説明的な文体で書かれた rule/skill を除外側へ倒さない)
- **fail-safe は code 側**: 判定が割れる・確信が持てないときは挙動資産 (コード相当) に倒す (「迷ったら `mixed`」)。挙動資産を `docs-only` に落として Phase 2/3 をスキップさせる fail-open を避ける
- **効果**: 挙動資産を **含む** diff は (人間向け docs の有無を問わず) `code+docs` とする — コード層 = Phase 2/3 が挙動を、doc 層 = Phase 5 関心 B が散文としての整合を見る。挙動資産が `docs-only` に落ちて Phase 2/3 をスキップする経路を塞ぐ

変更構成 (正規ラベル): `docs-only` / `code-only` / `code+docs` / `test-or-config-or-chore-only` / `mixed`。レベルは `thorough` / `standard` / `quick` で、Phase 1a で抽出されなければ会話文脈から推論、それも無理なら既定 `standard`。

**レベル推奨 (助言。判定は変えない)**: 確定したレベルとは別に、diff の特性から推奨レベルを理由 1 行付きで提示する。特性の軸: 規模 (変更行数・ファイル数) / 新規経路の有無 (新関数・エンドポイント・分岐・手順) / 不可逆性 (公開契約・スキーマ・データ移行) / 攻撃面 (認証認可・秘密情報・外部入力) / 挙動資産か。**ユーザの明示指定が常に優先**され、推奨は実行レベルを自動で変えない。推奨と実行レベルが食い違う場合のみ、統合レポートに 1 行明記する (例:「推奨 thorough / 実行 standard — 新規経路 + 不可逆契約変更のため」)。

### 引数なし呼び出しのデフォルト動作

`/km:review` (引数なし) では以下のフォールバック順で対象を決定する。`km:plan` / `km:github-workflow` 経由の dispatch でも同じ動作:

1. `git diff` で未コミット差分の有無を確認 → あれば未コミットモード
2. 未コミットなしかつ現ブランチが push 済みなら `gh pr diff` (current branch の PR) を試行 → 成功すれば PR モード
3. それも無ければ「対象がないため終了」と出力

## Phase 2: コードレビュー (generalist)

`code-review.md` に従い main コンテキストでレビューする。コードの正しさ・規約・可読性を見る generalist レビュー。能動的な敵対分析の主担当は Phase 3 adversary だが、本 Phase も code-review.md Step 2 の範囲 (前提の能動破壊・diff 外照合による不変条件の継承確認) を行う (重複は Phase 4 dedup が吸収)。

**起動条件**: docs-only 以外 (`code-only` / `code+docs` / `test/config/chore` / `mixed`) で常時起動。

**入力**: Phase 1b で解決した「変更ファイル一覧 + diff 内容」、Phase 1c の変更タイプ。対象が **挙動資産** に分類された実行では、`references/prompt-asset-lens.md` を読ませ、汎用レンズを prompt 資産の意味へ写像して当てさせる (standard では Phase 2 が唯一のコード層レビュアのため、ここへの配線が無いと読み替えが既定経路に届かない。code diff の実行では読み込ませない)。

**出力**: 重大度別件数 (CRITICAL/HIGH/MEDIUM/LOW) + 個別所見。

## Phase 3: 第三者レビュー (3 名並列)

`thorough` レベルで起動する。`docs-only` / `test-or-config-or-chore-only` では起動しない。

**内容ベースの昇格**: `quick` / `standard` でも、diff が高リスク領域に触れる場合は該当専門家を起動してよい。**高リスク領域と owner**: 覆すのが高コストな決定 (公開 API・契約・スキーマ・データモデル等の one-way door) → **architect**、認証 / 認可・データの移動 / 削除 / マイグレーション・秘密情報・LLM/AI の tool 実行 / 入力境界 → **security / adversary**。昇格した場合は統合レポートに昇格理由を 1 行記録する。

レビュアは **architect / security / adversary の 3 名**。各々が同じ diff を別視点で**独立に**レビューする ―― 暫定判定も他レビュアの所見も渡さない (アンカリングを避け視点の多様性を最大化する。重複の集約は Phase 4 統合が行う)。

### `<review skill root>` プレースホルダの解決規約

orchestrator (LLM) は実行環境の install root を `<review skill root>` の絶対パスとして解決する (Claude Code は `~/.claude/skills/review/`、Codex CLI は `~/.agents/skills/review/`。いずれも `~` を展開した絶対パスにする)。この解決は (a) subagent に渡す prompt template の文字列、(b) **subagent / main コンテキストが Read する静的ファイル本文** のいずれにも適用される。subagent は静的ファイル本文の `<review skill root>` を読んだ際も自前で絶対パスに置換してから Read する (相対パス・未展開の `~` は subagent の working directory 依存で Read が失敗する)。

### 起動方法

実行環境の subagent 機構 (Claude Code は Task tool、Codex CLI は subagent) で 3 名を **同一メッセージ内に並列起動**する。**最上位 model (Opus 等) + 高 effort** で動かす (Phase 3 は `thorough` / 高リスク昇格時のみ走るためコスト増は限定的。effort を直接指定できなければ可能な範囲で高く保つ)。参照パスは `<review skill root>/...` 形式で書き、`<role>` 等のプレースホルダは orchestrator が置換してから渡す。orchestrator は各レビュアに **レビュア別の報告出力ファイルパス** (`<report dir>/phase3-<role>.md`) を割り当てる (`<report dir>` の決め方は「報告のファイル永続化」節)。対象が挙動資産に分類された実行でのみ、Read 順序に prompt-asset-lens の 1 行を挿入する (code diff の実行では挿入しない)。各 subagent に次のプロンプトを渡す:

```
あなたは km:review Phase 3 の <role> レビュアです。

## 役割の前提
- 同じ diff を architect / security / adversary の 3 名が並列で別視点でレビューしています
- あなたは <role> の視点に集中してください
- 他レビュアの所見・全体の暫定判定は渡されません (独立レビュー)。レーンの扱い・偽陽性フィルタは report-format.md に従う。重複の集約は Phase 4 が行うので重複回避を予測しなくてよい

## Read 順序
まず `<review skill root>/experts/<role>.md` と `<review skill root>/experts/report-format.md` を読み (役割と判定基準・確信度・役割固有フィールドを把握)、その後 diff を pre-scan する。
<挙動資産の実行のとき orchestrator が挿入: 加えて `<review skill root>/references/prompt-asset-lens.md` を読み、担当観点を prompt 資産の意味へ写像して当てる>

## レビュー対象
- 変更ファイル一覧: <Phase 1b の出力>
- diff 内容 (`--repo` 時は diff ではなく現状コード本文): <raw diff>
- 変更タイプ / 規模: <Phase 1c の出力>

## 既知情報
- 意図情報 (km:plan issue 本文 / 会話文脈):
  <intent または "no intent context">
  intent がある場合は「diff が intent を達成しているか」を担当観点で 1 行コメントする。**具体的・反証可能な DoD / 完了条件が与えられていれば、それを goal anchor として信頼し** (km:review 側で完了条件を再導出・拡張しない)、diff が DoD を満たすかだけを軽く確認する

## 失敗ケースの扱い
- 該当観点なし: report-format.md の「指摘ゼロ時」フォーマット
- context 不足で判定しきれない: 「判定保留」セクションに「何があれば判定できるか」を書く
- diff が大きすぎる: 担当観点に該当しそうな箇所だけ深掘り、それ以外は判定保留
- diff から判定するために repo 内の近隣ファイルが必要なら、**判定に必要なだけ Read してよい** (固定上限なし。context budget を見て調整)。優先順位は ①該当コードの呼び出し元 / 呼び出し先 ②既存テスト ③同種の既存実装 ④関連 middleware / interceptor。**「判定保留」にする前に「あと何を読めば確定するか」を必ず一度試す**。脱線・budget 超過は避ける

## 出力形式と報告の書き出し (返信前に必須)
所見は `<review skill root>/experts/report-format.md` に従う (判定基準・確信度・役割固有の補足・検証済み所見の書き方はそこに集約)。
- **返信の前に**、報告全文を割り当てられたファイル `<report file>` へ書き出し、末尾に完了 sentinel `<!-- km:review:report:complete -->` を付す。**推奨**: 所見が一次形成できたら一度 draft を sentinel 無しで書き出す (分析中の中断からの回収範囲を広げる。義務ではない — 末尾の自己反証で改訂しうるため強制はしない)
- 返信メッセージは **件数行 + `<report file>` のパス + CRITICAL / HIGH のタイトル列挙** に限る。詳細はファイルに置く。返信とファイルが食い違う場合は **ファイルを正** とする (真実の所在を一意化)
- 他レビュアの報告ファイルは読まない (並列独立を保つ)
```

`<role>` は `architect`, `security`, `adversary` のいずれか。3 つを同一メッセージ内で発行する (sequential ではなく parallel)。`<report file>` は orchestrator が割り当てた `<report dir>/phase3-<role>.md`。

**ロール識別子と出力見出しのマッピング**は `report-format.md` の機械可読契約を単一ソースとする (`architect` → `### システムアーキテクト` 等。パース対象文字列なので二重管理しない)。

### 各レビュアの視点

| レビュア | 視点 | 重点 (担当 ISO/IEC 25010) |
|---|---|---|
| architect | 長期・横断・非機能 | **覆すのが高コストな決定** (公開 API・契約・スキーマ・データモデル・依存方向) と **repo 全体に複製される pattern** を重点に、不可逆 × 波及大に絞って firm に踏み込む (2, 3, 7, 8) |
| security | 脅威モデル・攻撃面 | 攻撃者視点での脆弱性・攻撃面・LLM 統合 (6, 9) |
| adversary | 敵対的批判 | 変更を「正しくない / 目的を達成しない」と仮定し前提・不変条件を攻撃、最悪入力で壊す。境界・異常系・信頼性・intent 達成 (1, 4, 5) |

Phase 2 ↔ architect の住み分けは `references/scope-alignment.md` に集約。

## 報告のファイル永続化 (中断時の回収)

Phase 3 の並列 subagent は長時間実行で中断 (API エラー・セッション制限) しうる。報告をファイルへ確定させ、中断しても書けたところまで回収できるようにする。**信頼性の改善** であり、トークン削減は主張しない (Phase 4 は dedup のため全所見を読む)。返信前の必須書き出しは「分析完了後・返信直前」の中断を回収可能にする。分析中の中断は返信前の 1 回だけでは全損のままなので、下の中間チェックポイント (推奨) がカバー範囲を広げる。

- **書き出し先 `<report dir>`**: repo root の `.km-review/<scope-slug>/` を既定とする (`<scope-slug>` は対象スコープから作る短い識別子)。セッションをまたいで発見可能な固定パスであることが要件 (recheck の入力源。session 固有 scratchpad 単独は不可)
- **git 追跡への非混入 (Phase 3 dispatch 前に orchestrator が実施)**: (1) `git ls-files` で対象が既追跡でないか確認し、**既追跡なら自動書き込みせずユーザに確認して停止** (`.plan/` と同じ安全分岐)。(2) `git check-ignore` で無視済みなら何もしない。(3) 未無視なら `.git/info/exclude` に `/.km-review/` を追記する。レビュー報告は当該レビュー限りの ephemeral な scratch なので、committed 管理する `.plan/` と違い対象 repo の committed `.gitignore` は汚さず exclude を選ぶ。これらのファイルを `git add` しない
- **run 同一性 (陳腐化ファイルの誤読防止)**: `<scope-slug>` は run 時刻に依らず (引数なし呼び出しは常に `uncommitted` へ集約) 同一スコープの別 run が同じパスを再利用する。**非 recheck の Phase 3 起動前に、orchestrator は `<report dir>` の `phase3-*.md` と `integration.md` を空にする** (前 run の完了 sentinel 付きファイルを今回の結果と誤認して黙って統合するのを防ぐ)。recheck は前 run の `integration.md` を明示的に入力源として読むので掃除の対象外
- **Phase 3 レビュア**: 返信前に `<report dir>/phase3-<role>.md` へ全文 + 完了 sentinel を書く。**推奨**: 所見が一次形成できた時点で一度 draft を sentinel 無しで書き出す (分析中の中断からの回収範囲を広げる。義務ではない — 末尾の自己反証で所見を改訂しうるため。sentinel 無し draft は下の部分回収規則が拾う)
- **Phase 4**: 各 `phase3-<role>.md` をファイルから読み込んで統合し、**統合レポートも `<report dir>/integration.md` へ書き出す** (recheck の入力源)
- **中断時の部分回収**: 完了 sentinel の無いファイルは中断された部分報告として扱い、**書けた所見まで回収** して `integration-report.md` の rule 6 (安全側 BLOCKED) に接続する
- **lifecycle**: `<report dir>` の内容は当該レビュー限りの作業物。PASS 確定後は不要で、機微な所見を含む場合はユーザ判断で削除してよい (git 非追跡なので放置しても commit されない)

## Phase 4: 統合 + コミット判定 (main コンテキスト)

Phase 2 / Phase 3 (architect / security / adversary) の所見を main コンテキストで統合する。レビューの最大コストは false negative (見落とし) なので、main コンテキストの能力 (ツール実行・長コンテキスト・自己反証) を **誤った PASS を出さないこと** に使う。

1. **中央 dedup**: 全所見を `(file, ±5 行, 根本原因)` でグルーピングし、同一欠陥を別角度から記述したものも束ね、最も証拠の濃い所見を残して併合注記する。判定基準は `<review skill root>/integration-report.md` の「中央 dedup ルール」。
2. **偽陽性確認 (substantiation)**: 各 CRITICAL/HIGH が diff から具体的に裏づくかを確認し、裏づかない指摘は降格する。
3. **能動的検証** (`thorough` / 高リスク昇格時、**HIGH 以上の `[possible]` / `[likely]` のみ**): read-only 静的推測で止まっている HIGH 以上を main コンテキストで軽量に実証し確定 / 棄却する。手段は ①呼び出し元 / 先を辿る ②既存テストを走らせる (非破壊で安全なときのみ) ③最小再現を組む。`[possible]` → `[confirmed]` に格上げ、裏づかなければ降格 / drop。確定 / 棄却に必要な分だけ行う (深掘りしすぎない)。Phase 3 subagent は read-only 推測のまま据え置き、確定はここに集約する。
4. **暫定判定**: 重大度を合算し、CRITICAL/HIGH があれば `BLOCKED`、なければ `PASS` 候補。
5. **completeness**:
   - **`PASS` 候補のとき (見落としを能動的に反証する)**:
     1. この diff が **実際に触れた surface** を短く列挙する (公開 API・契約 / 状態・データ移動 / IO・信頼境界 / 認証認可 / 並行・時間 のうち該当軸だけ)。永続化・全レビュアへの共有はせず、本手順の思考補助に限る
     2. 全所見を一旦伏せて diff を独立に 1 パスし、「全レビュアが見逃した CRITICAL/HIGH が隠れているなら **どの surface か** / なぜ 3 独立レビュア + Phase 2 が揃って見逃しうるか」を問う (anchoring 回避)
     3. **具体的に潜みうる箇所を名指せたら**、`thorough` / 高リスク時は手順 3 の能動的検証で確定 / 棄却する。確定すれば正規所見に追加し `BLOCKED` に更新。安価に解決できない (または検証手段がない level) ときは「確認推奨」ノート (重大度なし・件数に算入せず `PASS` は維持) に「何が分かれば PASS を覆せるか」を 1 行記録する
   - **検証済み所見 (reviewed-clear) の消費**: Phase 3 レビュアの「検証済み所見」(report-format.md) は、**どのレビュアも検証していない未カバー surface の優先順位付けにのみ** 使う。3 制約: (a) **手順 1 の surface 列挙は reviewed-clear を見ずに diff から独立に行い**、reviewed-clear は列挙済み surface の中での優先順位付けにのみ使う (未検証の clear が列挙自体を抑止して反証を素通りさせるのを防ぐ)。(b) 手順 2 の独立 1 パス (全所見を伏せる) にも持ち込まない。(c) 反証で名指した surface を確認推奨ノートから外すには Phase 4 自身のスポット検証を要求する。加えて、安全ゲート系 (認可・秘密情報・収束判定) の reviewed-clear は **統合レポートに載せる前に Phase 4 が最低 1 件スポット検証** する (所見側の偽陽性確認と対称)。無検証の 1 行に反証出力の拒否権・過大な確信度を与えない
   - **`BLOCKED` のとき**: 既に直すものがあるため、全所見を俯瞰し未検査の観点が無いかを 1 パスで確認するに留める
   - **歯止め (BLOCKED inflation 防止)**: 既定出力は「未カバー surface / 確認推奨ノート」。`BLOCKED` への昇格は **裏づけ済みの確定所見のみ**。**具体的な潜伏箇所を名指せないなら何も出さない** (裏づけのない疑いを重大度付き所見として量産しない)
6. **確定判定**: 手順 5 の結果を反映して `BLOCKED` / `PASS` を確定する。
7. **intent 整合**: intent context があれば各レビュアの intent コメントを統合サマリーに含める。**具体的・反証可能な DoD があれば goal anchor として信頼**し diff ↔ DoD の対応を軽く確認する (完了条件を km:review 側で再導出・拡張しない)。

統合レポート末尾に **優先順位付きアクションリスト** を生成する:

1. **マージ前必須** (CRITICAL/HIGH): 該当ファイル + 修正方針で「PASS への最短経路」を示す
2. **同一 PR で修正** (MEDIUM/LOW): この PR で直す対象
3. **PR 目的の外** (out-of-scope): follow-up issue 候補として分離
4. **指摘の相互関係 (共通根抽出)**: dedup 後、複数所見に共通する **設計レベルの根本原因** があるかを 1 回問う。あれば 1 文で抽出し、修正方針を個別所見単位でなく **根本原因単位** へ格上げして提示する (分散した所見が 1 つの設計原則に束なると修正が根本駆動される)

分類基準は「指摘対応の方針」を参照。

出力フォーマット (統合サマリー・各 Phase 表示・中央 dedup・アクションリスト・受け入れ済みリスク) は `integration-report.md` に集約。

## Phase 5: doc-review (最終状態に対して)

doc-review はコードレビューとは性質が異なり、**コードが確定した最終状態**に対してドキュメント整合を確認する。`doc-review.md` を Read して main コンテキストで実施する。doc-review は 2 つの関心を変更構成に応じて扱う (詳細は `doc-review.md`): **A. コード変更のドキュメント影響** をリポジトリ全体のスコープで確認・修正する / **B. 変更ドキュメントの全体整合性** (内部整合・他ドキュメントとの整合・一次情報) を確認する。

**起動条件** (Phase 4 のコード判定を踏まえる):

- **`docs-only`**: コード層は無いので doc-review が主レビュー。関心 B を実行
- **`code+docs` / `mixed`**: Phase 4 が `PASS` (最終状態が確定) のとき関心 A + B を実行。`BLOCKED` のときは **defer** (コード修正で内容が変わるため、修正後に実行)
- **`code-only`**: Phase 4 が `PASS` のとき関心 A を実行。`BLOCKED` なら defer
- **`test-or-config-or-chore-only`**: skip (config が高リスクなら関心 A を実行)

doc-review が CRITICAL/HIGH を出した場合は最終判定を `BLOCKED` に更新する。defer した場合はレポートに `### Phase 5: Doc Review\n（defer - コード解消後に実施）` と明記する。

## 再検証モード (recheck)

BLOCKED を出したレビューは「修正後の再確認」を必要とする。フル再実行 (thorough なら 3 subagent 再起動) は高コストなので、検証コストを差分に比例させる。ただし再確認は BLOCKED 解除という最も重い判定なので、コスト削減が精度を落とす形 (著者自身による解消確認・反証なしの `PASS`) にはしない — km:plan の差分レビューに倣い、**独立 subagent + PASS 反証必須** の構造を保つ。

- **起動条件**: `--recheck` token、かつ「直前の km:review が BLOCKED で修正差分を伴う再依頼」と判断できること。判断材料は同一セッションの会話文脈、または **新セッションではユーザの現ターン依頼 + 永続化された統合レポート** (「前回の指摘を直したので再チェック」等)。どちらでも可 (セッション境界に依存しない)
- **入力**: 未解決所見の一覧 + 修正差分。一覧は会話文脈、または **永続化された統合レポート** (`<report dir>/integration.md`) から取得する。**フォールバック (通常実行へ切替)**: (a) 一覧をいずれからも入手できない、(b) 読み込んだ `integration.md` の判定が BLOCKED でない (別 run に上書きされた疑い)、(c) その所見が今回の対象差分と噛み合わない — のいずれかなら recheck とせず通常実行に切り替え、その旨を報告に明記する (存在しない・陳腐化した所見一覧を推測で使わない)
- **実行主体**: 解消確認と修正 hunk の欠陥走査は **独立 subagent 1 名への差分指示** で行う (著者バイアス回避)。この subagent は **通常の Phase 2/3 と同じ方法論を継承する**: `code-review.md` Step 2 (3 層 + diff 外照合) で修正 hunk を走査し、対象が挙動資産分類なら `references/prompt-asset-lens.md` を読み、返信前に報告ファイル + 完了 sentinel を書く (中断時の部分回収を recheck 経路にも適用)。指示の骨子: 未解決所見ごとに解消済み / 未解消を判定し、修正 hunk に新たな欠陥がないかを上記方法論で走査。main コンテキストは統合と判定のみを担う
- **PASS 反証の必須**: recheck で `PASS` を出す前に、全レベル共通の PASS 反証 (反実仮想 1 パス、Phase 4 手順 5 の安価な版) を必須で実施する
- **Phase 3 の再起動 (昇格)**: 修正が高リスク領域に **新たに** 触れる場合のみ、該当 expert を起動する (既存の内容ベース昇格と同一基準)
- **defer 済み doc-review の再開**: recheck の結果が `PASS` になったら、defer されていた Phase 5 を実行して最終判定を確定する
- **出力**: `integration-report.md` の統合サマリー形式で、**解消済み / 未解消 / 新規** を区別した更新判定を出す
- **制約**: recheck は修正 hunk の外の回帰をフル再実行と同等には見ない。この検出範囲の狭さは PASS 反証の必須化と昇格条件で緩和するトレードオフであり、ユーザはいつでもフル再実行を明示指定できる

## 進行ゲート

**コードレビュー層 (Phase 2 → Phase 3 → Phase 4 統合) は最後まで実行する**。Phase 2 / Phase 3 で CRITICAL/HIGH が出ても早期停止せず、並列レビュアの所見をすべて Phase 4 で集約してから判定する。Phase 3 は 3 名全員の完了を待って統合する。

doc-review (Phase 5) のみ、Phase 4 のコード判定が `BLOCKED` のとき defer する (docs-only を除く)。

## レベル別実行マトリクス

| Level | Phase 2 | Phase 3 | Phase 4 統合 | Phase 5 doc-review |
|---|---|---|---|---|
| `quick` | ✓ (浅) | スキップ | ✓ | 変更構成依存 / PASS 時 |
| `standard` | ✓ | スキップ | ✓ | 変更構成依存 / PASS 時 |
| `thorough` | ✓ | ✓ (3 名並列) | ✓ | 変更構成依存 / PASS 時 |

変更構成・内容による override:

- `docs-only` → Phase 2/3 skip、Phase 5 doc-review (full) のみ
- `test-or-config-or-chore-only` → Phase 3 / Phase 5 skip (Phase 2 + Phase 4 のみ)
- **内容ベースの昇格は降格に優先する**: `quick` / `standard` でも diff が高リスク領域 (Phase 3 の「内容ベースの昇格」参照) に触れるなら、該当専門家を起動する。`test-or-config-or-chore-only` でも、その変更が高リスク (CI 権限・デプロイ・秘密情報など) なら同様に昇格してよい

`quick` と `standard` は Phase 起動条件こそ同じだが、`quick` では Phase 2 / doc-review 内部の検査深度を絞る (詳細は `code-review.md` / `doc-review.md` の深度表。ただし不変条件の継承サブプローブは全レベル無条件で深度削減の対象外 — `code-review.md` Step 2「diff 外照合」)。Phase 4 の **能動的検証 (`[possible]` HIGH+ の実証) と PASS 反証の確定ステップは `thorough` / 高リスク昇格時のみ** 行う (ツール実行を伴うため)。PASS 反証の反実仮想 (surface 列挙 + 独立 1 パス) は安価なため全レベルで行う。そこで出る確認推奨ノートは非ブロッキングで判定を変えない。

## 指摘対応の方針

レビューは好み・様式の好き嫌いを出さず、「本質的に改善すべきもの」だけを指摘する。**出した指摘は `LOW` を含め原則すべて修正する**。変更に起因する / 変更の目的達成に必要な指摘は **同一 PR 内で直す** (follow-up に逃がさない)。follow-up issue にするのは、この PR の目的の外にある既存問題や大規模リファクタに限る (`Change Surgically` は proactive に触る範囲を最小化する原則で、レビューで露見した自分の変更の欠陥は in-scope)。

大規模修正 / 仕様変更 / 設計トレードオフでユーザ判断が要るものだけ、残す場合に「受け入れ済みリスク」形式 (重大度・残す理由・後続対応条件) で明示記録する。出力形式は `integration-report.md` を参照。
