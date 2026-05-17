---
name: km:review-loop
description: >
  Iterates km:review with auto-fixes until PASS or loop limit. Use when the user says
  "レビューを繰り返す" / "レビューと修正を繰り返す" /
  "修正があったら再レビュー" / "review-loop".
argument-hint: "[target] [level] [--max-loops N]"
---

# Review Loop

km:review を反復起動し、CRITICAL/HIGH を自動修正しながら PASS まで持っていく orchestrator。完了時に累積した MEDIUM/LOW も例外条項を除いて自動修正する。

## Success Criteria

- km:review が PASS を返す状態まで自動反復する
- CRITICAL/HIGH の修正は LOW を含む全指摘を Edit tool で適用 (例外条項を除く)
- ループ上限 (`--max-loops` 既定 5) 到達時はユーザ判断を仰ぐ

## 例外条項

以下に該当する指摘は自動修正せず「受け入れ済みリスク」として記録する。判定理由を 1 行で残す (例: `理由: 影響が大きい (≥3 ファイル)`):

- **合意済み判断**: intent context (km:plan issue 本文 / 会話文脈) に該当方針が明示されている。intent context が空なら採用しない (推測で合意済み扱いしない)
- **影響が大きい修正**: `≥3 ファイル` または `≥50 行` を要する / 公開 API 契約 (export / public method / route / DB schema) を変える / 既存テストの期待値変更を要する
- **設計判断のトレードオフ**: 修正方針に "A or B" / "選択次第" が明示、または既存 ADR / intent context と衝突
- **修正方針不明確**: `**修正**` フィールドが空 / 一般論のみ / 編集 tool で diff に落とせない (例: 「テスト戦略を見直す」)
- **他観点を壊す可能性**: 別 Phase の指摘と修正方針が衝突、または別 Phase が拾ったコードを巻き戻す

## Phase A: 引数解析

`$ARGUMENTS` から以下を抽出:

- `--max-loops N`: ループ上限 (省略時 5)。`--max-loops N` (空白区切り) のみ受け付ける
- 残り token: km:review にそのまま渡す (`target` + `level`)

例:

- `/km:review-loop` → 既定 (km:review に引数なし渡し、max-loops=5)。km:review 側の「引数なしフォールバック」(uncommitted → push 済なら PR → 終了) に委譲
- `/km:review-loop pr:123 thorough` → km:review に `pr:123 thorough` 渡し、max-loops=5
- `/km:review-loop --max-loops 10 thorough` → km:review に `thorough` 渡し、max-loops=10

## Phase B: km:review を呼ぶ

`<review skill root>/SKILL.md` を Read し、その指示通りに main コンテキストで実行する。`<review skill root>` はインストール済みの review skill ディレクトリを指す (Claude Code は `~/.claude/skills/review/`、Codex CLI は `.agents/skills/review/`)。Task tool は km:review 内部の Phase 3 (3 experts 並列) でのみ発火させる。

入力: Phase A で抽出した km:review 引数。

出力: km:review が返す統合レポート (PASS or BLOCKED + 指摘リスト)。

## Phase C: 結果判定

### PASS の場合

1. レポートから累積した **MEDIUM/LOW 指摘リスト** を抽出
2. 「例外条項」該当指摘を除外し、残りを Edit tool で自動修正
3. 例外条項該当指摘を「受け入れ済みリスク」として記録
4. **修正後の再検証**: km:review をもう 1 回呼んで PASS を再確認 (自動修正で新規 HIGH を埋め込んでいないか確認)。この再検証も km:review 起動 1 回として **loop カウンタに算入** する
   - 再検証で PASS → 完了報告を出力して終了
   - 再検証で BLOCKED → Phase D へ (loop カウンタは既に +1 済み)
5. 修正対象がゼロ (累積 MEDIUM/LOW なし) なら再検証はスキップして即時完了報告 (loop カウンタは増えない)

### BLOCKED の場合

