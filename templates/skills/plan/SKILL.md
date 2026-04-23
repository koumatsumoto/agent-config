---
name: km:plan
description: Creates a reviewed implementation plan in `.plan/YYYYMMDD-<slug>.md` and mirrors the full body into a GitHub issue. Use when the user says "計画を作って", ".plan に出して", "計画を issue にして", "計画レビューしてから issue 化", "この計画ファイルをレビューして", or otherwise asks for a pre-implementation plan, a planning issue, or a review of a plan file / planning content. Not for "実装して", "コミットして", or "PR にして" — those belong to km:github-workflow / km:commit. For general "レビューして" on changes, use km:review; only plan-file / planning-content review stays with km:plan. For "計画を作って PR まで", km:plan runs first and hands the PR step off to km:github-workflow.
argument-hint: "[title-or-topic]"
---

# Plan

実装前の計画を Plan Mode で作り込み、通常実行モードで `.plan/` に詳細版を書き出し、そのファイルを対象に agentic な計画レビューを行い、レビュー反映後の本文を GitHub issue に全文ミラーする。

## Context

- Repo: !`git rev-parse --is-inside-work-tree 2>/dev/null || echo "(not a git repo)"`
- Branch: !`git branch --show-current 2>/dev/null`
- `.plan/` tracked?: !`git ls-files -- .plan .plan/ 2>/dev/null | head -1 || echo "(none)"`
- `.plan/` ignored?: !`git check-ignore -q .plan/ 2>/dev/null && echo "yes" || echo "no"`
- `.gitignore` has `.plan/`: !`grep -E '^\.plan/?$' .gitignore 2>/dev/null || echo "(absent)"`

GitHub / `gh` の状態は draft-only 用途では不要なので Context では取得しない。GitHub issue phase (下の「GitHub Issue 作成とミラー」) の手順 1-2 で `gh auth status` / `gh repo view` を実行する。

## Success Criteria

- Plan Mode 中は `.plan/`, `.gitignore`, GitHub issue を変更しない
- 書き出し先は `.plan/YYYYMMDD-<slug>.md`。`.plan/` が git 追跡・ignore 済みかは書き出し前に確認する
- 計画本文は背景・制約・判断理由・却下案・実装手順・検証条件・レビュー結果を含み、GitHub issue だけでも読める形にする
- agentic review を最大 2 pass 行い、未解決の `CRITICAL` / `HIGH` があれば issue 化しない
- GitHub 管理 repo では新規 issue を作り、`.plan/` ファイルを `--body-file` に直接渡して全文ミラーする
- 新規 issue 作成後は URL を `.plan/` に追記し、再度 `gh issue edit --body-file` で同期する
- 非 GitHub repo / `gh` 未認証なら `.plan/` 出力までで止め、その理由を報告する

## Trigger Signals

**計画作成・`.plan/`・計画 issue 化** が明示された発話のときだけ使う。

- 例: "計画を作って" / "実装計画を作成して" / ".plan に出して" / "計画を issue にして" / "計画レビューしてから issue 化" / "この計画ファイルをレビューして" / "/km:plan <topic>"
- 非 trigger: "実装して" / "コミットして" / "PR にして" — これらは計画作成を明示していない
- 「レビューして」は対象で分岐: 計画ファイル / 計画内容のレビューなら `km:plan`、変更差分のレビューなら `km:review`
- 優先度:
  - 「計画を作って PR まで」のように計画と PR delivery が同時依頼された場合は、まず `km:plan` で計画と issue 化まで行い、PR delivery は後続の `km:github-workflow` に委ねる
  - 「issue 化してから PR」だけで計画作成が明示されない場合は `km:github-workflow` を優先する
  - 「この計画ファイルをレビューして」は `km:plan` の計画レビュー、「この変更をレビューして」は `km:review`

## Entry Mode

次の 3 mode に固定する。

