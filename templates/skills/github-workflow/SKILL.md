---
name: km:github-workflow
description: Reference and orchestrate the GitHub PR delivery workflow. Consult for branch, commit, PR, issue linkage, follow-up issue, and completion-report rules; use directly when the user clearly wants to finish with a PR.
argument-hint: "[issue-number]"
---

# GitHub Workflow

GitHub 管理リポジトリで、branch / commit / PR / issue 連携 / 完了報告まで進めるための運用ルールを定義する。`CLAUDE.md` / `AGENTS.md` には workflow の概要だけを置き、詳細な実行判断は本スキルを参照する。

実装計画を issue 本文として管理する責務は `km:plan`、未コミット変更のレビュー責務は `km:review`。本スキルはそれらを重複実装せず、GitHub delivery の実行順序、follow-up issue、作業方法改善メモ、PR 公開を扱う。

## Context

- Branch: !`git branch --show-current`
- Status: !`git status --short`
- Upstream: !`git rev-parse --abbrev-ref @{u} 2>/dev/null || echo "(none)"`
- Unpushed: !`git log --oneline @{u}..HEAD 2>/dev/null`
- Remote: !`git remote -v 2>/dev/null | head -1`

## Success Criteria

- GitHub 管理リポジトリであることを確認してから進める
- issue 要求がある場合だけ issue 連携を扱う
- issue 連携がある場合だけ PR 本文に `Closes #<num>` または `Refs #<num>` を入れる
- 計画を issue 本文として管理する作業は `km:plan` に委ねる。本スキルでは plan 本文を書かない・更新しない
- レビューは `km:review` に委ねる。本スキルでレビュー観点や指摘判定を直接行わない
- PR 作成後は PR を実装成果物の正とし、issue の詳細同期を続けない
- 現 PR スコープ外の改善点を見つけたら、現作業に混ぜず GitHub issue 化または既存 issue 参照を行う
- 作業方法の改善点を見つけたら `.plan/` 配下の作業メモへ追記し、完了報告で共有する
- PR URL、変更要約、見てほしい論点、作業方法の改善点を共有する

## Reference Timing

GitHub 管理リポジトリで作業し、最終的に branch / commit / PR / issue 連携 / 完了報告へ進む場合は参照する。直接実行するのは、`PR` / `delivery` の完了要求が明確なときに限る。

- 直接実行する例: `PRにして` / `最後はPRにする` / `/km:github-workflow 123` / `このバグの issue を起こして PR まで`
- 参照する例: 通常実装後に branch / commit / PR / follow-up issue / 完了報告のルールを確認する
- 直接扱わない例: 単独の `issue にして` / `計画を issue にして` / `Issueで計画して` は `km:plan` に委ねる
- 計画 + PR delivery が同時に依頼された場合は、まず `km:plan` で issue 番号を確定させ、その issue 番号を使って本スキルを参照する
- 単独の「レビューして」は `km:review` に委ねる

## Entry Point

1. `gh auth status` で認証を確認する。失敗したら認証エラーとして停止する
2. `gh repo view --json nameWithOwner,defaultBranchRef` で GitHub 管理 repo を確認する。失敗したら non-GitHub repo、権限不足、network 失敗を区別して停止する
3. `$ARGUMENTS` に issue 番号があれば `existing-issue` mode とする
4. ユーザー要求が PR delivery と一体の ad-hoc issue 作成なら `issue-first` mode とする
5. issue 連携なしで PR / delivery シグナルが明確なら `standard-pr` mode とする
6. 単独の issue 作成・計画 issue 化・レビュー依頼は本スキルで直接扱わず、該当 skill を案内して停止する

現在状態から開始位置を決める:

| 状態 | 開始位置 |
| --- | --- |
| 既定 base branch 上 | Phase 1 |
| 作業ブランチ + 未コミット変更あり | Phase 3 |
| 作業ブランチ + 未 push コミットあり | Phase 5 |
| push 済みで PR 未作成 | Phase 5 |
| push 済みで既存 PR あり | Phase 5 |

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

Issue 本文や PR 本文を書く前に `references/body-writing-principles.md` と `references/gh-body-file-rules.md` を読む。本フェーズでは計画 issue の作成・本文更新は扱わない。計画 issue が必要な場合は `km:plan` に委ね、issue 番号が確定してから本スキルに戻る。

### `issue-first` mode

PR delivery と一体の ad-hoc issue 作成だけを扱う。

1. ユーザー要求が計画 issue の作成、または PR delivery を伴わない単独の issue 作成の場合は、ここで停止して `km:plan` の利用を案内する
2. 主キーワード 1-3 語で `gh issue list --state open --search ...` を実行する。結果が 10 件超または弱一致ばかりなら 1 回だけ絞り直す
3. 1 件一意なら再利用、0 件なら新規作成、2 件以上または曖昧なら作成せずユーザーに確認する
4. issue 本文には現状の問題・影響・想定対応を最低限書く。計画レベルの詳細・レビュー履歴を書かない
5. issue / PR 本文は `--body-file - <<'EOF'` で流し込む
6. 実装がまだ終わっていなければ、issue を用意した時点で一度止める。再開時は `/km:github-workflow <issue-number>` を参照する

