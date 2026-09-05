---
name: km-github-workflow
description: GitHubリポジトリの変更をissue・PRとして提出し、明示された場合はマージまで完了する。「PRにして」などの依頼で使う
argument-hint: "[issue-number]"
---

# GitHub Workflow

GitHubリポジトリの変更について、issueの作成からPRの提出までを担う。ユーザーが明示した場合は、PRのマージと作業用worktreeの削除まで完了する。計画は`km-plan`、レビューは`km-review`、commitは`km-commit`へ委ねる。

## Workflow

`Plan` → `Setup` → `Implement` → `Review` → `Submit` → `Merge`（依頼された場合のみ）

### Plan

原則として変更ごとにissueを作り、PRと対応させる。論点が少ない場合は、目的と完了条件だけを記載する。複雑で、誤方向へ進んだ場合の手戻りが大きい場合は`km-plan`を使う。ユーザーがissueは不要だと明示した場合は省略する。

### Setup

- 変更に着手する前に、基点branchから作業branchと専用worktreeを作る。以降の作業は、そのworktree内で行う。基点branch側や別の作業用worktreeを作業場所にしない。
- branch名は`<type>/<issue番号>-<slug>`とする。issueがない場合は`<type>/<slug>`とする。
- 既存PRを更新する場合は、そのbranch専用のworktreeを使う。専用worktreeがなければ作成する。
- worktreeの作成直後、読み込んだこの `SKILL.md` の実在directoryを基準に `scripts/prepare-worktree.py` を解決し、利用可能なPython 3.9以上のinterpreterで、作成元worktree rootと新しいworktree rootを引数に渡す。skill directoryへ `cd` しない。正常終了（no-op / matchなしを含む）なら続行し、失敗した場合はそのworktreeで作業を始めず停止する。

### Implement

依頼された変更を専用worktreeで実装する。

### Review

完了条件、差分、テスト結果を確認した後、`km-review`を実行する。

### Submit

`km-commit`で変更をcommitし、作業branchをpushして、PRを作成または更新する。マージまで依頼されていない場合は、ここでPR URL、変更の要約、検証結果を報告する。

### Merge

ユーザーが現在の依頼でマージを求めた場合、または元の作業指示にマージまで含まれていた場合に限り、レビューを完了したPRをマージする。マージ完了を確認したら基点branch側のworktreeへ戻り、今回の作業に使った専用worktreeを削除する。

最後に、PR URL、変更の要約、検証結果、マージ結果を報告する。

## GitHub Contract

- すべての変更はPR経由で基点branchへ取り込む。基点branchへ直接commit、push、mergeしない。
- PR本文には、最終差分を理解するために必要な背景、主要な判断、検証結果だけを書く。内部タスクの情報、逐次の作業ログ、レビュー対応の履歴など、不要な経緯は残さない。
- `km-plan`が管理するissueに実装時確認事項がある場合は、各項目の確認結果または対応しない理由をPR本文に残す。
- issueを完了するPRには独立行で`Closes #N`を書く。複数PRに分ける場合、中間PRは`Refs #N`とする。
- CIの状態を確認し、未確認または失敗している場合は、その状態を報告する。

## Safety

- force pushしない。
- worktreeを作る前に、既存のworktree、branch、配置先を確認する。既存worktreeを削除したり、別の作業用branchを再利用したりしない。
- PRのマージ完了を確認するまで、作業用worktreeを削除しない。削除前に対象パスを特定し、未コミット変更がないことを確認する。削除に失敗した場合も強制削除しない。
- 無関係な未コミット変更をPRへ含めない。
- GitHub上のissueやPRに、秘密情報、非公開情報、個人環境を識別できる情報を載せない。
- issueとPRの本文は`--body-file`で渡す。`--body`やクォートなしのheredocは使わない。
