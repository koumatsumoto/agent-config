---
name: km:review-loop
description: >
  Iterates km:review with auto-fixes until PASS or loop limit. Use when the user says
  "レビューを繰り返す" / "レビューと自動修正を反復" / "review-loop".
argument-hint: "[target] [level] [--max-loops N]"
---

# Review Loop

km:review を反復起動し、CRITICAL/HIGH を自動修正しながら PASS まで持っていく orchestrator。完了時に累積した MEDIUM/LOW も例外条項を除いて自動修正する。

## Success Criteria

- km:review が PASS を返す状態まで自動反復する
- CRITICAL/HIGH の修正は LOW を含む全指摘を Edit tool で適用 (例外条項を除く)
- ループ上限 (`--max-loops` 既定 5) 到達時はユーザ判断を仰ぐ

## 例外条項

以下に該当する指摘は自動修正せず「受け入れ済みリスク」として記録し、ユーザ判断を仰ぐ。判定揺れを抑えるため定量・観察可能な hint を併記する:

- **合意済み判断**: intent context (km:plan issue 本文 / 会話文脈) に該当方針が明示されている。**intent context が空の場合は本条項を採用しない** (推測で合意済み扱いしない)
- **影響が大きい修正**: 次のいずれかを満たす。(a) 1 件の修正が `≥3 ファイル` または `≥50 行` の変更を要する、(b) 公開 API 契約 (export / public method / route / DB schema) を変える、(c) 既存テストの期待値変更を要する
- **設計判断のトレードオフ**: 指摘の `**修正**` フィールド内に "A or B" / "選択次第" 等の二択以上が明示、または既存 ADR / intent context と修正方針が衝突する
- **修正方針不明確**: 指摘の `**修正**` フィールドが空 / 一般論のみ (例: "適切にハンドリングする") / 編集 tool で diff に落とせない (例: 「テスト戦略を見直す」)
- **修正で他観点を壊す可能性が高い**: 同一ファイルの別 Phase 指摘と修正方針が衝突、または修正が別 Phase が拾ったコードを巻き戻す

例外条項判定は **指摘ごとに上記 hint と照らして可否を記録** する (例: `理由: 影響が大きい修正 (a) ≥3 ファイル`)。

## Phase A: 引数解析

`$ARGUMENTS` から以下を抽出:

- `--max-loops N`: ループ上限 (省略時 5)。`--max-loops=N` のような `=` 区切り形式は受け付けない
- 残り token: km:review にそのまま渡す (`target` + `level`)

例:

- `/km:review-loop` → 既定 (km:review に引数なし渡し、max-loops=5)。km:review 側の「引数なしフォールバック」(uncommitted → push 済なら PR → 終了) に委譲
- `/km:review-loop pr:123 thorough` → km:review に `pr:123 thorough` 渡し、max-loops=5
- `/km:review-loop --max-loops 10 thorough` → km:review に `thorough` 渡し、max-loops=10

## Phase B: km:review を呼ぶ

`~/.claude/skills/review/SKILL.md` を Read し、その指示通りに main コンテキストで実行する。Task tool は km:review 内部の Phase 3 (3 experts 並列) でのみ発火させる。

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

直前 km:review (Phase B 直接 BLOCKED でも、Phase C PASS ルートの Recheck-BLOCKED でも) が止まった停止 Phase の指摘 (CRITICAL/HIGH + MEDIUM + LOW) について処理する。それ以前の Phase の MEDIUM/LOW は最終 PASS 後にまとめて自動修正される (累積管理は下記参照)。

### 累積 MEDIUM/LOW の管理

- イテレーションごとに **「最終 km:review iteration (= PASS を返した実行) の Phase 2 / Phase 4 等で出た MEDIUM/LOW」** を最終処理対象とする。それ以前のイテレーションで出た MEDIUM/LOW は **採用しない** (該当指摘は修正済みか、別観点に変質しているはずなので最終 iteration の出力に立ち戻る)
- 同一 iteration 内で「停止 Phase より前の Phase」で出た MEDIUM/LOW は、PASS 確定後にまとめて処理対象とする
- 重複は `(file_path, 影響行範囲, ISO 副特性 ID / Phase 2 観点ラベル)` の組で排除し、最新 wording を採用

各指摘について:

1. 「例外条項」に該当 → 「受け入れ済みリスク」として記録 (重大度 / 残す理由 / 後続対応条件)
2. 該当しない → Edit tool で自動修正

### Phase D の集計

- 自動修正対象が 1 件以上ある → Phase E (ループ判定) へ
- **全 CRITICAL/HIGH が例外条項該当** (= 自動修正できる CRITICAL/HIGH がゼロ) → 即時ユーザ判断を仰ぐ (下記「ユーザ判断 3 択」)。Phase E のループには進まない

## Phase E: ループ判定

Phase D で自動修正が 1 件以上発生した後にここへ来る。次のいずれか:

- **ループ上限 (`--max-loops`) 到達** → ユーザ判断 3 択を仰ぐ
- **収束しない兆候 (oscillation)** → ユーザ判断 3 択を仰ぐ。判定基準は次のとおり:
  - **同一指摘 = `(file_path, 影響行範囲, ISO 副特性 ID / Phase 2 観点ラベル, 重大度)` の組** が一致するもの
  - 直前 2 イテレーション連続で同一指摘が再出現したら oscillation と判定
- **それ以外** → loop カウンタ +1 して **Phase B に戻る** (km:review を再走)

## ユーザ判断 3 択

例外条項全該当時、ループ上限到達時、収束しないとき orchestrator が以下を提示する。**「受け入れ」は BLOCKED 判定を PASS に格上げする重大選択** なので、orchestrator は安易に推奨せず、受け入れ済みリスクの内容を要約してユーザに判断を仰ぐ:

- **受け入れ**: 残った CRITICAL/HIGH を「受け入れ済みリスク」として承認し、PASS 扱いで完了報告 → 次は km:commit / km:github-workflow へ (commit message / PR description で受け入れ済みリスクを明記する想定)
- **再起動**: `--max-loops` を拡張して再度 `/km:review-loop` を実行 (推奨: 直前 2 イテレーションで同観点が再出現していない場合)
- **中止**: 手動修正に切り替え、完了後にユーザが再度 `/km:review-loop` を実行 (推奨: oscillation 検出済、または修正方針が定性的で自動化に向かない場合)

## 自動修正の方針

1. **修正方法の決定**: 指摘の `**修正**` フィールドに記載された修正方針を読み、Edit tool で diff に適用。新規ファイル作成や Bash 実行が必要な指摘は **Edit に落とせない** とみなし例外条項へ
2. **複数指摘の処理**: 同一ファイルに複数指摘がある場合は、ファイルごとにまとめて Edit する
3. **修正検証**: project root に `tsconfig.json` / `pyproject.toml` / `Cargo.toml` 等の typecheck 起点があれば該当言語の構文 / 型チェックを実行する。起点がない / 言語が判別不能な場合は検証スキップ。明らかな破綻が出たら Phase E でユーザ判断を仰ぐ
4. **修正できない場合**: 例外条項 (修正方針不明確 / Edit 不可) として「受け入れ済みリスク」へ

## ループ状態の管理

ループ反復回数と直前状態は次の二段で復元可能にする (context compaction / resume 後にも上限保証を守るため):

1. **会話履歴に残る進行ログ**: orchestrator は **各 km:review iteration 完了直後に、応答テキスト本文へ次の 1 行ブロックを必ず inject する** (本文に書くため compaction 後の要約にも残りやすい)。
   ```
   loop_state: target=<target> level=<level> run=<n>/<max> last_blocker=<停止 Phase もしくは PASS>
   ```
2. **inject 済みヘッダの最大 run 値を採用**: orchestrator はループ回数を判定するとき、会話履歴中に存在する `loop_state` ヘッダの `run=<n>` の最大値と、自身が把握する内部カウンタの最大値を採用する。compaction で履歴前半が削除された場合は、最後に残った `loop_state` ヘッダの run 値を起点に継続する。

セッションをまたぐ反復が必要な場合は、ユーザが `--max-loops N` で都度指定する。永続ファイルは必須ではないが、`.plan/` 配下に作業メモを残す運用とは整合する。

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
- 修正で diff が **当初の 3 倍以上または +500 行以上** に膨張したらループを止めてユーザ判断を仰ぐ
- Phase C 再検証で **初めて検出された** CRITICAL/HIGH は auto-fix で混入した可能性があるため、それを「受け入れ済みリスク」として提示する際は **その由来 (auto-fix の副作用かもしれない)** をユーザに併記する
