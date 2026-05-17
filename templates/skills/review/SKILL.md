---
name: km:review
description: >
  Reviews code changes (uncommitted, commits, PRs, subtrees) for bugs, design, security, and
  quality. Use when the user says "レビューして" or "PR をレビューして".
argument-hint: "[target] [level]"
---

# Review

複数の review 観点を統合する **単発診断** の review orchestrator。レビュー対象を引数 / 会話文脈から決め、レベルに応じて Phase を起動する。

## Success Criteria

- 変更タイプと対象スコープに応じた Phase / 専門家を正しく選ぶ
- Phase 2 / Phase 3 (3 専門家) / Phase 4 のいずれかで CRITICAL または HIGH があれば BLOCKED とする
- 実行した Phase とスキップした Phase の両方が分かるレポートにする

## Phase 1: 引数解析 + 対象スコープ解決 + 変更タイプ/レベル決定

### Phase 1a. 引数パース仕様

`$ARGUMENTS` は単一文字列。flag 抽出 → 残り token 分類の順で解析する。

1. **flag 抽出 (位置不問)**: `--` プレフィックス token を先に取り出す
   - `--uncommitted`: 明示の未コミットモード (値なし)
   - `--repo <subtree>`: 直後の token を subtree value として同時消費。直後が無い / level token / 別 flag なら「サブツリー必須」エラー終了
2. **残り token を順序評価**: 先頭一致で以下に分類 (同種が複数あれば最後を有効)
   1. `^pr$` または `^pr:[0-9]+$` → PR モード
   2. `..` を含む → コミット範囲モード
   3. `^[0-9a-f]{7,40}$` → 単一コミットモード (sha)
   4. `^(quick|standard|thorough)$` → level 指定
   5. それ以外 → 曖昧入力として警告
   6. 全 token なし → 既定 (未コミット差分)
3. **裸の数字 `42` は曖昧入力として警告**。`km:github-workflow` の `[issue-number]` 引数との混同を防ぐ。明示的に `pr:42` を要求する
4. **`pr` 系と `--repo` の同時指定はエラー終了** (排他モード)

### Phase 1b. 対象スコープ解決

| 対象 | コマンド |
|---|---|
| 未コミット (既定) | `git diff` + `git diff --name-only` |
| `<base>..<head>` | `git diff <base>..<head>` |
| `<sha>` | `git show <sha>` |
| `pr` / `pr:<n>` | `gh pr diff [<n>]` (失敗時は別スコープ指定を促す) |
| `--repo <subtree>` | `git ls-files <subtree>` で対象ファイル列挙し各ファイルを Read (diff ではなく現状コード全体が対象) |

base/head/sha が解決できなければエラー終了。下位コンポーネント (Phase 2 / experts / Phase 4) は「解決済みのファイル一覧 + diff 内容」を共通コンテキストで受け取る。

**Context budget 防御 (`--repo` のみ)**: 対象テキストファイル総行数を `1 行 ≈ 25 tokens` で概算し、**約 1600 行 (≈ 40k tokens) を超える場合は Phase 2 以降を強制停止** してサブツリーを絞るよう促す (3 並列 subagent の合算 context を考慮した閾値)。binary / lockfile / generated は除外。

### Phase 1c. 変更タイプ判定とレベル選択

変更タイプの判定入力:

| 対象 | 判定入力 |
|---|---|
| 未コミット | ファイル拡張子・変更パターン |
| `<base>..<head>` / `<sha>` | 拡張子・変更パターン + コミットメッセージ (`refactor:` 等の Conventional 接頭辞) |
| `pr` / `pr:<n>` | `gh pr view` のタイトル/ラベル + diff |
| `--repo <subtree>` | 常に `mixed` 扱い (判定省略) |

コミットメッセージ取得失敗 / `gh pr view` 失敗時は拡張子のみで判定し変更構成は `mixed` にフォールバック。

変更構成 (正規ラベル): `docs-only` / `code-only` / `code+docs` / `test-or-config-or-chore-only` / `mixed`。レベルは `thorough` / `standard` / `quick` で、Phase 1a で抽出されなければ会話文脈から推論、それも無理なら既定 `standard`。