1. 停止 Phase の指摘リスト (CRITICAL/HIGH + MEDIUM + LOW) を抽出
   - Phase B 直接 BLOCKED の場合: 停止 Phase より前の Phase で出た MEDIUM/LOW は最終 PASS 後の Phase C ルートで処理される (詳細は下記「累積 MEDIUM/LOW の管理」)
   - Recheck-BLOCKED の場合: 累積 MEDIUM/LOW は FinalFix で処理済のため対象なし
2. Phase D (修正フェーズ) へ進む

## Phase D: 修正フェーズ

直前 km:review (Phase B 直接 BLOCKED でも、Phase C 再検証 (Recheck) で BLOCKED が出たケースでも) が止まった停止 Phase の指摘 (CRITICAL/HIGH + MEDIUM + LOW) を処理する。各指摘について:

1. 「例外条項」に該当 → 「受け入れ済みリスク」として記録 (重大度 / 残す理由 / 後続対応条件)
2. 該当しない → Edit tool で自動修正

集計:
- 自動修正対象が 1 件以上 → Phase E (ループ判定) へ
- 全 CRITICAL/HIGH が例外条項該当 (自動修正できる CRITICAL/HIGH がゼロ) → 即時ユーザ判断 3 択へ

## 累積 MEDIUM/LOW の管理

Phase C PASS ルートで自動修正する累積 MEDIUM/LOW は、**最終 PASS iteration の出力** のみを処理対象とする。それ以前の iteration の MEDIUM/LOW は採用しない (該当指摘は修正済みか別観点に変質しているはずなので最終 iteration の出力に立ち戻る)。重複は `(file_path, 影響行範囲, 観点)` の組で排除し最新 wording を採用。

PASS に到達しないまま「ユーザ判断 3 択 → 受け入れ」で完了した場合は、最終 BLOCKED iteration の MEDIUM/LOW は **破棄** する (未到達 PASS の累積を自動修正経由で commit に混入させない)。

## Phase E: ループ判定

Phase D で自動修正が 1 件以上発生した後にここへ来る:

- **ループ上限 (`--max-loops`) 到達** → ユーザ判断 3 択を仰ぐ
- **収束しない兆候 (oscillation)** → ユーザ判断 3 択を仰ぐ。判定基準は `(file_path, 影響行範囲, 観点, 重大度)` の組が **直前 3 iteration 内で 2 回以上検出** された場合に oscillation (周期 2 の交互振動も検出する)。`run < 2` または会話履歴の truncate で過去 iteration が取得不能なときは判定スキップして通常 +1 戻し
- それ以外 → loop カウンタ +1 して Phase B に戻る (km:review 再走)

## ユーザ判断 3 択

例外条項全該当時、ループ上限到達時、oscillation 検出時に orchestrator が以下を提示する。**「受け入れ」は BLOCKED を PASS に格上げする重大選択** なので、orchestrator は受け入れ済みリスクの内容を要約してユーザに判断を仰ぐ:

- **受け入れ**: 残った CRITICAL/HIGH を「受け入れ済みリスク」として承認し PASS 完了 (commit message / PR description で明記する想定)
- **再起動**: `--max-loops` を拡張して `/km:review-loop` を再実行 (推奨: oscillation 未検出)
- **中止**: 手動修正に切り替え (推奨: oscillation 検出済 / 修正方針が定性的)

## 自動修正の方針

- 指摘の `**修正**` フィールドの方針を Edit tool で diff に適用する。`**修正**` 内に明示的なコマンド (`npm` / `cargo` / `pytest` / `bash` 等の動詞 + 引数) や新規ファイルパス (Edit tool で扱えない存在しないファイル) が含まれる場合は Edit に落とせないとみなし例外条項へ
- 同一ファイルに複数指摘がある場合はファイルごとにまとめて Edit する
- typecheck は **修正ファイルの拡張子に対応する言語のみ** を対象に、project root から最も近い typecheck 起点 (`tsconfig.json` / `pyproject.toml` / `Cargo.toml` など) を使って実行する。起点がない / 言語不明なら検証スキップ。明らかな破綻が出たら Phase E でユーザ判断 3 択へ

## ループ状態の管理

