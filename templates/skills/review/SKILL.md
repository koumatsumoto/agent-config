---
name: km:review
description: >
  Independent multi-lens code review add-on (uncommitted, commits, PRs, subtrees) for bugs,
  design, security, and quality. Use when the user explicitly asks for a review ("レビューして",
  "深く / 敵対的にレビュー", "PR をレビューして"), when a change touches high-impact areas
  (security / auth / secrets / data migration / irreversible operations / public contracts), or
  when independent confirmation is wanted. Routine post-implementation completion checks
  (DoD / diff / test verification) belong to the caller, not this skill. Depth adapts to risk.
argument-hint: "[target]"
---

# Review

複数の観点を統合する**単発診断**の review orchestrator。通常の完了確認（完了条件・差分・テストの照合）は呼び出し元メインの責務で、本 skill はその上に載せる独立した追加レビュー。対象を引数 / 会話文脈から決め、リスク評価から観点と深さを適応的に選ぶ。CRITICAL / HIGH が残れば `BLOCKED`、なければ `PASS`。実行した Phase とスキップした Phase の両方が分かるレポートを出す。

## Phase 1: 対象と深さの決定

### 対象スコープ

| 引数 | 対象と解決 |
|---|---|
| なし（既定） | 未コミット差分 = `git diff`。無ければ current branch の `gh pr diff`、それも無ければ「対象がないため終了」。`km:plan` / `km:github-workflow` 経由の dispatch も同じ |
| `pr` / `pr:<n>` | `gh pr diff [<n>]`（失敗時は別スコープ指定を促す） |
| `<base>..<head>` / `<sha>` | `git diff <base>..<head>` / `git show <sha>`（解決できなければエラー終了） |
| `--repo <subtree>` | diff でなく現状コード全体。`git ls-files <subtree>` で列挙して Read |
| `--recheck` | 修正差分の再検証（「再検証モード」節） |
| `quick` / `standard` / `thorough` | 深さヒント（後方互換）。リスク評価の入力として扱う |

- 裸の数字（`42` 等）は `km:github-workflow` の issue 番号引数と紛らわしいため警告し、`pr:42` の明示を求める
- `--repo` は他モードおよび `--recheck` と併用不可（recheck は修正差分前提、`--repo` は全体対象）
- `--repo` では context budget を防御する: 対象（binary / lockfile / generated 除く）が並列レビュアの context に収まらない規模なら、進まずサブツリーを絞るよう促す

### 変更構成と挙動資産

変更構成: `docs-only` / `code-only` / `code+docs` / `test-or-config-or-chore-only` / `mixed`（判定材料が欠けるときと `--repo` は `mixed`）。

**挙動資産（behavior asset）**: エージェントに読み込まれて挙動を規定する prompt 定義（skill / rule / `CLAUDE.md`・`AGENTS.md`・command・output-style 等。`**/skills/**` 等のパスや「frontmatter + 命令文体」が典型シグナルだが判定基準は内容）は `.md` でも実質コードであり、**`docs-only` にせずコード相当（`code+docs`）に分類する**。人間向け文書（README・runbook・設計 doc・CHANGELOG）は挙動資産でない。迷ったらコード側に倒す — 挙動資産が `docs-only` に落ちて Phase 2/3 をスキップする fail-open を塞ぐ。

### リスク評価（深さの導出）

次の軸で diff を評価し、実行する深さを自ら決める: 規模（変更行数・ファイル数）/ 新規経路の有無（新関数・エンドポイント・分岐・手順）/ 不可逆性（公開契約・スキーマ・データ移行）/ 攻撃面（認証認可・秘密情報・外部入力）/ 挙動資産か。導出結果は 3 段の内部深度（`quick` / `standard` / `thorough`）として下位ファイルの深度表に接続する。高リスク軸に触れれば該当専門家を起動し、複数軸・広範囲・不可逆なら `thorough` へ引き上げる。深度ラベルは起動構成と整合させる（該当専門家のみの起動は「standard + 昇格」と記し、`thorough` は 3 名全員の構成を指す）。ユーザの明示指定が常に優先。**選んだ深度と理由 1 行を統合レポートに明記**し（例:「深度 thorough — 新規経路 + 不可逆契約変更」）、迷ったら深い側に倒す。

