---
name: km:review
description: >
  Reviews uncommitted changes, committed ranges, single commits, PRs, or repo subtrees with
  selectable depth (quick / standard / thorough). Use whenever the user says "レビューして" or
  any target-aware variant such as "PR をレビューして", "<sha>..<sha> をレビューして",
  "リポジトリ全体をレビューして", or "深くレビューして". Prefer this skill over running individual
  phases.
argument-hint: "[target] [level] [--skip-gating]"
---

# Review

複数の review 観点を統合する review orchestrator。レビュー対象を引数 / 会話文脈から決め、レベルに応じて Phase を起動する。

## レビューの目的

開発者は目の前の実装に集中するため、設計上の問題・品質特性の見落とし・ドキュメント不整合が視野外になりやすい。本 skill は Phase 2 (generalist code review)、Phase 3 (3 専門家による別視点レビュー)、Phase 4 (doc review) を統合し、CRITICAL/HIGH を漏れなく検出する。

## Success Criteria

- 変更タイプと対象スコープに応じた Phase / 専門家を正しく選ぶ
- 要求されたレベルに応じて Phase を絞り込む
- Phase 2 / Phase 3 (3 専門家) / Phase 4 のいずれかで CRITICAL または HIGH があれば BLOCKED とする
- 実行した Phase とスキップした Phase の両方が分かるレポートにする
- `--skip-gating` 指定時は CRITICAL/HIGH 残置でも進行し、Phase 5 でユーザに判断を委ねる

## Workflow

1. **Phase 1**: 引数解析 + 対象スコープ解決 + 変更タイプ/レベル決定
2. **Phase 2**: コードレビュー (generalist) — main コンテキスト、`code-review.md` を Read して実行
3. **Phase 3**: 第三者専門家レビュー (3 名並列、Task tool) — `thorough` のみ
4. **Phase 4**: doc-review — main コンテキスト、`doc-review.md` を Read して実行
5. **Phase 5**: 統合 + コミット判定

## Phase 1: 引数解析 + 対象スコープ解決 + 変更タイプ/レベル決定

### Phase 1a. 引数パース仕様

`$ARGUMENTS` は単一文字列。**tokenize + classify の 2 段アルゴリズム** で解析する。

1. **flag 抽出 (位置不問)**: `--` プレフィックスの token を先に抽出
   - `--skip-gating`: gating 無効化フラグ (escape hatch)
   - `--uncommitted`: 明示の未コミットモード
   - `--repo`: リポジトリ全体モード (サブツリー指定が後続必要)
2. **残り token を順序評価**: flag 抽出後の残り token を以下の優先順位で分類
   1. 完全一致 `^pr$` または `^pr:[0-9]+$` → PR モード
   2. `..` を含む → コミット範囲モード
   3. `^[0-9a-f]{7,40}$` → 単一コミットモード (sha)
   4. `^(quick|standard|thorough)$` → level 指定
   5. それ以外 → 曖昧入力として警告
   6. 全 token なし → 既定 (未コミット差分)
3. **裸の数字 `42` は曖昧入力として警告**。`km:github-workflow` の `[issue-number]` 引数との混同を防ぐ。明示的に `pr:42` を要求する

### Phase 1b. 対象スコープ解決

| 対象 | コマンド | フォールバック |
|---|---|---|
| 未コミット (既定) | `git diff` + `git diff --name-only` | — |
| `<base>..<head>` | `git diff <base>..<head>` | base/head が解決できなければエラー終了 |
| `<sha>` | `git show <sha>` | sha が見つからなければエラー終了 |
| `pr` | `gh pr diff` (current branch の PR) | `gh` 未認証 or 非 GitHub repo / PR 未存在ならエラー + 別スコープ指定を促す |
| `pr:<n>` | `gh pr diff <n>` | 同上 |
| `--repo <subtree>` | サブツリー必須。明示サブツリーがなければ「対象が広すぎる」と警告し、サブツリー指定を要求 | — |

**Context budget 防御**: `--repo <subtree>` 時は diff サイズを実測し、**40k tokens を超える場合**はユーザに警告し、サブツリーをさらに絞るよう促す (3 並列 subagent の合算考慮)。

下位コンポーネント (Phase 2 / experts / Phase 4) は **「解決済みのファイル一覧 + diff 内容」** を共通コンテキストで受け取る。

### Phase 1c. 変更タイプ判定とレベル選択

変更タイプの判定入力は対象スコープに応じて変える:

| 対象 | 変更タイプ判定の入力 |
|---|---|
| 未コミット / `<base>..<head>` / `<sha>` | ファイル拡張子・変更パターン + コミットメッセージ (`refactor:` 等の Conventional 接頭辞) |
| `pr` / `pr:<n>` | `gh pr view` のタイトル/ラベル + diff |
| `--repo <subtree>` | 変更タイプ判定を行わず常に `mixed` 扱い。全 Phase を有効化 |

変更構成: `docs-only` / `code-only` / `code+docs` / `test/config/chore` のいずれか。

レベルは `thorough` / `standard` / `quick`。Phase 1a で抽出されなければ会話文脈から推論、それも無理なら既定 `standard`。

### km:plan からの引数なし dispatch のデフォルト

`km:plan` の "PR まで作る" フローでは引数なしで呼ばれる:
- まず `git diff` で未コミット差分の有無を確認
- 未コミットなしかつ現ブランチが push 済みなら `pr` (current branch の PR) を試行
- それも無ければ「変更なしのため終了」と出力

## Phase 2: コードレビュー (generalist)

`code-review.md` を Read してその指示に従って main コンテキストでレビューを実施する。

**起動条件**: docs-only 以外 (`code-only` / `code+docs` / `test/config/chore` / `mixed`) で常時起動。

**入力**: Phase 1b で解決した「変更ファイル一覧 + diff 内容」、Phase 1c の変更タイプ。

**出力**: 重大度別件数 (CRITICAL/HIGH/MEDIUM/LOW) + 個別所見。

## Phase 3: 第三者専門家レビュー (3 名並列)

`thorough` レベルでのみ起動。docs-only / `test/config/chore` 単独では起動しない。

### 起動方法

**同一メッセージ内で Task tool を 3 個並行発行** する。各 Task tool に以下のプロンプトを渡す:

```
あなたは <role> 専門家です。templates/skills/review/experts/<role>.md を Read してから着手してください。

レビュー対象:
- 変更ファイル一覧: <Phase 1b の出力>
- diff 内容: <raw diff>
- 変更タイプ / 規模: <Phase 1c の出力>

担当観点の参照リソース (担当分のみ Read):
- templates/skills/review/references/iso-25010/<該当ファイル>.md

既知情報:
- Phase 2 で確定した MEDIUM/LOW 指摘リスト (偽陽性フィルタの参考):
  <Phase 2 の MEDIUM/LOW 指摘>
- 意図情報: <km:plan の GitHub issue 本文があれば添付、なければ "no intent context">

出力形式: templates/skills/review/experts/report-format.md に従う
```

`<role>` は `architect`, `qa`, `security` のいずれか。3 つを同一メッセージ内で発行する (sequential ではなく parallel)。

### 担当配分

| 専門家 | 視点 | 担当 ISO/IEC 25010 特性 |
|---|---|---|
| architect | 長期・横断・非機能 | 2 (性能効率性), 3 (互換性), 7 (保守性), 8 (柔軟性) |
| qa | 異常系・境界・運用品質 | 1 (機能適合性), 4 (インタラクション能力), 5 (信頼性) |
| security | 脅威モデル・攻撃面 | 6 (セキュリティ), 9 (安全性) |

### Phase 2 との住み分け

`templates/skills/review/references/scope-alignment.md` を参照。Phase 2 は code-level (関数・モジュール・システム境界の正しさ)、Phase 3 architect は「異なる視点 (長期・横断・非機能)」。

## Phase 4: doc-review

`doc-review.md` を Read してその指示に従って main コンテキストでレビューを実施する。**Phase 3 完了後** (sequential、並走させない)。

### 起動モード

Phase 1c で確定した変更構成に基づいて以下のいずれかで起動:

- **docs-only** (docs 変更のみ) → **full モード**。Phase 2/3 は skip して直接 Phase 4 へ
- **code+docs** (コード変更とドキュメント変更の両方) → **full モード**
- **code-only** (コードのみ変更、docs 変更なし) → **need-check モード** (軽量、ループなし、CRITICAL/HIGH 出さない)
- **test / config / chore のみ** → **Phase 4 skip**

## Phase 5: 統合 + コミット判定

- Phase 2 + Phase 3 (3 専門家) + Phase 4 の指摘を重大度ごとに合算
- いずれかに CRITICAL/HIGH があれば `BLOCKED`、なければ `PASS`
- 統合サマリーは `report-format.md` の形式に従う

## Sequential gating

### 進行ゲート

**Phase N で `CRITICAL` または `HIGH` の検出件数が 0 でない限り、Phase N+1 を起動してはならない** (`--skip-gating` 指定時を除く)。LOW/MEDIUM は次 Phase の起動を阻まない。

