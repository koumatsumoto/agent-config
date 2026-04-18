---
name: km:github-workflow
description: Runs the GitHub PR delivery workflow with optional issue linkage. Use when the user says "PRにして", "issue化してからPRにして", or otherwise explicitly requests PR / issue / delivery completion.
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
- issue 要求がある場合だけ Phase 2 で issue を扱う
- issue 連携がある場合だけ PR 本文に `Closes #<num>` または `Refs #<num>` を入れる
- issue を計画として使うなら、PR 作成前までは計画更新をなるべく issue 本文に反映する
- PR 作成後は PR を実装成果物の正とし、issue の詳細同期を続けない
- PR URL、変更要約、見てほしい論点を共有する

## Trigger Signals

`PR` / `issue` / `delivery` の完了要求が明確なときだけ使う。単なる実装依頼では使わない。

- 例: `PRにして` / `issue化してからPRにして` / `/km:github-workflow 123`

## Entry Point

まず `gh auth status` で認証を確認する。失敗したら認証エラーとして停止する。
次に `gh repo view --json nameWithOwner,defaultBranchRef` を実行する。失敗したら stderr を見て、non-GitHub repo、権限不足、network 失敗を区別して停止する。

次に mode を決める:

1. `$ARGUMENTS` に issue 番号があれば `existing-issue` mode
2. ユーザー要求に issue 化シグナルがあれば `issue-first` mode
3. それ以外で PR / delivery シグナルが明確なら `standard-pr` mode
4. どれにも当てはまらなければ停止する

`issue-first` と `existing-issue` mode では、ブランチ状態にかかわらず Phase 2 を先に完了してから後続 phase に進む。

`standard-pr` mode、または issue 連携をすでに解決済みの状態では、現在状態から開始位置を決める:

|状態|開始位置|
|---|---|
|既定 base branch 上|Phase 1|
|作業ブランチ + 未コミット変更あり|Phase 3|
|作業ブランチ + 未 push コミットあり|Phase 3|
|push 済みで PR 未作成|Phase 4 の PR 作成|
|push 済みで既存 PR あり|Phase 4 の PR 更新|

無関係な未コミット変更や別件ブランチの疑いがあれば、先にユーザーへ確認する。

## Phase 1: ブランチ準備

1. 現在ブランチを確認する
2. base branch の明示指定は `<branch> から` または `base は <branch>` のように branch 名が直接示された場合だけ採用する
3. base branch 指定がなければ、Entry Point で取得した `defaultBranchRef` を既定 base branch とする
4. 明示された base branch が存在しない、指定が曖昧、または `defaultBranchRef` が取得できない場合は確認する
5. base branch 上にいるなら `type/short-description` 形式で新ブランチを切る
6. 既存作業ブランチなら、今回のタスク用かをブランチ名と最近のコミットで判断する
7. issue-first / existing-issue mode でも、ブランチ名に issue 番号は必須にしない

## Phase 2: Issue 連携

Issue 本文や PR 本文を書く前に `references/body-writing-principles.md` と `references/gh-body-file-rules.md` を読む。

### `issue-first` mode

1. 主キーワード 1-3 語で `gh issue list --state open --search ...` を実行する。結果が 10 件超または弱一致ばかりなら 1 回だけ絞り直す
2. 1 件一意なら再利用、0 件なら新規作成、2 件以上または曖昧なら作成せずユーザーに確認する
3. issue を計画として使うなら、再利用でも新規でも、計画更新は issue 本文に反映する。PR 作成前のみ補足や決定履歴を issue comment に残す
4. issue / PR 本文は `--body-file - <<'EOF'` で流し込む
5. 実装がまだ終わっていなければ、issue を用意した時点で一度止める。再開時は `/km:github-workflow <issue-number>` を使う

### `existing-issue` mode

1. 指定された issue 番号が open で存在することを確認する
2. 既定では issue 本文を編集しない
3. ユーザーが計画更新を明示要求した場合のみ、必要最小限の本文更新を行う
4. PR 作成前で、レビュー結果や修正完了報告を残したい場合だけ issue comment に追記する
5. PR 本文にはその issue 番号だけを連携対象として使う

### `standard-pr` mode

1. issue 連携は追加しない
2. 既存の issue を勝手に探索・作成しない

## Phase 3: レビューと修正

1. 実装後に `/km:review` を実行する
2. `CRITICAL` は勝手に修正せず、まず共有する
3. それ以外は原則対応するが、大規模修正や仕様変更は先に確認する
4. 修正後にもう一度 `/km:review` を行い、未解決の高重大度がないことを確認する。レビューは最大 2 回まで。2 回目でも `BLOCKED` が解消しない場合はユーザーに判断を委ねる

## Phase 4: 公開

1. `/km:commit` でコミットする
2. ブランチを push する
3. PR 本文を書く前に `references/pr-conventions.md` と `references/gh-body-file-rules.md` を読む
4. issue が 1 件に決まっている場合:
   - 単一 PR なら独立行で `Closes #<num>` を入れる
   - 複数 PR に分割する場合は、中間 PR では `Refs #<num>`、最終 PR だけ `Closes #<num>` を入れる
5. 既存 PR があれば更新し、なければ新規作成する
6. PR 作成・更新時は `--body "..."` を使わず、`--body-file - <<'EOF'` を使う
7. PR URL、変更要約、見てほしい論点を共有する

## Decision Rules

- まだ議論や追加修正が残るなら Draft PR を使う
- レビュー対応まで済んでいれば通常 PR を使う
- PR タイトルは Conventional Commits 形式に合わせる
- PR 説明は日本語で書く
- issue 本文・PR 本文の章立ては固定テンプレートに縛らず、タスクの難しさに応じて必要な情報を過不足なく含める
- issue が 1 件に定まらない状態で `Closes` を勝手に決めない
- issue を計画として使うなら、PR 作成前までは計画更新をなるべく issue 本文へ反映する
- PR を作成したら、以後の実装状態や詳細な差分は PR を正とする
- 明示 base branch 指定は新規ブランチ作成時だけに効かせ、既存作業ブランチの履歴を書き換える理由には使わない

## Safety Rules

- GitHub 管理リポジトリでない場合、または `gh` 認証・アクセスが不足している場合は何も変更せず停止する
- 認証変更、権限付与、remote 変更は勝手に行わない
- branch 作成 / push / PR 作成の要求が曖昧な場合は、workflow 開始前にユーザーへ確認する
- issue 作成の要求が曖昧な場合も、workflow 開始前にユーザーへ確認する
- `--body "..."` や非クォート heredoc で issue / PR 本文を流し込まない
- `--force` push はしない
- PR 作成が完了したら主体的な作業は止める