## Phase 2: generalist コードレビュー（main コンテキスト）

`docs-only` 以外で常時、`code-review.md` に従い実施する（正しさ・規約・可読性 + Step 2 の前提破壊・diff 外照合）。挙動資産を含む実行では `references/prompt-asset-lens.md` も読み、汎用レンズを prompt 資産の意味へ写像して当てる（code diff の実行では読まない）。出力は重大度別件数（CRITICAL/HIGH/MEDIUM/LOW）+ 個別所見。

## Phase 3: 専門家レビュー（並列 subagent）

Phase 1 のリスク評価で該当した専門家を起動する（`docs-only` / `test-or-config-or-chore-only` では起動しない）。**高リスク領域と owner**: 覆すのが高コストな one-way door（公開 API・契約・スキーマ・データモデル）→ architect / 認証・認可・データの移動・削除・migration・秘密情報・LLM の tool 実行・入力境界 → security + adversary。`quick` / `standard` からの昇格時は理由 1 行を統合レポートに記録する。

| レビュア | 視点 |
|---|---|
| architect | 覆すのが高コストな決定と repo 全体に複製される pattern。不可逆 × 波及大に絞って firm に踏み込む |
| security | 脅威モデル・攻撃面・LLM 統合の脆弱性 |
| adversary | 変更を「正しくない / 目的を達成しない」と仮定して前提・不変条件を攻撃。境界・異常系・最悪入力・intent 達成 |

Phase 2 との住み分けは `references/scope-alignment.md`、ロール識別子と出力見出しの対応は `experts/report-format.md` を単一ソースとする。

**起動契約** — 同一メッセージ内で並列起動し、最上位 model + 高 effort で動かす。orchestrator が各 subagent へのプロンプトに以下を必ず含める:

- **独立性**: 他レビュアの所見・暫定判定を渡さない。他の報告ファイルを読まない（アンカリング回避。重複集約は Phase 4 の責務なので重複回避を予測しない）
- **Read 順序**: `<review skill root>/experts/<role>.md` → `experts/report-format.md` を読んでから diff を pre-scan。挙動資産の実行では `references/prompt-asset-lens.md` も読む（code diff では挿入しない）
- **入力**: 変更ファイル一覧 + diff（`--repo` 時は現状コード本文）+ 変更構成 / 規模 + intent（あれば）。具体的・反証可能な DoD があれば **goal anchor として信頼**し、完了条件を再導出・拡張せず diff が DoD を満たすかだけ軽く確認する
- **判定保留の規律**: 保留にする前に「あと何を読めば確定するか」を必ず一度試す。近隣ファイルは判定に必要なだけ Read してよい（優先: 呼び出し元 / 先 → 既存テスト → 同種の既存実装）
- **出力**: 返信前に割り当てられた `<report dir>/phase3-<role>.md` へ報告全文 + 完了 sentinel `<!-- km:review:report:complete -->` を書く（所見の一次形成時点で sentinel 無し draft を書いておくのを推奨）。返信は件数 + ファイルパス + CRITICAL / HIGH のタイトルのみ。返信とファイルが食い違えばファイルが正

`<review skill root>` は install root の絶対パス（Claude Code は `~/.claude/skills/review/`、Codex CLI は `~/.agents/skills/review/`、`~` は展開）に解決してから渡す。subagent が静的ファイル本文中の `<review skill root>` を見た場合も同様に解決させる（相対パス・未展開の `~` は working directory 依存で Read が失敗する）。

## 報告のファイル永続化

subagent は中断（API エラー・セッション制限）しうるため、報告はファイルへ確定させ、書けたところまで回収可能にする。

