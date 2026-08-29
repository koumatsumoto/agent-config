---
name: km-github-workflow
description: GitHubリポジトリの変更をissue・worktree・commit・PRまで届ける。「PRにして」などの依頼で使う
argument-hint: "[issue-number]"
---

# GitHub Workflow

GitHubリポジトリの変更をissueからPRまで届ける。計画は`km-plan`、レビューは`km-review`、コミットは`km-commit`へ委ねる。

## Workflow

1. **Issue**: 原則としてissueとPRを対応させる。論点が少なければ目的と完了条件だけのissueを作り、複雑で誤方向の手戻りが大きい場合は`km-plan`を使う。ユーザーがissue不要と明示した場合は省略する
2. **Worktree**: 変更前に基点ブランチから作業ブランチと専用worktreeを作り、編集・検証・コミットはそのworktree内で行う。既存PRの更新では、そのブランチ専用のworktreeを使い、なければ作成する。基点ブランチ側や別作業のworktreeを作業場所にしない。ブランチ名は`<type>/<issue番号>-<slug>`、issueがなければ`<type>/<slug>`とする
3. **Bootstrap**: 専用worktreeの作成直後、新しいworktreeのrepository rootにtracked `.worktreeinclude`があれば、記載されたignored pathまたは`.gitignore`形式のpatternに一致する作成元worktreeのignored fileを、同じ相対pathへコピーする。`.worktreeinclude`がなければ何もしない
4. **Verify**: 完了条件・差分・テストを確認し、`km-review`を通す
5. **Deliver**: `km-commit`でコミットし、pushしてPRを作成または更新する
6. **Report**: PR URL、変更要約、検証結果を報告する

## GitHub Contract

- すべての変更はPR経由で基点ブランチへ取り込む。基点ブランチへ直接コミット・push・mergeしない
- PR本文には最終差分を理解するために必要な背景・主要な判断・検証結果だけを書き、内部タスク情報、逐次の作業ログ、レビュー反映の往復履歴など不要な経緯を残さない
- `km-plan`管理issueに実装時確認事項がある場合は、各項目の確認結果または対応しない理由をPR本文に残す
- issueを完了するPRには独立行で`Closes #N`を書く。複数PRに分ける場合、中間PRは`Refs #N`とする
- CIを確認し、未確認または失敗があればその状態を報告する

## Safety

- force pushしない
- worktree作成前に既存のworktree・ブランチ・配置先を確認し、既存worktreeの削除や別作業のブランチの再利用をしない
- `.worktreeinclude`からコピーするのはGitにignoredされたfileだけとし、tracked file、repository外を指すpath、source symlink、既存destinationは対象にしない。内容をlogへ出さず、コピーしたfileをstageしない
- `.worktreeinclude`のpatternが何にも一致しない場合は正常とする。対象を確定した後のcopyに失敗した場合は、不完全なworktreeで作業を続けず停止する
- 無関係な未コミット変更をPRへ含めない
- issue / PRなどの公開面へ秘密情報、非公開情報、個人環境の識別情報を載せない
- issue / PR本文は`--body-file`で渡す。`--body`や非クォートのheredocは使わない
