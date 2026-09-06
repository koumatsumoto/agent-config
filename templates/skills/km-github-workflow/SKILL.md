---
name: km-github-workflow
description: GitHubリポジトリの変更をissue・PRとして提出する。「PRにして」などの依頼で使い、明示された場合だけマージまで行う。
argument-hint: "[issue-number]"
---

# GitHub Workflow

issueからPR提出までを管理する。計画は`km-plan`、読み取り専用レビューは`km-review`、commitは`km-commit`へ委ねる。レビュー後の修正・再確認はこのスキルが管理する。

## Issueと作業場所

- 変更ごとにissueを作り、PRと対応させる。論点が少なければ目的と完了条件だけでよい。複雑で誤方向の手戻りが大きい場合は`km-plan`を使う。ユーザーがissue不要と明示した場合は省略する。
- 着手前に既存worktree・branch・配置先を確認し、基点branchから作業branchと専用worktreeを作る。既存worktreeを削除せず、別作業のbranchを再利用しない。
- branch名は`<type>/<issue番号>-<slug>`、issueがなければ`<type>/<slug>`。既存PRの更新にはそのbranch専用のworktreeを使い、なければ作成する。
- 実装は専用worktree内だけで行う。基点branch側や別作業のworktreeを使わない。

### worktreeの準備

作成直後に、`python3`、次に`python`で`-c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)'`を実行し、最初に成功したinterpreterを使う。どちらも失敗したら停止する。
読み込んだ`SKILL.md`の実在directoryからhelperを解決し、そこへ`cd`せず、作成元と作成先のworktree rootを渡す。

```text
"<python>" "<skill-directory>/scripts/prepare-worktree.py" "<source-root>" "<destination-root>"
```

正常終了（no-op / matchなしを含む）なら実装へ進む。失敗したworktreeでは作業を始めない。

## 実装・検証・レビュー

依頼範囲を実装し、完了条件・差分・テスト結果を確認して`km-review`を実行する。判定を受け取った時点でレビュー工程を終える。

- `PASS`：提出へ進む。
- `BLOCKED`：issueの範囲内で未解決blockerを最小限修正し、関連検証を実行して`km-review --recheck`で再確認する。
- `NOOP`：対象と完了条件を照合する。提出すべき変更がなければ終了し、対象の指定漏れなら指定を直してレビューする。

MEDIUM・LOWのnon-blockingをゼロにするために反復しない。既存の権限・要件内で安全に解消できない、必要な検証ができない、またはユーザー判断が必要な場合は`BLOCKED`として論点を報告して停止する。

## 提出・マージ

`km-commit`でcommitし、作業branchをpushしてPRを作成または更新する。CIを確認し、未確認・失敗もそのまま報告する。
現在の依頼または元の作業指示にマージが含まれる場合だけ、レビューを完了したPRをマージする。完了を確認してから基点branch側のworktreeへ戻り、今回の専用worktreeを削除する。削除前にパスと未コミット変更がないことを確認し、失敗しても強制削除しない。
最後にPR URL、変更の要約、検証結果、マージした場合はその結果を報告する。マージ依頼がなければPR提出で終える。

## GitHubへの反映

- 基点branchへの取り込みはPR経由に限る。基点branchへ直接commit・push・mergeせず、force pushもしない。
- PR本文には最終差分の背景・主要な判断・検証結果だけを書く。内部タスク、逐次ログ、レビュー対応履歴は残さない。
- `km-plan`管理issueの`実装時確認事項`があれば、各項目の確認結果または対応しない理由をPR本文へ書く。
- issueを完了するPRには独立行で`Closes #N`を書く。中間PRは`Refs #N`とする。
- 無関係な未コミット変更を含めず、issue・PRに秘密情報、非公開情報、個人環境を識別できる情報を載せない。
- issue・PR本文は`--body-file`で渡す。`--body`とクォートなしheredocは使わない。