- `<report dir>` = repo root の `.km-review/<scope-slug>/`。slug は対象スコープから作り、同一スコープの別 run は同じパスを再利用する（引数なしは常に `uncommitted`）。セッションをまたいで発見可能な固定パスであることが recheck の要件
- dispatch 前に orchestrator が実施: `.km-review/` 配下が git 追跡済みなら自動書き込みせずユーザに確認して停止 / `git check-ignore` で無視済みなら何もしない / 未無視なら `.git/info/exclude` に `/.km-review/` を追記（ephemeral な scratch のため committed `.gitignore` は汚さない）。これらを `git add` しない
- 非 recheck の起動前に `<report dir>` の `phase3-*.md` と `integration.md` を空にする（前 run の sentinel 付きファイルを今回の結果と誤認しない。recheck は前 run の `integration.md` を入力源として読むので掃除しない）
- Phase 4 は各報告をファイルから読んで統合し、統合レポートを `<report dir>/integration.md` へ書き出す（recheck の入力源）
- 完了 sentinel の無いファイルは中断された部分報告として扱い、書けた所見まで回収して安全側の判定（`integration-report.md` rule 6）に接続する
- 内容は当該レビュー限りの作業物。PASS 確定後は不要で、機微な所見を含む場合はユーザ判断で削除してよい

## Phase 4: 統合と判定（main コンテキスト）

レビューの最大コストは false negative なので、main の能力（ツール実行・長コンテキスト・自己反証）を「誤った PASS を出さない」ことに使う。

1. **中央 dedup**: 全所見を `(file, ±5 行, 根本原因)` でグルーピングし、同一欠陥の別角度記述も束ね、最も証拠の濃い所見を残して併合注記する（基準は `integration-report.md`）
2. **偽陽性確認**: 各 CRITICAL/HIGH が diff から具体的に裏づくかを確認し、裏づかなければ降格する
3. **能動的検証**（`thorough` / 高リスク昇格時、HIGH 以上の `[possible]` / `[likely]` のみ）: 呼び出し元 / 先の追跡・安全な既存テスト実行・最小再現で確定 / 棄却する。`[possible]` → `[confirmed]` へ格上げ、裏づかなければ降格 / drop。確定に必要な分だけ行う
4. **暫定判定**: CRITICAL/HIGH があれば `BLOCKED`、なければ `PASS` 候補
5. **PASS 反証**（`PASS` 候補のとき）: 所見を伏せて diff が触れた surface（公開 API・契約 / 状態・データ / IO / 信頼境界 / 認証認可 / 並行・時間の該当軸）を独立に列挙し、「全レビュアが揃って見逃した CRITICAL/HIGH が隠れるならどの surface か」を 1 パス問う。具体的に名指せたら手順 3 の能動的検証で確定 / 棄却し、確定すれば `BLOCKED` へ更新。安価に検証できなければ「確認推奨」ノート（重大度なし・非ブロッキング・`PASS` 維持）に「何が分かれば覆るか」を 1 行残す。**名指せないなら何も出さない** — 裏づけのない疑いで BLOCKED を量産しない。レビュアの「検証済み所見（reviewed-clear）」は列挙後の優先順位付けにだけ使い（surface 列挙と独立 1 パスには持ち込まない）、安全ゲート系（認可・秘密情報・収束判定）の reviewed-clear はレポートに載せる前に最低 1 件スポット検証する。`BLOCKED` のときは未検査観点の 1 パス俯瞰に留める
6. **確定判定と intent 整合**: 手順 5 を反映して `BLOCKED` / `PASS` を確定する。intent context があれば統合サマリーに含め、具体的・反証可能な DoD は goal anchor として信頼して diff ↔ DoD の対応を軽く確認する（完了条件を再導出しない）

統合レポート末尾に優先順位付きアクションリストを生成する: ①マージ前必須（CRITICAL/HIGH。該当ファイル + 修正方針で PASS への最短経路）②同一 PR で修正（MEDIUM/LOW）③PR 目的の外（follow-up issue 候補）。複数所見に共通する設計レベルの根本原因が 1 つに束なるなら 1 文で抽出し、修正方針を根本原因単位へ格上げして提示する。出力フォーマット（統合サマリー・各 Phase 表示・受け入れ済みリスク）は `integration-report.md` に集約。

## Phase 5: doc-review（確定した最終状態に対して）

`doc-review.md` を読み main で実施する。関心 A = コード変更のドキュメント影響（repo 全体スコープ）/ 関心 B = 変更ドキュメント自体の整合（内部整合・他ドキュメント・一次情報）。