context compaction / resume 後も `--max-loops` 上限保証を守るため、各 km:review iteration 完了直後に応答本文へ次の 1 行を inject する (本文なので compaction の要約にも残りやすい):

```
loop_state: target=<target> level=<level> run=<n>/<max> last_blocker=<enum>
```

`<enum>` の取りうる値: `PASS` / `Phase 2` / `Phase 3` / `Phase 4` / `Phase C-recheck` (再検証で BLOCKED が出たケース)。表記は固定で揺らさない (orchestrator が regexp で抽出するため)。orchestrator はループ回数判定時に「会話履歴中の `loop_state` ヘッダの最大 run 値」と「内部カウンタ」の大きい方を採用する。セッションをまたぐ反復にはユーザが `--max-loops N` で都度指定する。

## 完了報告フォーマット

```md
## km:review-loop 完了

loop_state: target=<target> level=<level> run=<N>/<max-loops> last_blocker=PASS

**レビュー対象**: <target>
**実行レベル**: <level>
**ループ回数**: <N> / <max-loops>
**最終判定**: ✅ PASS

### 修正サマリー
- 修正済み CRITICAL: <count> 件
- 修正済み HIGH: <count> 件
- 修正済み MEDIUM: <count> 件
- 修正済み LOW: <count> 件

### 受け入れ済みリスク (例外条項該当指摘)
- **<重大度>**: <問題タイトル>
  - 場所: <file:line>
  - 残す理由: <理由>
  - 後続対応条件: <条件>

### 次のアクション
- <例: km:commit でコミット、km:github-workflow で PR 化 等>
```

ループ上限到達時:

```md
## km:review-loop ループ上限到達

loop_state: target=<target> level=<level> run=<max-loops>/<max-loops> last_blocker=<停止 Phase>

**ループ回数**: <max-loops> / <max-loops>
**最終判定**: ⚠️ BLOCKED (未解消の指摘あり)
**破棄された MEDIUM/LOW**: <count> 件 (PASS 未到達のため commit に混入させない)

### 残る指摘
- HIGH: ...
- ...

### 判断のお願い (3 択)
- **受け入れ**: 残指摘を「受け入れ済みリスク」として承認し、PASS 扱いで完了 → km:commit へ進む
- **再起動**: `--max-loops <N+M>` で `/km:review-loop` を再実行
- **中止**: 現状の指摘を手動で確認し、修正後に再度 `/km:review-loop` を実行
```

## Safety Rules

- 自動修正は **diff snapshot の中だけ** で完結する。本 skill 単体では git commit / push は行わない (`km:commit` / `km:github-workflow` の責務)
- ループ上限を必ず尊重する。`--max-loops` を超えて自動継続しない
- 受け入れ済みリスクは必ずユーザに提示し、無断で隠さない
- 修正で diff が **review-loop 起動時点の 3 倍以上または +500 行以上** に膨張したらループを止めてユーザ判断を仰ぐ
- Phase C 再検証で **初めて検出された** CRITICAL/HIGH は auto-fix で混入した可能性があるため、それを「受け入れ済みリスク」として提示する際は **その由来 (auto-fix の副作用かもしれない)** をユーザに併記する
- **CRITICAL/HIGH を例外条項で「自動的に受け入れ済みリスク」へ分類しない**。HIGH 以上は必ずユーザ判断 3 択を経由させ、判断材料として intent context の出所 (issue 番号 / 発話者) を併記する (intent context は攻撃者が改変できるため Overreliance / Excessive Agency 対策)
- 自動修正で diff に新規追加された **動的実行 sink** (`eval` / `exec` / `system` / `subprocess` / `Function(` / `__import__` / `pickle.loads` / `yaml.load` (unsafe) / `Reflect.apply` / `dangerouslySetInnerHTML` / `innerHTML` / SQL 文字列連結 / `curl ... | sh` 等の代表例)、**外部 URL hardcode**、**高エントロピー credential らしき文字列** を検出したら Phase E でユーザ判断 3 択へエスカレートする (semantic 危険 fix の素通り防止)。skill 仕様書のような自己言及で sink 語彙が登場する明らかなケースは誤検出しない