### `existing-issue` mode

1. 指定された issue 番号が open で存在することを確認する
2. issue 本文は本スキルでは編集しない。本文の更新が必要な場合は `km:plan` に委ねる
3. PR 作成前で実装上の補足を残したい場合だけ issue comment に短く追記する。レビュー結果は `km:review` のレポートで扱うため issue comment へ書き写さない
4. PR 本文にはその issue 番号だけを連携対象として使う

### `standard-pr` mode

1. issue 連携は追加しない
2. 既存の issue を勝手に探索・作成しない

## Phase 3: レビューと修正

レビュー観点・指摘判定・重大度の運用は `km:review` の責務。本フェーズでは `km:review` の結果を受けて修正のオーケストレーションだけを担う。

1. 実装後に `/km:review` を実行する
2. `CRITICAL` は勝手に修正せず、まず共有する
3. それ以外は原則対応するが、大規模修正や仕様変更は先に確認する
4. 修正後にもう一度 `/km:review` を行い、未解決の高重大度がないことを確認する。レビューは最大 2 回まで。2 回目でも `BLOCKED` が解消しない場合はユーザーに判断を委ねる

## Phase 4: 作業方法改善メモ

作業中に、今回の実装成果物そのものではなく作業実施に関する改善点を見つけた場合は、`.plan/` 配下の作業メモへ随時追記する。

1. 対象は、計画の立て方、確認方法、レビュー手順、ツール運用、分岐判断、ユーザーへの確認方法とする
2. 作業メモはローカル一時作業場であり、issue / PR の source of truth にしない
3. 完了報告では、成果物の報告とは別に作業方法の改善点を簡潔に共有する

## Phase 5: 公開

1. `/km:commit` でコミットする
2. ブランチを push する
3. PR 本文を書く前に `references/pr-conventions.md` と `references/gh-body-file-rules.md` を読む
4. issue が 1 件に決まっている場合:
   - 単一 PR なら独立行で `Closes #<num>` を入れる
   - 複数 PR に分割する場合は、中間 PR では `Refs #<num>`、最終 PR だけ `Closes #<num>` を入れる
5. 既存 PR があれば更新し、なければ新規作成する
6. PR 作成・更新時は `--body "..."` を使わず、`--body-file - <<'EOF'` を使う
7. PR URL、変更要約、見てほしい論点、作業方法の改善点を共有する

## Out-of-Scope Findings

作業中に現 PR のスコープ外の改善点・設計課題・未解決問題を見つけた場合は、現作業に混ぜず follow-up issue として分離する。後回しにすると忘却するか、現 PR の diff に混入して scope が崩れる。

1. 発見したタイミングで、主キーワード 1-3 語で既存 open issue を軽く確認する。明らかな既存 issue があれば新規作成せず参照する
2. 新規に残す価値がある場合は `gh issue create --body-file - <<'EOF' ...` で起票する
3. 起票対象は、現作業に混ぜると scope が崩れ、問題・影響・想定対応を書けるものに限る。機能改善、リファクタリング、修正、設計課題、運用課題を含む
4. issue body には最低限「問題 / 影響 / 想定対応案（TBD でよい）/ 優先度」を記録する。発見の文脈（どの PR/ファイル/行で見つけたか）も簡潔に残す
5. 現 PR の diff には含めない。別 PR / 別作業で対応する
6. コード箇所にマーカーを残す場合は `FIXME(issue #N)` 形式で該当 issue 番号を入れる。git grep で追跡可能にする
7. リポジトリ内に `backlog.md` などの追跡ファイルを作らない。改善バックログは GitHub issue で一元管理する
8. 起票後または既存 issue 参照後は issue URL をユーザーに共有し、現 PR の作業に戻る

## Decision Rules

- まだ議論や追加修正が残るなら Draft PR を使う
- レビュー対応まで済んでいれば通常 PR を使う
- PR タイトルは Conventional Commits 形式に合わせる
- PR 説明は日本語で書く
- issue 本文・PR 本文の章立ては固定テンプレートに縛らず、タスクの難しさに応じて必要な情報を過不足なく含める
- issue が 1 件に定まらない状態で `Closes` を勝手に決めない
- 計画 issue の本文管理は `km:plan` に委ね、本スキルでは PR 本文と ad-hoc issue 本文だけ書く
- レビュー指摘の検出・重大度判定は `km:review` に委ね、本スキルでは結果を受けて修正のオーケストレーションだけ行う
- `.plan/` はローカル一時作業場。共有される成果物（PR 本文・issue 本文・commit message・PR/issue comments）から `.plan/` 配下の具体的なファイルを source of truth として参照させない。`.plan/` という機能や概念に触れる必要があれば書いてよい。共有用の正本は GitHub issue / PR の URL に集約する
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
