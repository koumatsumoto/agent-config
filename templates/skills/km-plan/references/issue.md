# GitHub issueへの反映

新しいplan artifactは必ず`plan-artifact.py init`から開始する。helperが先頭へ配置する`<!-- km:plan:managed -->`は、このSkillが管理するissue本文であることを示す。公開前に`plan-artifact.py validate`を通し、validate済みの同じfileをそのまま`--body-file`で反映する。
既存issueの更新が明示されていなければ新規作成し、計画内容からタイトルを付ける。

更新を明示された既存issueは、次の条件で扱う。

- マーカーがあれば全文を更新してよい
- マーカーがなければ、全文置換の前にユーザーへ確認する
- 内容と合わなくなったタイトルは必要に応じて更新する

既存issueのmanaged / unmanaged判定はissue本文を見て行い、unmanaged issueの全文置換可否をhelperへ判断させない。
作成・更新のどちらも、validate済みfileとissue本文を一致させる。GitHubへ反映できなければ一時ファイルまでで止め、反映できなかったことを報告する。
