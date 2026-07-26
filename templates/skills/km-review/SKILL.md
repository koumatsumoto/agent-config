---
name: km-review
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

**レビューの最大コストは false negative。** 見逃しを防ぐことに独立性と反証のコストを割く。通常の完了確認（完了条件・差分・テストの照合）は呼び出し元メインの責務で、本 skill はその上に載せる独立した追加レビュー。

判定は `PASS` / `BLOCKED`（CRITICAL / HIGH が残れば BLOCKED）/ `NOOP`（対象なし）。実行したものとスキップしたものの両方が分かるレポートを出す。

## 対象を決める

| 引数 | 対象 |
| --- | --- |
| なし（既定） | 未コミット差分 `git diff` → 無ければ current branch の `gh pr diff` → それも無ければ `NOOP` |
| `pr` / `pr:<n>` | `gh pr diff [<n>]`（失敗時は別スコープの指定を促す） |
| `<base>..<head>` / `<sha>` | `git diff <base>..<head>` / `git show <sha>`（解決できなければエラー終了） |
| `--repo <subtree>` | diff でなく現状コード全体。`git ls-files <subtree>` で列挙して読む |
| `--recheck` | BLOCKED 後の修正差分の再確認（`references/recheck.md`） |
| `quick` / `standard` / `thorough` | 深さのヒント。ユーザの明示指定は常に優先 |

裸の数字（`42`）は km-github-workflow の issue 番号引数と紛らわしいので、警告して `pr:42` の明示を求める。`--repo` は他モードおよび `--recheck` と併用しない。`--repo` で対象（binary / lockfile / generated を除く）が並列レビュアの context に収まらない規模なら、進まずサブツリーを絞るよう促す。

## 深さとレビュアを決める

次の軸で対象を測り、深さと起動するレビュアを自分で決める。

**規模**（変更行数・ファイル数）/ **新規経路**（新しい関数・エンドポイント・分岐・手順）/ **不可逆性**（公開 API・契約・スキーマ・データモデル・データ移行）/ **攻撃面**（認証・認可・秘密情報・外部入力・データの移動と削除・LLM の tool 実行と入力境界）/ **挙動資産か**

- 不可逆性 → architect、攻撃面 → security + adversary。データ移行は不可逆性の軸に属するが、データの移動・削除を伴うので owner は security + adversary
- 複数軸に触れる・広範囲・不可逆なら 3 名全員（`thorough`）へ引き上げる。迷ったら深い側へ倒す。深さラベルは起動構成と揃える（該当レビュアだけの起動は「`standard` + 昇格」、`thorough` は 3 名全員）
- **選んだ深さと理由を 1 行レポートに残す**（例: `thorough — 新規経路 + 不可逆な契約変更`）

変更構成は `docs-only` / `code-only` / `code+docs` / `test-or-config-or-chore-only` / `mixed`（判定材料が欠けるときと `--repo` は `mixed`）で分類する。**挙動資産**（skill / rule / `CLAUDE.md` / `AGENTS.md` / command / output-style など、agent に読み込まれて挙動を規定する prompt 定義）は `.md` でも実質コードなので、`docs-only` に落とさずコード相当（`code+docs`）に分類する。`**/skills/**` のようなパスや「frontmatter + 命令文体」は典型シグナルだが、判定基準は内容。人間向け文書（README・runbook・設計 doc・CHANGELOG）は挙動資産ではない。迷ったらコード側に倒す — 挙動資産が `docs-only` に落ちてコードレビュー層をスキップする fail-open を塞ぐ。

## 進め方

**自分で読む → 独立レビュアを走らせる → 統合して判定する → ドキュメントを見る。**

### 自分で読む

`docs-only` 以外では常に、`references/generalist-review.md` に従って main context で読む。ここで出た指摘も他レビュアと同じ重大度尺度で扱う。**CRITICAL / HIGH が出ても早期停止せず**、起動した全レビュアの完了を待って統合で判定する。

### 独立レビュアを走らせる

| レビュア | 見るもの |
| --- | --- |
| architect | 覆すのが高コストな決定と、repo 全体に複製される pattern |
| security | 脅威モデル・攻撃面・LLM 統合、および正当な利用者・運用者の事故 |
| adversary | 「この変更は正しくない / 目的を達成しない」と仮定して前提と不変条件を攻撃する |

**独立性を保って並列起動する** — 他レビュアの所見も暫定判定も渡さない。起動契約と報告の永続化は `references/dispatch.md`。`docs-only` / `test-or-config-or-chore-only` では起動しないが、高リスク（CI 権限・デプロイ・秘密情報など）なら昇格して起動してよい。昇格したときは理由 1 行をレポートに残す。

### 統合して判定する

`references/verdict.md` に従う。main の強み（ツール実行・長コンテキスト・自己反証）を「**誤った `PASS` を出さない**」ことに使い、`PASS` を出す前に必ず自分の `PASS` を反証する。

### ドキュメントを見る

コード / 設計が確定した最終状態に対して `references/doc-review.md` を読み main で実施する。`docs-only` なら主レビューとして実施する。`code-only` / `code+docs` / `mixed` は判定が `PASS` になってから実施し、`BLOCKED` なら defer してレポートに明記する。`test-or-config-or-chore-only` は skip（config が高リスクなら実施）。ここで CRITICAL / HIGH が出たら最終判定を `BLOCKED` に更新する。

## 指摘をどう扱うか

好み・様式の指摘は出さず「本質的に改善すべきもの」だけを出す。**出した指摘は LOW を含め原則すべて直す。** 変更に起因する / 目的達成に必要な指摘は同一 PR 内で直し、follow-up issue にするのは PR 目的の外の既存問題・大規模リファクタに限る（レビューで露見した自分の変更の欠陥は in-scope）。大規模修正・仕様変更・設計トレードオフでユーザ判断が要るものだけ、残すなら「受け入れ済みリスク」として明示記録する。
