---
name: km-github-workflow
description: GitHub管理リポジトリの変更の実装・PR提出に使う。issueから提出まで進め、明示された場合だけマージする。計画のみ・レビューのみ・コミットのみの依頼は対象外。
argument-hint: "[issue-number]"
---

# GitHub Workflow

## 準備

対応するissueがなければ作る。小さな変更のissueは目的と完了条件だけでよい。設計判断を先に固める必要があれば`km-plan`を使う。ユーザーがissue不要と明示した場合は省略する。

次のコマンドで専用branch・worktreeを用意し、必要なローカルファイルを引き継ぐ。`<skill-directory>`はこの`SKILL.md`のあるdirectory。新規branch名は`<type>/<issue番号>-<slug>`（issueなしなら`<type>/<slug>`）とする。

```text
bash "<skill-directory>/scripts/run-python.sh" "<skill-directory>/scripts/prepare-worktree.py" "<source-root>" "<destination-root>" --branch "<branch>"
```

作成元・作業先のパスと作業branch名を渡す。基点は作成元のHEAD（指定する場合は`--base <ref>`）、既存PRのbranchには`--existing`を付ける。成功時に表示されたworktreeで実装し、失敗したら停止する。

## 実装・レビュー

実装と検証を終えたら`km-review`を使い、判定に応じて進める。

- `PASS`：提出する
- `BLOCKED`：issueの範囲内でblockerを修正し、関連検証後に`km-review --recheck`で確認する。安全に修正できない、必要な検証ができない、またはユーザー判断が必要なら論点を報告して停止する
- `NOOP`：提出すべき変更がなければ終了する。対象の指定漏れなら指定を直してレビューする

non-blockingの解消だけを目的に反復しない。

## 提出

レビュー済みの変更を、一つの目的で説明・取り消せる単位でcommitする。作業branchをpushし、PRを作成または更新する。

- 本文には変更の背景・主要な判断・検証結果を書く。issueの`実装時確認事項`があれば、確認結果または対応しない理由も含める
- issueを完了するPRには独立行で`Closes #N`、中間PRには`Refs #N`を書く
- CIを確認し、PR URL・変更の要約・検証結果を報告する。未確認・失敗も明示する

現在または元の依頼にマージが含まれる場合だけマージする。完了確認後に基点branch側のworktreeへ戻り、今回のworktreeを削除して結果を報告する。削除前に対象パスと未コミット変更がないことを確認し、強制削除しない。

## GitHub操作の制約

- 基点branchへの取り込みはPR経由に限り、直接commit・push・mergeやforce pushをしない
- 無関係な変更を含めず、issue・PRに秘密情報、非公開情報、個人環境を識別できる情報を載せない
- issue・PR本文は一時ファイルから`--body-file`で渡す。`--body`とクォートなしheredocは使わない