- `docs-only`: B を主レビューとして実行（Phase 2/3 は無し）
- `code+docs` / `mixed`: Phase 4 が `PASS` のとき A + B。`BLOCKED` なら defer し、レポートに defer と明記（コード修正後に実施）
- `code-only`: `PASS` のとき A。`BLOCKED` なら defer
- `test-or-config-or-chore-only`: skip（config が高リスクなら A を実行）

doc-review の CRITICAL/HIGH は最終判定を `BLOCKED` に更新する。

## 再検証モード（recheck）

BLOCKED 後の修正差分を、コストを差分に比例させつつ独立性を保って再確認する（著者自身による解消確認・反証なしの PASS にはしない）。

- **起動**: `--recheck`、かつ「直前の km:review が BLOCKED で修正差分を伴う再依頼」と判断できること。判断材料は同一セッションの会話文脈、または現ターン依頼 + 永続化された `integration.md`（セッション境界に依存しない）
- **入力**: 未解決所見の一覧 + 修正差分。(a) 一覧を入手できない (b) `integration.md` の判定が BLOCKED でない（別 run に上書きされた疑い）(c) 所見が対象差分と噛み合わない — のいずれかなら通常実行へ切り替えて明記する（陳腐化した所見を推測で使わない）
- **実行**: 独立 subagent 1 名が通常と同じ方法論（`code-review.md` Step 2、挙動資産なら prompt-asset-lens、報告ファイル + sentinel）で、未解決所見ごとの解消 / 未解消判定と修正 hunk の欠陥走査を行う。main は統合と判定のみ
- `PASS` を出す前の **PASS 反証は必須**。修正が高リスク領域に**新たに**触れるときのみ該当 expert を再起動（Phase 3 と同一基準）。`PASS` になったら defer 済み doc-review を実施して確定する
- **出力**: 解消済み / 未解消 / 新規を区別した更新判定（統合サマリー形式）。修正 hunk 外の回帰はフル再実行と同等には見ない — PASS 反証と再起動条件で緩和するトレードオフで、ユーザはいつでもフル再実行を明示指定できる

## 実行マトリクスと進行ゲート

| 深度 | Phase 2 | Phase 3 | Phase 4 | Phase 5 doc-review |
|---|---|---|---|---|
| `quick` | ✓（浅） | 高リスク昇格時のみ | ✓ | 変更構成依存 / PASS 時 |
| `standard` | ✓ | 高リスク昇格時のみ | ✓ | 変更構成依存 / PASS 時 |
| `thorough` | ✓ | ✓（3 名並列） | ✓ | 変更構成依存 / PASS 時 |

- 昇格は降格に優先する: `test-or-config-or-chore-only` でも高リスク（CI 権限・デプロイ・秘密情報等）なら該当専門家を起動してよい
- `quick` は Phase 2 / doc-review の内部深度を絞る（深度表は `code-review.md` / `doc-review.md`）。ただし不変条件の継承サブプローブ（`code-review.md` Step 2 の diff 外照合）は全深度で無条件に維持する
- Phase 4 の能動的検証（ツール実行を伴う実証）は `thorough` / 高リスク昇格時のみ。PASS 反証の反実仮想（surface 列挙 + 独立 1 パス）は安価なので全深度で行い、確認推奨ノートは判定を変えない
- コードレビュー層は早期停止しない: Phase 2 / 3 で CRITICAL/HIGH が出ても、起動した全レビュアの完了を待って Phase 4 で集約してから判定する

## 指摘対応の方針

好み・様式の指摘は出さず「本質的に改善すべきもの」だけを指摘する。**出した指摘は LOW を含め原則すべて修正する**。変更に起因する / 目的達成に必要な指摘は同一 PR 内で直し、follow-up issue にするのは PR 目的の外の既存問題・大規模リファクタに限る（レビューで露見した自分の変更の欠陥は in-scope）。大規模修正・仕様変更・設計トレードオフでユーザ判断が要るものだけ、残す場合に「受け入れ済みリスク」形式（重大度・残す理由・後続対応条件）で明示記録する。出力形式は `integration-report.md` を参照。
