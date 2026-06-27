---
name: km:plan
description: Materializes implementation plans into `.plan/YYYYMMDD-<slug>.md` and, on a GitHub-managed repo, mirrors the final plan body to a GitHub issue as the canonical reference. The materialize-and-issue flow fires on explicit materialize / issue triggers — e.g. "issue にして", "計画を issue にして", "Issueで計画して", "issue に実装計画を作って", ".plan に出して", "計画レビューしてから issue 化". Lighter "計画を作って" / "実装計画を作成して" / "まず計画だけ" stays in draft-only — `<proposed_plan>` only, no disk write, no issue. Bare "PR にして" / "最後は PR" is km:github-workflow; "レビューして" on diffs is km:review. For "計画を作って PR まで" or "計画を issue にして PR にして", km:plan runs first then hands off to km:github-workflow with the issue number.
argument-hint: "[title-or-topic]"
---

# Plan

実装前の計画を作り込み、`.plan/YYYYMMDD-<slug>.md` に詳細版を書き出し、そのファイルを対象に agentic な計画レビューを行い、レビュー反映後の本文を GitHub issue に全文ミラーする。Plan / Materialize / Review / Mirror / Report の 5 phase で進める。

## Context

- Repo: !`git rev-parse --is-inside-work-tree 2>/dev/null || echo "(not a git repo)"`
- Branch: !`git branch --show-current 2>/dev/null`
- `.plan/` tracked?: !`git ls-files -- .plan .plan/ 2>/dev/null | head -1 || echo "(none)"`
- `.plan/` ignored?: !`git check-ignore -q .plan/ 2>/dev/null && echo "yes" || echo "no"`
- `.gitignore` has `.plan/`: !`grep -E '^\.plan/?$' .gitignore 2>/dev/null || echo "(absent)"`

GitHub / `gh` の状態は draft-only では不要なため Context では取得しない。GitHub repo 確認と `gh` 認証は Phase 4 (Mirror) で行う。Context はロード時のスナップショットで、実際の gate 判定は Phase 2 / Phase 4 の手順で実行時に取り直す。

## Success Criteria

- materialize 前に計画の骨子（**Goal / Non-goal / 合否判定できる Definition of Done**、主要トレードオフ）の未決を解消し、goal を反証可能な anchor として計画冒頭に固定してある
- plan 本文は背景・制約・判断理由・却下案・実装手順・検証条件・受け入れ済みリスクを含み、GitHub issue 単体で読める
- agentic review を行い、未解決の `CRITICAL` / `HIGH` が無い（収束しなければ issue 化しない）
- レビュー履歴・採否経緯が plan 本文・issue 本文に残っていない（最終計画と意図的な受け入れ済みリスクだけが残る）
- GitHub 管理 repo では新規 issue に `.plan/` ファイルを `--body-file` で全文ミラーし、URL 追記後に再同期してある
- 非 GitHub repo / `gh` 未認証なら `.plan/` 出力で停止し、原因を区別して報告してある
- 秘密情報が `.plan/` ファイル・issue 本文のいずれにも残っていない

## Routing

計画の `.plan/` materialize または計画 issue 化が明示された発話、あるいは materialize / issue 化の明示が無い軽量な計画作成依頼（draft-only）で使う。

- materialize / issue 化 trigger 例: "issue にして" / "計画を issue にして" / "Issueで計画して" / "issue に実装計画を作って" / ".plan に出して" / "合意済み計画を issue 化" / "計画レビューしてから issue 化" / "/km:plan <topic>"
- draft-only trigger 例: "計画を作って" / "実装計画を作成して" / "まず計画だけ"
- 使わない発話: "実装して" / "コミットして" / 単独の "PR にして" / 単独の "レビューして"
  - "PR にして" / "最後は PR" など PR delivery が明確 → `km:github-workflow`
  - 変更差分の "レビューして" → `km:review`
  - 計画ファイル単体のレビュー依頼は trigger にしない（必要なら手動で Phase 3 の観点で読む）
- 外部レビュー結果を計画 issue に反映する依頼（例: 「このレビュー結果を計画に反映して」）は「Incorporating External Review Feedback」節に従う

**Entry mode**（最初に 1 つ決める）:

| mode | 条件 | 進み方 |
| --- | --- | --- |
| `draft-only` | Plan Mode 中、または materialize / issue 化の明示が無い計画作成依頼 | Phase 1 で `<proposed_plan>` 提示まで → **停止**（書き込み・issue 化なし） |
| `materialize-existing-plan` | Plan Mode 外で、直近の合意済み計画を会話から復元でき、materialize / issue 化が依頼された | 合意済み内容は再設計せず詳細化する。Phase 1 で骨子の未決のみ確認 → Phase 2 以降 |
| `full-normal-mode` | Plan Mode 外で、`.plan/` 出力 / 計画 issue 化が明示された | Phase 1（質問・調査・Clarify Gate）→ Phase 2 以降 |

直近の合意済み計画を会話から復元できない場合は推測で書き出さず、計画内容を再確認する。

**複合依頼の優先度**:

- 「計画を作って PR まで」「計画を issue にして PR にして」= 計画 + PR delivery → まず `km:plan` で issue 化まで行い、その issue 番号で `km:github-workflow` を起動する。issue を作れずに停止した場合（非 GitHub / 未認証 / secret 検出 / CRITICAL 未収束）は handoff せず、停止理由を報告して判断を委ねる
- 計画コンテキストの無い ad-hoc issue + PR delivery（「このバグの issue を起こして PR まで」など）→ `km:github-workflow` に委ねる（km:plan は起動しない）

## Phase 1: Plan (clarify & mode)

1. repo と依頼内容を把握する。`$ARGUMENTS` は計画タイトル / 既存 issue 番号のヒントとして扱う。立案前に関連コード・既存実装・制約を**規模に応じて**調査する: 影響範囲が広い計画は **並行 Explore subagent** で関連箇所・制約を収集してから立案し、軽量な計画は過剰探索を避けて最小限の確認に留める（規模判断は Phase 3 step 2 の rubric と揃える）。subagent 非対応環境では直接 grep / read で調べる。収集した事実は **出典付き（`file:line` 等）** で計画の「依拠する前提」に残す（plan-template.md）
2. Routing の entry mode を 1 つ決める（Plan Mode かどうか判別できない場合は安全側に倒して `draft-only` とする）
3. `draft-only` なら質問・調査・下案作成を行い、計画下案を `<proposed_plan>`（チャット上の提示）として示して **停止する**。`.plan/` 書き込み・issue 化は一切行わない。停止時に「materialize / issue 化に進むには『.plan に出して』『計画を issue にして』と依頼する」と案内する
4. materialize に進む mode では **Clarify Gate**: 計画の骨子（**Goal＝本質的に満たすべき要件・ビジネス価値**、Non-goal＝スコープ境界、合否判定できる受け入れ条件、主要トレードオフ）を左右する未決事項を解消する。要件を取り違えていないか・浅い理解で進めていないかを確かめ、**本質を固めて引き出してから**進む
   - **計画を分岐させる未決だけ**を確認する。妥当な前提で進められるものは聞かない。確認は **選択肢 + 推奨案つきでまとめて 1 回**（構造化質問が使える環境では AskUserQuestion）で行い、往復を最小化する
   - 確認で固めた骨子は、計画冒頭の **Goal / Non-goal / Definition of Done anchor** に落とす（plan-template.md）。未解消のまま Phase 2 に進まない

## Phase 2: Materialize to `.plan/`

副作用を出す前に `.gitignore` 安全確認を済ませてから書き出す。

1. **`.gitignore` 安全確認**（この順で、副作用を出す前に実行する）:
   1. `git rev-parse --is-inside-work-tree` で git repo か確認。git repo でなければ `.gitignore` を編集せず `.plan/` 出力のみ行う
   2. `git ls-files -- .plan .plan/` で追跡済みか確認。追跡済みなら repo 方針と衝突するため、自動編集せずユーザに確認して停止する
   3. `git check-ignore -q .plan/` で既に ignore 済みか確認。`.git/info/exclude` 等で除外済みなら `.gitignore` は編集しない
   4. 追跡済みでなく ignore もされていない場合だけ `.gitignore` に `.plan/` を追加する（無ければ新規作成）
2. 安全確認が通った後にのみ `mkdir -p .plan` で出力先を確保する（tracked file 衝突を避けるため順序を逆にしない）
3. `references/plan-template.md` を読み、その観点集に沿って plan 本文を **メモリ上で** 組み立てる。`<!-- km:plan:managed -->` marker は plan-template.md の指示どおり本文先頭近くに 1 行で入れる
4. **pre-write Secret Check**（gate）: 組み立てた本文に「Secret Check」節のパターンを適用する。検出したら **書き出さず停止** し、ユーザにマスキングを依頼する（秘密情報をディスクに残さない）
5. Secret Check を通過したら、同日付の既存 `.plan/YYYYMMDD-*.md` と衝突しないか確認し（衝突時はファイル名規約の suffix を付ける。既存計画の上書きを避ける）、`.plan/YYYYMMDD-<slug>.md` に書き出す