### 引数なし呼び出しのデフォルト動作

`/km:review` (引数なし) では以下のフォールバック順で対象を決定する。`km:plan` / `km:github-workflow` 経由の dispatch でも同じ動作:

1. `git diff` で未コミット差分の有無を確認 → あれば未コミットモード
2. 未コミットなしかつ現ブランチが push 済みなら `gh pr diff` (current branch の PR) を試行 → 成功すれば PR モード
3. それも無ければ「対象がないため終了」と出力

## Phase 2: コードレビュー (generalist)

`code-review.md` を Read してその指示に従って main コンテキストでレビューを実施する。

**起動条件**: docs-only 以外 (`code-only` / `code+docs` / `test/config/chore` / `mixed`) で常時起動。

**入力**: Phase 1b で解決した「変更ファイル一覧 + diff 内容」、Phase 1c の変更タイプ。

**出力**: 重大度別件数 (CRITICAL/HIGH/MEDIUM/LOW) + 個別所見。

## Phase 3: 第三者専門家レビュー (3 名並列)

`thorough` レベルでのみ起動。`docs-only` / `test-or-config-or-chore-only` では起動しない。

### 起動方法

実行環境の subagent 機構で 3 expert を **同一メッセージ内で並列起動** する (Claude Code では Task tool、Codex CLI では subagent と読み替え)。subagent prompt 内の参照パスは `<review skill root>/...` 形式で書き、orchestrator が installed skill root に解決して渡す。`<role>` / `<Phase 2 の出力>` などのプレースホルダも orchestrator が置換してから渡す (未置換のまま subagent に渡さない)。各 subagent に以下のプロンプトを渡す:

```
あなたは km:review Phase 3 の <role> 専門家です。

## 役割の前提
- 同じ diff を architect / qa / security の 3 名が並列で別視点でレビューしています
- あなたは <role> の視点に集中し、他者の担当 ISO 副特性には踏み込まないでください
- 他者と矛盾する判定をしてもよい (Phase 5 統合で解消される)

## Read 順序
まず `<review skill root>/experts/<role>.md` と `<review skill root>/experts/report-format.md` を読み (役割と判定基準・確信度・重複時 SOT を把握)、その後 diff を pre-scan して該当しそうな ISO 副特性に当たりをつける。`<review skill root>/references/iso-25010/<該当ファイル>.md` は **判断に必要なものだけ** Read する (該当 1-2 ファイル、判断保留や thorough 深掘りが必要なら追加で担当 reference を読む)。

## レビュー対象
- 変更ファイル一覧: <Phase 1b の出力>
- diff 内容: <raw diff>
- 変更タイプ / 規模: <Phase 1c の出力>

## 既知情報
- Phase 2 で確定した MEDIUM/LOW 指摘リスト (偽陽性フィルタの参考、同ファイル/行/同観点は除外。ただし security は重大度再評価可):
  <Phase 2 の MEDIUM/LOW 指摘 (markdown のまま貼付)。Phase 2 が指摘ゼロなら "none">
- 意図情報 (km:plan issue 本文 / 会話文脈):
  <intent または "no intent context">
  intent がある場合は「diff が intent を達成しているか」を担当観点で 1 行コメントする

## 失敗ケースの扱い
- 該当観点なし: report-format.md の「指摘ゼロ時」フォーマット
- context 不足で判定しきれない: 「判定保留」セクションに「何があれば判定できるか」を書く
- diff が大きすぎる: 担当 ISO 副特性に該当しそうな箇所だけ深掘り、それ以外は判定保留
- diff から判定するために repo 内の近隣ファイル (middleware / interceptor / 類似 endpoint) が必要なら最大 5 個まで Read してよい

## 出力形式
`<review skill root>/experts/report-format.md` に従う。判定基準・確信度・偽陽性フィルタ・役割固有フィールド (HIGH 以上必須) はすべてそこに集約されている。
```

`<role>` は `architect`, `qa`, `security` のいずれか。3 つを同一メッセージ内で発行する (sequential ではなく parallel)。