- `draft-only`: Plan Mode 中、または「まず計画だけ」と依頼された場合。調査、質問、計画下案作成、`<proposed_plan>` 提示まで行い、書き込み前に停止する。停止時は「通常実行モードで `.plan` と issue に出すには、この計画を `.plan` と issue に出して、と依頼する」と報告する
- `materialize-existing-plan`: Plan Mode ではない状態で、直近の合意済み計画を会話から復元できる場合。計画内容を再設計せず、詳細本文化 → `.plan/` 出力 → 計画レビュー → issue 化に進む
- `full-normal-mode`: Plan Mode ではない状態で、最初から「計画を作って `.plan` と issue に出して」と依頼された場合。必要な質問と調査を行い、書き込み前に高影響の未決事項を解消してから materialize まで進む

直近の合意済み計画を会話から復元できない場合は推測で書き出さず、計画内容を再確認する。

## Workflow

1. repo と依頼内容を把握する。`$ARGUMENTS` があれば計画タイトルや既存 issue 番号のヒントとして扱う
2. entry mode を決める（`draft-only` / `materialize-existing-plan` / `full-normal-mode`）
3. `draft-only` では Plan Mode で質問・調査・下案作成を行い、`<proposed_plan>` を提示して停止する
4. materialize に進む場合、**副作用を出す前** に「`.gitignore` 安全確認」節の 4 ステップ（git repo 判定 → tracked 判定 → ignore 判定 → 必要なら `.gitignore` 更新）を実行する。`.plan` が tracked / blocked ならここで停止してユーザー確認
5. 安全確認が通った後にのみ `mkdir -p .plan` で出力先を確保する（tracked file 衝突や意図しない動作を避けるため、順序を逆にしない）
6. `references/plan-template.md` を読み、その観点集に沿って plan 本文を **メモリ上で** 組み立てる。先頭近くに `<!-- km:plan:managed -->` marker を含める
7. **pre-write Secret Check**: 組み立てた plan 本文に「Secret Check」節のパターンを適用する。検出したらファイル書き出しを行わず停止し、ユーザーにマスキングを依頼する（検出時は秘密情報をディスクに残さない）
8. Secret Check を通過したら `.plan/YYYYMMDD-<slug>.md` に書き出す
9. `references/plan-review-checklist.md` を読み、その観点集で `.plan/` ファイルを対象に agentic 計画レビューを最大 2 pass 行う。未解消の `CRITICAL` / `HIGH` があれば issue 化を止めて報告する
10. **pre-issue Secret Check (再チェック)**: レビューの過程で plan 本文に追加された情報が secret を含まないか、issue 化直前にもう一度 Secret Check をかける。検出時はファイルを削除せず、ユーザーに対処依頼して停止
11. GitHub 管理 repo なら新規 issue を作る（既存 issue 再利用はユーザーが明示した場合のみ。後述）
12. 新規 issue 作成後、返された URL を `.plan/` 本文に追記し、`gh issue edit <number> --body-file <plan-file>` で再同期する（2-step sync）
13. 結果をユーザーに報告する（`.plan/` のパス、issue URL、未反映の受け入れ済みリスク）

## `.plan/` 出力ルール

- ファイル名は `.plan/YYYYMMDD-<slug>.md`。日付 prefix は区切りなしの `YYYYMMDD`（例: `.plan/20260423-km-plan-skill.md`）
- slug は英小文字 ASCII の kebab-case（`[a-z0-9-]+`）、長さは 50 文字以下を目安にする。日本語依頼でも repo 名や issue title から短い英語 slug を作る
- 適切な英語 slug が作れない場合は `plan`。同日付内で既存の `.plan/YYYYMMDD-*.md` と衝突する場合は `-2`, `-3` の suffix を付ける（衝突判定は同日付内のみ）
- plan 本文の先頭近くに `<!-- km:plan:managed -->` marker を入れる（`km:plan` 管理 issue の識別に使う）
- 計画本文の構成は `references/plan-template.md` の観点集で組み立てる。タスクの性質に合わせて節の順序や粒度は変える。固定テンプレートではない

