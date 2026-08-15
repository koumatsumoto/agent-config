---
name: km-github-workflow
description: GitHubリポジトリの変更をissue・ブランチ・コミット・PRまで届ける。「PRにして」などの依頼で使う
argument-hint: "[issue-number]"
---

# GitHub Workflow

GitHubリポジトリの変更をissueからPRまで届ける。計画は`km-plan`、レビューは`km-review`、コミットは`km-commit`へ委ねる。

## Workflow

1. **Issue**: 原則としてissueとPRを対応させる。論点が少なければ目的と完了条件だけのissueを作り、複雑で誤方向の手戻りが大きい場合は`km-plan`を使う。ユーザーがissue不要と明示した場合は省略する
2. **Branch**: 基点ブランチから作業ブランチを作る。基点ブランチへ直接コミット・pushしない。名前は`<type>/<issue番号>-<slug>`、issueがなければ`<type>/<slug>`とする
3. **Verify**: 完了条件・差分・テストを確認し、`km-review`を通す
4. **Deliver**: `km-commit`でコミットし、pushしてPRを作成または更新する
5. **Report**: PR URL、変更要約、検証結果を報告する

## GitHub Contract

- PR本文には最終差分を理解するために必要な背景・主要な判断・検証結果だけを書き、内部タスク情報、逐次の作業ログ、レビュー反映の往復履歴など不要な経緯を残さない
- `km-plan`管理issueに実装時確認事項がある場合は、各項目の確認結果または対応しない理由をPR本文に残す
- issueを完了するPRには独立行で`Closes #N`を書く。複数PRに分ける場合、中間PRは`Refs #N`とする
- CIを確認し、未確認または失敗があればその状態を報告する

## Safety

- force pushしない
- 無関係な未コミット変更をPRへ含めない
- issue / PRなどの公開面へ秘密情報、非公開情報、個人環境の識別情報を載せない
- issue / PR本文は`--body-file`で渡す。`--body`や非クォートのheredocは使わない