**ロール識別子と出力見出しのマッピング**: `architect` → `### システムアーキテクト`、`qa` → `### QA 専門家`、`security` → `### セキュリティ専門家`。

### 担当配分

| 専門家 | 視点 | 担当 ISO/IEC 25010 特性 |
|---|---|---|
| architect | 長期・横断・非機能 | 2 (性能効率性), 3 (互換性), 7 (保守性), 8 (柔軟性) |
| qa | 異常系・境界・運用品質 | 1 (機能適合性), 4 (インタラクション能力), 5 (信頼性) |
| security | 脅威モデル・攻撃面 | 6 (セキュリティ), 9 (安全性) |

Phase 2 ↔ Phase 3 architect の住み分けは `references/scope-alignment.md` に集約。

## Phase 4: doc-review

`doc-review.md` を Read してその指示に従って main コンテキストでレビューを実施する。**Phase 3 完了後に sequential 起動** (Phase 3 がスキップされた level では Phase 2 完了後)。並走はさせない。

### 起動モード

Phase 1c で確定した変更構成に基づいて以下のいずれかで起動:

- **`docs-only`** → **full モード**。Phase 2/3 は skip して直接 Phase 4 へ
- **`code+docs`** → **full モード**
- **`mixed`** (`--repo` 経由) → **full モード**
- **`code-only`** → **need-check モード** (軽量、CRITICAL/HIGH 出さない)
- **`test-or-config-or-chore-only`** → **Phase 4 skip**

need-check モードで内部的に HIGH/CRITICAL 相当の検出があった場合は **MEDIUM に強制降格** して報告する。

## Phase 5: 統合 + コミット判定

- Phase 2 / Phase 3 (3 専門家) / Phase 4 の指摘を重大度ごとに合算し、CRITICAL/HIGH があれば `BLOCKED`、なければ `PASS`
- Phase 2 と Phase 3 で同観点が重複した場合の取り扱いは `experts/report-format.md` の「Phase 2 との重複時 (SOT ルール)」が唯一の規約
- intent context があった場合は各 expert の「intent との整合性 1 行コメント」を統合サマリーに含める

統合レポート末尾に **優先順位付きアクションリスト** を生成する:

1. **マージ前必須** (CRITICAL/HIGH): 該当ファイル + 修正方針サマリで「PASS への最短経路」を示す
2. **マージ後推奨** (MEDIUM): follow-up issue 候補
3. **受け入れ可能** (LOW): 残しても害なし
4. **指摘の相互関係**: 同一根本原因でグルーピング可能なら明示

詳細フォーマットは `report-format.md`。

## 進行ゲート

**Phase N で CRITICAL/HIGH があれば Phase N+1 を起動しない**。当該 Phase で停止し Phase 5 で `BLOCKED` を報告して終了。LOW/MEDIUM は次 Phase 起動を阻まない。Phase 3 は 3 expert 全員完了後に合算判定する。

## レベル別実行マトリクス

| Level | Phase 2 | Phase 3 | Phase 4 |
|---|---|---|---|
| `quick` | ✓ (浅) | スキップ | 変更構成依存 |
| `standard` | ✓ | スキップ | 変更構成依存 |
| `thorough` | ✓ | ✓ (3 名並列) | 変更構成依存 |

変更構成による override:

- `docs-only` → Phase 2/3 skip、Phase 4 full のみ
- `test-or-config-or-chore-only` → Phase 3/4 skip (Phase 2 のみ実行)

`quick` と `standard` は Phase 起動条件こそ同じだが、`quick` では Phase 2 / Phase 4 内部の検査深度を絞る (詳細は `code-review.md` / `doc-review.md` の深度表)。

## 指摘対応の方針

検出された指摘は `LOW` を含め原則すべて対応する。大規模修正 / 仕様変更 / 設計トレードオフのいずれかに該当する場合のみユーザ判断に委ね、残す場合は「受け入れ済みリスク」形式 (重大度・残す理由・後続対応条件) で明示記録する。出力形式は `report-format.md` を参照。