## `.gitignore` 安全確認

`.plan/` は作業中のローカル計画を置く場所で、通常は git に含めない。出力前チェックを以下の順で行う。

1. `git rev-parse --is-inside-work-tree` で git repo か確認する。git repo でなければ `.gitignore` を編集せず `.plan/` 出力のみ行う
2. `git ls-files -- .plan .plan/` で `.plan` 配下が追跡済みか確認する。追跡済みなら repo 方針と衝突するため、自動で `.gitignore` を編集せずユーザーに確認する
3. `git check-ignore -q .plan/` で既に ignore されているか確認する。`.git/info/exclude` などで除外済みなら `.gitignore` は編集しない
4. 追跡済みでなく ignore もされていない場合だけ、`.gitignore` に `.plan/` を追加する。`.gitignore` がなければ新規作成する

## Agentic Review

- レビュー前に `references/plan-review-checklist.md` を読む
- 計画は `.plan/` に書き出した後、そのファイルを対象に第三者目線でレビューして精度を上げる
- 基本は checklist の観点でレビューする。高リスク計画では専門家ロールレビューを追加する
- レビュー実行者の選び方:
  - Task tool / subagent が使える環境（Claude Code の Agent tool、Codex CLI のサブエージェントなど）では、**別エージェントに `.plan/` ファイルを渡してレビュー**してもらう。メイン agent の視点バイアスを避ける意図
  - 使えない環境では、メイン agent が「第三者レビュー」と明示して同じ観点で critical に読み直す。自分の計画を評価するバイアスを自覚し、通常の Q&A より厳しめに判定する
- レビュー結果は `CRITICAL` / `HIGH` / `MEDIUM` / `LOW` と対象箇所・問題・修正案で記録する
- **反映した指摘は plan 本文の「計画レビュー結果」相当の節（`references/plan-template.md` の「計画レビューで何が指摘され、どう反映したか」観点）に追記する**。修正後の最終本文を plan file に残し、reviewing の痕跡を読者が追えるようにする
- review loop は最大 2 pass。1 pass 目で `CRITICAL` / `HIGH` が出たら修正し、2 pass 目で再確認する。2 pass 目でも未解消なら issue 化を止め、ユーザーに判断を委ねる
- 残す `MEDIUM` / `LOW` は plan 本文の「受け入れ済みリスク」相当の記述に重大度・残す理由・後続対応条件を記録してから issue 化する

## Secret Check

plan 本文は GitHub issue に全文ミラーされるため、秘密情報の混入は public 公開に直結する。`.plan/` はローカル ignore されていても、検出時にファイルがディスクに残れば事故リスクは減らない。そのため以下の 2 点でチェックする。

- **pre-write** (Workflow step 7): 組み立て中の plan 本文をメモリ上で走査する。検出したらファイル書き出しを行わず停止し、ユーザーにマスキングを依頼する。検出された秘密情報はディスクに書き出さない
- **pre-issue** (Workflow step 10): レビュー pass で追記・修正された最終本文をもう一度走査する。検出時は `gh issue create/edit` を実行せず停止。`.plan/` のファイルは自動削除せず、ユーザーに対処 (masking / 再生成) を依頼する

検出パターン:

- ファイル名や path パターン: `.env*`, `*.pem`, `*.key`, `*credentials*`, `*.pfx` を参照する行
- 文字列パターン: `AKIA`, `sk-`, `password=`, `secret=`, `api_key=`, `token=`, `Bearer ` で始まる行
- ログやスタックトレースを貼り付けた場合に含まれがちな、社内ホスト名・ユーザー名・内部 URL

検出が不確かな場合も issue 化前にユーザーへ確認する。疑わしきは止める。

## GitHub Issue 作成とミラー

