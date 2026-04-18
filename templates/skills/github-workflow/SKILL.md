---
name: km:github-workflow
description: Runs the GitHub delivery workflow for a GitHub-managed repository, including optional issue linkage before branch-review-commit-push-PR. Use when the user says "PRにして", "PR作って", "PRまでやって", "issue化してからPR", or otherwise clearly asks for GitHub delivery.
argument-hint: "[issue-number]"
---

# GitHub Workflow

GitHub 管理リポジトリで、issue 連携を含む delivery workflow を完了する。

## Context

- Branch: !`git branch --show-current`
- Status: !`git status --short`
- Upstream: !`git rev-parse --abbrev-ref @{u} 2>/dev/null || echo "(none)"`
- Unpushed: !`git log --oneline @{u}..HEAD 2>/dev/null`
- Remote: !`git remote -v 2>/dev/null | head -1`

## Success Criteria

- GitHub 管理リポジトリであることを確認してから進める
- issue 要求がある場合は open issue を再利用または新規作成してから PR に進む
- `[issue-number]` 指定時は issue 本文を編集せず、PR 側の連携だけを行う
- base branch 名が明示されていればそこから作業ブランチを切り、未指定なら `main` を優先して既定 base を決める
- 今回の作業に対応するブランチで作業する
- レビュー結果を反映してからコミットする
- issue 連携がある場合、PR 本文の末尾に `Closes #<num>` または `Refs #<num>` を入れる
- issue / PR 本文は `--body-file` で安全に流し込む
- issue を計画の SSOT として使う場合、レビュー結果や計画修正は issue comment に残す
- push と PR 作成まで完了し、URL と論点を共有する

## Trigger Signals

この skill は GitHub delivery 意図が明確な発話でのみ使う。代表例:

- `PRにして`
- `PR作って`
- `PRまでやって`
- `このブランチをPRまで更新して`
- `issue化してからPRにして`
- `issue付きでPRまでやって`
- `/km:github-workflow 123`

以下では開始しない:

- `この機能を実装して`
- `この変更を直して`
- PR / issue / delivery が明示されていない一般的な実装依頼

## Entry Point

まず `gh repo view --json nameWithOwner` を実行し、失敗したら GitHub 管理リポジトリではないものとして停止する。

次に mode を決める:

1. `$ARGUMENTS` に issue 番号があれば `existing-issue` mode
2. ユーザー要求に issue 化シグナルがあれば `issue-first` mode
3. それ以外で PR / delivery シグナルが明確なら `standard-pr` mode
4. どれにも当てはまらなければ停止する

`issue-first` と `existing-issue` mode では、ブランチ状態にかかわらず Phase 2 を先に完了してから後続 phase に進む。

`standard-pr` mode、または issue 連携をすでに解決済みの状態では、現在状態から開始位置を決める:

|状態|開始位置|
|---|---|
|`main` / `master` 上|Phase 1|
|作業ブランチ + 未コミット変更あり|Phase 3|
|作業ブランチ + 未 push コミットあり|Phase 3|
|push 済みで PR 未作成|Phase 4 の PR 作成|
|push 済みで既存 PR あり|Phase 4 の PR 更新|

無関係な未コミット変更や別件ブランチの疑いがあれば、先にユーザーへ確認する。

## Phase 1: ブランチ準備

1. 現在ブランチを確認する
2. ユーザー要求に base branch 名が明示されていれば、新規ブランチを切るときの作業開始元としてその branch を使う
3. base branch 指定がなければ、`main` があれば `main`、なければ `master` を既定 base branch とする
4. 明示された base branch が存在しない、または `main` / `master` のどちらも判断できない場合は確認する
5. base branch 上にいるなら `type/short-description` 形式で新ブランチを切る
6. 既存作業ブランチなら、今回のタスク用かをブランチ名と最近のコミットで判断する
7. issue-first / existing-issue mode でも、ブランチ名は既存ルールを維持し、issue 番号の埋め込みを必須にしない

## Phase 2: Issue 連携

Issue 本文や PR 本文を書く前に `references/body-writing-principles.md` と `references/gh-body-file-rules.md` を読む。

### `issue-first` mode

1. タスク内容から検索語を決め、`gh issue list --state open --search ...` で open issue を確認する
2. 強く一致する候補が 1 件なら再利用する
3. 候補が 2 件以上なら新規作成せず、どれを使うべきかユーザーに確認する
4. 候補が 0 件なら新規 issue を作成する
5. issue 作成・更新時は `--body "..."` を使わず、原則 `--body-file - <<'EOF'` を使う
6. issue を計画の SSOT として使う場合、後続の計画レビュー結果、修正方針、修正完了報告は issue comment に残す
7. まだ実装が終わっていなければ、issue を用意したあと通常の実装に戻り、コード差分ができてから次の phase に進む

### `existing-issue` mode

1. 指定された issue 番号が open で存在することを確認する
2. issue 本文は編集しない
3. 計画レビュー結果や修正完了報告が必要なら issue comment に追記する
4. PR 本文にはその issue 番号だけを連携対象として使う

### `standard-pr` mode

1. issue 連携は追加しない
2. 既存の issue を勝手に探索・作成しない

## Phase 3: レビューと修正

4. 実装後に `/km:review` を実行する
5. `CRITICAL` は勝手に修正せず、まず共有する
6. それ以外は原則対応するが、大規模修正や仕様変更は先に確認する
7. 修正後にもう一度 `/km:review` を行い、未解決の高重大度がないことを確認する。レビューは最大 2 回まで。2 回目でも `BLOCKED` が解消しない場合はユーザーに判断を委ねる

## Phase 4: 公開

8. `/km:commit` でコミットする
9. ブランチを push する
10. PR 本文を書く前に `references/pr-conventions.md` と `references/gh-body-file-rules.md` を読む
11. issue が 1 件に決まっている場合:
    - 単一 PR なら PR 本文末尾に独立行で `Closes #<num>` を入れる
    - 複数 PR に分割する場合は、中間 PR では `Refs #<num>`、最終 PR だけ `Closes #<num>` を入れる
12. 既存 PR があれば、最新の変更内容に合わせてタイトルと説明を更新する。なければ GitHub で PR を新規作成する
13. PR 作成・更新時は `--body "..."` を使わず、原則 `--body-file - <<'EOF'` を使う
14. PR URL、変更要約、見てほしい論点を共有する

## Decision Rules

- まだ議論や追加修正が残るなら Draft PR を使う
- レビュー対応まで済んでいれば通常 PR を使う
- PR タイトルは Conventional Commits 形式に合わせる
- PR 説明は日本語で書く
- issue 本文・PR 本文の章立ては固定テンプレートに縛らず、タスクの難しさに応じて必要な情報を過不足なく含める
- issue が 1 件に定まらない状態で `Closes` を勝手に決めない
- issue 本文を SSOT にした場合でも、レビュー履歴や修正履歴は comment で残し、本文で履歴を消さない
- 明示 base branch 指定は新規ブランチ作成時だけに効かせ、既存作業ブランチの履歴を書き換える理由には使わない

## Safety Rules

- GitHub 管理リポジトリでない場合は何も変更せず停止する
- 認証変更、権限付与、remote 変更は勝手に行わない
- branch 作成 / push / PR 作成の要求が曖昧な場合は、workflow 開始前にユーザーへ確認する
- issue 作成の要求が曖昧な場合も、workflow 開始前にユーザーへ確認する
- `--body "..."` や非クォート heredoc で issue / PR 本文を流し込まない
- `[issue-number]` mode では issue 本文を更新しない
- `--force` push はしない
- PR 作成が完了したら主体的な作業は止める