ファイル名規約:

- 日付 prefix は区切りなしの `YYYYMMDD`（例: `.plan/20260423-km-plan-skill.md`）
- slug は英小文字 ASCII の kebab-case（`[a-z0-9-]+`）、50 文字以下を目安にする。日本語依頼でも repo 名 / issue title から短い英語 slug を作る
- 適切な英語 slug が作れない場合は `plan`。同日付内で既存の `.plan/YYYYMMDD-*.md` と衝突する場合のみ `-2`, `-3` の suffix を付ける

## Phase 3: Review (agentic)

`.plan/` に書き出したファイルを対象に、第三者目線で計画の精度を上げる。

1. `references/plan-review-checklist.md` を読む（レビュー観点・重大度定義・出力形式）
2. **レビュー強度を計画規模・リスクで選ぶ**（rubric）。2 レンズ（generalist＝見落とし / adversary＝敵対的分析）は全強度で共通で、最重要は「計画が**本質的に満たすべき要件（Goal）を取り違えていないか**」を問うこと（観点は `plan-review-checklist.md`）。多角的に作り込むのではなく、**強度だけを規模で伸縮**させる:

   | 強度 | 適用 | やり方 |
   | --- | --- | --- |
   | self-review | 軽量計画（小規模・可逆・低リスク。例: 文言 1 箇所修正、1 ファイル内の小変更） | subagent を立てず、メイン agent が「第三者レビュー」と明示し著者バイアスを自覚して 2 レンズで critical に読み直す |
   | 単一 subagent（既定） | 標準（複数ファイル / 設計判断を含む中規模） | **著者であるメイン agent ではなく別 subagent**（Claude Code の Task tool、Codex CLI の subagent）に 2 レンズでレビューさせる（著者バイアス回避）。下のプロンプトで起動 |
   | 専門家追加 | 高リスク領域（認証 / 認可、秘密情報、データ移行、破壊的操作、不可逆な公開 API 契約、LLM の tool / 入力境界）に触れる | 単一 subagent に加え、該当する専門家レンズ（security / architect 等）を必要な分だけ足す。観点が重ければ専門家を独立 subagent に分けてよい |

   判断軸は **規模・不可逆性・リスク領域**。迷ったら一段上の強度を選ぶ（under-review より over-review が安全）。subagent 非対応環境では self-review にフォールバックする
3. 返ってきた指摘を重大度別に整理し、**plan 本文へ直接反映する**。指摘内容・修正経緯は plan 本文にも issue 本文にも書き戻さない。共有用に履歴を残したい場合は issue 作成後に issue comments を使う（comments の内容を本文へ再同期しない）
4. `CRITICAL` / `HIGH` が解消するまで反復する。**初回はフルレビュー、2 回目以降は前回未解決の `CRITICAL` / `HIGH` の解消確認に絞った差分レビュー**にする（毎回フルで回さず、収束に向けてコストを絞る）。反復は **3 周を上限**とする。`MEDIUM` / `LOW` は原則反映し、意図的に残すものだけ plan 本文の「受け入れ済みリスク」として記録する（記録項目は plan-template.md に従う）
5. 反復上限に達しても `CRITICAL` / `HIGH` が収束しない場合は issue 化を止め、未収束の指摘とともにユーザに判断を委ねる
6. レビュー結果が **空・形式不一致・subagent が対象ファイルを読めず失敗** したのいずれかは、レビュー未実施として「収束」とみなさない（正規の `指摘なし`（重大度別件数すべて 0）とは区別する）。原因（多くは未解決のパス）を解消して再実行し、**実体のあるレビューが完了するまで issue 化しない**

subagent 起動プロンプト。`<plan skill root>` と計画ファイルは、メイン agent が **`~` を展開した絶対パス**に置換してから渡す（subagent はメイン agent の working directory を共有しないため、相対パス・未展開の `~` は解決できない）。install root は Claude Code が `~/.claude/skills/plan/`、Codex CLI が `~/.agents/skills/plan/`:

```
あなたは km:plan の第三者計画レビュアです。計画の著者ではない独立した視点で、`.plan/` の実装計画を critical にレビューしてください。

## 視点（2 レンズ）
- 最重要: この計画が **本質的に満たすべきもの（ユーザが本当に達成したいビジネス価値・要件）を取り違えていないか**
- generalist: 見落とし（要件・成功条件・手順・前提の曖昧 / 抜け）を潰す
- adversary: 計画を崩しにいく（本質要件を達成しないことを示せるか / 前提の真偽を repo で検証 / 実コードで最初に破綻する箇所 / より強い代替案）

## Read 順序
まず `<plan skill root>/references/plan-review-checklist.md` を読み、2 レンズの観点・重大度定義・出力形式を把握する。その後レビュー対象の計画ファイルを読む。

## レビュー対象
- 計画ファイル: <.plan/YYYYMMDD-<slug>.md の絶対パス>

## 補足
- 計画の前提（コードベースについて「調査で分かった事実」とされている箇所など）が実際に正しいか確認するため、必要なら repo 内のファイルを最大 5 個まで Read してよい。**出典（`file:line` 等）が付いた事実主張はそれを直接たどって確認し、出典の無い事実主張は「判定保留 / 要検証」とする**
- checklist または計画ファイルが読めない場合は、レビューせずその旨（読めなかったパス）を報告して終了する。憶測でレビューしない
- 計画だけでは前提の真偽を判定できない場合は「判定保留」とし、何を確認すれば判定できるかを書く
- **差分レビュー（2 回目以降）の指示がある場合は、指定された未解決の `CRITICAL` / `HIGH` が解消したかの確認に絞ってよい**（フル再レビューは不要）

## 出力
plan-review-checklist.md の「重大度と対応」「出力形式」に従い、各指摘に対象箇所・問題・修正案・重大度を付けて返す。本文の書き換えはせず、指摘だけを返す（反映はメイン agent が行う）。
```

## Phase 4: Mirror to GitHub issue

GitHub 管理 repo でのみ実行する。明示が無い限り **新規計画・新規 issue** を作る（類似 open issue は自動探索しない。誤上書きを避けるため）。

1. **pre-issue Secret Check**（gate, 再チェック）: レビューで追記・修正された最終本文と issue title に「Secret Check」節のパターンを再適用する。検出したら `gh issue create/edit` を実行せず停止する。`.plan/` ファイルは自動削除せず、ユーザに対処（masking / 再生成）を依頼する
2. `gh auth status` で `gh` の可用性と認証を同時確認する。失敗は原因を区別して報告し、`.plan/` 出力までで停止する:
   - `command not found: gh` → 未インストール。インストールを依頼
   - 認証エラー → 未認証。`gh auth login` を依頼
3. `gh repo view --json nameWithOwner,defaultBranchRef,url` で GitHub 管理 repo を確認する。失敗時は stderr で非 GitHub repo / 権限不足 / ネットワーク失敗を区別する
4. issue title を計画タイトルから作る（Conventional Commits 互換にすると後続 PR と揃う）。`--title` は shell 展開されるため backtick や `$(...)` を含めない（含む場合は単一引用符で囲む）
5. `gh issue create --title "<title>" --body-file <plan-file>` で `.plan/` ファイルを直接渡し、全文ミラーする
6. **2-step sync**: 返された URL を `.plan/` 本文に追記し、`gh issue edit <number> --body-file <plan-file>` で再同期する
7. 必要なら issue body に Mermaid 図を含める（使いどころは plan-template.md を参照）

### 既存 issue 更新の例外

既存 issue の更新は **ユーザが issue 番号 / 既存 issue 更新を明示した場合だけ** 扱う（例: "この計画を issue #25 に反映して" / "既存の計画 issue を更新して" / `/km:plan 25`）。

- `gh issue view <number> --json number,title,body,url,state` で対象を確認する
- body に `<!-- km:plan:managed -->` marker があれば `.plan/` ファイルを直接 `gh issue edit <number> --body-file <plan-file>` で更新できる
- marker が無い既存 issue は km:plan 管理外の可能性があるため、自動で全文置換せず更新前にユーザに確認する
- **title**: 原則 body のみ更新。タイトルが大きく変わり既存 title と齟齬が出る場合だけ、ユーザに可否を確認してから `gh issue edit <number> --title <new-title>` を実行する（自動判定しない）

## Phase 5: Report

`.plan/` のパス、issue URL、意図的に残した受け入れ済みリスク、未同期があればその旨をユーザに報告する。計画は **検証可能な作業単位に分解済み**（plan-template.md）なので、issue はそのまま km:github-workflow の実装タスク列として渡り、実装 agent が再分解せず最初の作業単位から着手できる。

## Secret Check