- 明示がない限り **新規計画・新規 issue** を作る。類似 open issue は自動探索しない（誤上書きリスクを避けるため）
- 手順:
  1. `gh auth status` で `gh` CLI の可用性と認証を同時に確認する。失敗したら原因を区別して報告する:
     - `command not found: gh` → `gh` CLI 未インストール。`.plan/` 出力までで停止し、インストールを依頼する
     - 認証エラー → 未認証。`.plan/` 出力までで停止し、`gh auth login` を依頼する
  2. `gh repo view --json nameWithOwner,defaultBranchRef,url` で GitHub 管理 repo を確認する。失敗時は stderr を見て非 GitHub repo / 権限不足 / ネットワーク失敗を区別する
  3. issue title は計画タイトルから作る（Conventional Commits 互換にしておくと後続 PR と揃う）
  4. 新規作成は常に `gh issue create --title "<title>" --body-file <plan-file>` で `.plan/` ファイルを直接渡す
  5. issue 作成後、返された URL を `.plan/` に追記し、`gh issue edit <number> --body-file <plan-file>` で再同期する
  6. 必要があれば issue body に Mermaid 図を含める（3 コンポーネント以上 → `flowchart`、時系列 → `sequenceDiagram`、状態遷移 → `stateDiagram`）

## 既存 issue 更新の例外

既存 issue の更新は **ユーザーが issue 番号または既存 issue 更新を明示した場合だけ** 扱う。

- 例: "この計画を issue #25 に反映して" / "既存の計画 issue を更新して" / `/km:plan 25`
- `gh issue view <number> --json number,title,body,url,state` で対象を確認する
- body に `<!-- km:plan:managed -->` marker があれば `.plan/` ファイルを直接 `gh issue edit <number> --body-file <plan-file>` で更新できる
- marker がない既存 issue は `km:plan` 管理外の可能性があるため、自動で全文置換しない。更新前にユーザーへ確認する
- **title 更新ポリシー**: 更新対象は原則 body のみ。計画タイトルが大きく変わり既存 issue title と齟齬が出る場合だけ、ユーザーに変更可否を確認してから `gh issue edit <number> --title <new-title>` を追加実行する。タイトル変更を自動判定しない

## Decision Rules

- 計画本文の章立ては固定せず、タスクの難しさに応じて必要な情報を過不足なく含める
- issue body にローカル `.plan/` への参照リンクを置かない（GitHub 読者は `.plan/` を読めないため）
- issue body は `.plan/` の **全文ミラー**。要約や抜粋ではなく、同じ markdown を渡す
- issue body 同期は `.plan/` ファイルをそのまま `--body-file` に渡す。別ファイルや heredoc の本文を組み立て直さない
- `--body "..."` を使わない
- 計画は作って終わりではなく、レビュー → 反映 → issue 化までが 1 単位
- 非 GitHub repo、`gh` 未インストール、`gh` 未認証のいずれでも `.plan/` 出力までで止め、原因を区別して報告する
- 計画生成スクリプトや `agents/openai.yaml` は追加しない（初回実装の非スコープ）

## Safety Rules

- Plan Mode 中は `.plan/`, `.gitignore`, GitHub issue を一切変更しない
- `.plan` 追跡済み、または既存 ignore ルールで除外済みの場合、`.gitignore` を自動編集しない
- 明示のない限り既存 issue を探索・再利用しない。類似 issue の自動 search は行わない
- 既存 issue を更新する場合でも、marker がなければ全文置換前にユーザーへ確認する
- `gh issue create/edit` が失敗した場合、成功扱いせず `URL 未同期` として報告する
- 2 pass レビューでも `CRITICAL` / `HIGH` が残る場合、issue 化を止めてユーザーに判断を委ねる
- PR 作成・ブランチ作成・push は `km:github-workflow` の責務。このスキルでは行わない
- 計画作成の意図が曖昧な場合は、書き込み前にユーザーへ確認する