### ループ上限 (`--skip-gating` 未指定時)

- Phase 2: 同 Phase 連続再実行 5 周まで。超過は警告してユーザ判断
- Phase 3 / Phase 4-full: 同 Phase 連続再実行 3 周まで。超過は現状の指摘リストを提示してユーザ判断
- Phase 4-need-check: ループ対象外 (1 回のみ実行)

### 修正の担当

orchestrator が編集ツールで自動修正しない。CRITICAL/HIGH が検出されたら **ユーザに修正を促し、次回の入力で同 Phase を再実行** する。

### カウンタリセット

上流 Phase に戻った場合 (例: Phase 3 で修正後に Phase 2 観点が崩れた場合) は下流 Phase のカウンタをリセット。

### `--skip-gating` のセマンティクス

1. **Phase 内ループのスキップ**: 各 Phase 内で CRITICAL/HIGH を検知しても再実行ループに入らず、1 周のみ実行
2. **Phase 進行ゲートのスキップ**: 下流 Phase への進入可否判定をスキップし、CRITICAL/HIGH 残置でも進行
3. **Phase 5 判定は通常どおり**: CRITICAL/HIGH があれば `BLOCKED` を表示するが、orchestrator はユーザに「以下の指摘があるが続行するか / 中止するか」を提示して判断を仰ぐ (自動で中止しない)

### Phase 内並列性 (Phase 2 → Phase 3)

Phase 2 の CRITICAL/HIGH がゼロになった時点で Phase 3 (3 名並列) を起動する。Phase 2 の MEDIUM/LOW 修正は Phase 3 と並走可。Phase 4 は Phase 3 完了後に sequential 実行 (並走させない)。

## レベル別実行マトリクス

| Level | Phase 1 | Phase 2 (generalist) | Phase 3 (3 experts) | Phase 4 (doc) | Phase 5 |
|---|---|---|---|---|---|
| `quick` | ✓ | ✓ | スキップ | code-only → need-check / その他 → full | ✓ |
| `standard` | ✓ | ✓ | スキップ | code-only → need-check / その他 → full | ✓ |
| `thorough` | ✓ | ✓ | ✓ (3 名並列) | code-only → need-check / その他 → full | ✓ |

docs-only 変更は level によらず Phase 4 full モードのみ実行する (Phase 2/3 skip)。

## 指摘対応の方針

検出された指摘は `LOW` を含め原則すべて対応する。以下の場合のみユーザ判断に委ねる:

- 大規模な修正が必要で影響範囲が広い
- 仕様変更を伴う
- 設計判断のトレードオフがある

合意済み判断や影響大の修正で残す場合は「受け入れ済みリスク」形式 (重大度・残す理由・後続対応条件) で明示記録する。

## Mermaid 図

```mermaid
flowchart TD
  Args[$ARGUMENTS] --> P1a[Phase 1a: 引数パース]
  P1a -->|曖昧入力| Err[警告 + ユーザ指定要求]
  P1a --> P1b[Phase 1b: 対象スコープ解決]
  P1b -->|gh 不可 / sha 未存在 / context >40k| Err
  P1b --> P1c[Phase 1c: 変更タイプ + レベル決定]
  P1c -->|docs-only| P4full[Phase 4 full: doc-review main]
  P1c -->|code change| P2[Phase 2: code-review generalist main]
  P2 -->|CRITICAL/HIGH ゼロ or --skip-gating| P3decide{level == thorough?}
  P2 -->|CRITICAL/HIGH あり 最大 5 周| P2
  P2 -->|5 周超過| UserJudge[ユーザ判断]
  P3decide -->|yes| P3[Phase 3: 3 experts 並列 Task tool]
  P3decide -->|no, code-only| P4check[Phase 4 need-check: 軽量 main]
  P3decide -->|no, code+docs| P4full
  P3 -->|各 expert CRITICAL/HIGH ゼロ or --skip-gating| P4full
  P3 -->|CRITICAL/HIGH あり 最大 3 周| P3
  P3 -->|3 周超過| UserJudge
  P4full -->|CRITICAL/HIGH ゼロ or --skip-gating| P5[Phase 5: 統合 + コミット判定]
  P4full -->|CRITICAL/HIGH あり 最大 3 周| P4full
  P4full -->|3 周超過| UserJudge
  P4check --> P5
  UserJudge -->|Continue| P5
  UserJudge -->|Abort| End[終了 - 統合レポートなし]
```

出力形式は `report-format.md` を参照。