plan 本文は GitHub issue に全文ミラーされるため、秘密情報の混入は public 公開に直結する。`.plan/` がローカル ignore されていても、検出時にファイルがディスクに残れば事故リスクは減らない。Phase 2 (pre-write) と Phase 4 (pre-issue) の 2 gate で、組み立て中の本文と最終本文の両方を走査する。

検出パターン:

- ファイル名 / path: `.env*`, `*.pem`, `*.key`, `*credentials*`, `*.pfx` を参照する行
- 認証情報のキー名（**大文字小文字を区別せず**、`=` でも `:` でも区切りを問わず値が付いている行）: `password`, `secret`, `token`, `api_key` / `apikey`, `credential`, `private_key` を名前に含むキー
- 認証情報の値パターン: `AKIA` / `ASIA`（AWS）, `ghp_` / `github_pat_`, `xox[baprs]-`（Slack）, `sk-`, `eyJ`（JWT）, `-----BEGIN ... PRIVATE KEY-----`, `Bearer ` を含む行
- ログ / スタックトレースの貼り付けに含まれがちな社内ホスト名・ユーザー名・内部 URL

検出が不確かな場合も issue 化前にユーザへ確認する。疑わしきは止める。

## Incorporating External Review Feedback

ユーザが外部レビュー結果を持ち込んだ場合（複数レビュアー・指摘多数を含むことがある）、「まとめて確認」して漏らす事故を避けるため次を行う。

1. **レビュアー別・指摘別にタスク化**: 利用可能な task / todo / checklist tool で各指摘を 1 件 1 タスクに分解する。無ければ番号付き check list で管理する。複数レビュアー分は出典別に併記し、内容が似ていても統合せず別タスクで扱う
2. **対応要否を個別判断**: タスクごとに対応価値を分析する。`CRITICAL` / `HIGH` は原則反映、`MEDIUM` / `LOW` は反映か「受け入れ済みリスク」移行かを個別判定する
3. **個別反映**: 対応すると決めた指摘だけを plan 本文へ直接反映する（複数件を 1 編集にまとめない）。本文への反映方針は Phase 3 step 3-4 と同じ（採否判断・反映経緯は本文に書かない）
4. **更新背景は issue コメントへ**（任意）: 共有したい採否判断・反映背景は `gh issue comment <number> --body-file -` で残す。本文には移さない
5. **re-sync**: 反映後に `.plan/` ファイルを更新し、**pre-issue Secret Check を通してから**（外部レビュー結果には log や認証情報が混じりやすい）`gh issue edit <number> --body-file <plan-file>` で issue body を再同期する

## Decision Rules

- 計画本文の章立ては固定せず、タスクの難しさに応じて必要な情報を過不足なく含める
- issue body は `.plan/` の **全文ミラー**。要約・抜粋ではなく同じ markdown を `--body-file` でそのまま渡す（別ファイルや heredoc で本文を組み立て直さない、`--body "..."` を使わない）
- `.plan/` はローカル一時作業場。共有成果物（issue 本文・PR 本文・commit message・issue/PR comments）から `.plan/` 配下の **具体的なファイル**（`.plan/YYYYMMDD-*.md` 等）を source of truth として参照させない（GitHub 読者は `.plan/` を読めない）。`.plan/` という機能・概念への言及は許容する。正本は GitHub issue / PR の URL に集約する
- 計画は作って終わりではなく、レビュー → 反映 → issue 化までが 1 単位

## Safety Rules

- Plan Mode 中は `.plan/`, `.gitignore`, GitHub issue を一切変更しない
- `.plan` が追跡済み、または既存 ignore ルールで除外済みなら `.gitignore` を自動編集しない
- 明示の無い限り既存 issue を探索・再利用しない
- marker の無い既存 issue は全文置換前にユーザへ確認する
- `gh issue create/edit` を行う全経路（新規作成・2-step sync・既存 issue 更新・外部レビュー反映後の再同期）で、実行前に pre-issue Secret Check を通す
- `gh issue create/edit` が失敗したら成功扱いせず、issue 未作成と、作成済みだが再同期失敗（`URL 未同期`）を区別して報告する
- 反復しても `CRITICAL` / `HIGH` が残り収束しない場合は issue 化を止め、ユーザに判断を委ねる
- PR 作成・ブランチ作成・**PR 分割の実行**・push は `km:github-workflow` の責務。本スキルは作業単位への分解（分割の設計）までを担い、分割の実行はしない
- 計画作成の意図が曖昧な場合は、書き込み前にユーザへ確認する
- 非 GitHub repo / `gh` 未インストール / `gh` 未認証はいずれも `.plan/` 出力で停止し、原因を区別して報告する
