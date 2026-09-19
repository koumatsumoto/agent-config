# worktreeの準備

既存worktree・branch・配置先を確認し、基点branchから作業branchと専用worktreeを作る。既存worktreeを削除せず、別作業のbranchを再利用しない。
branch名は`<type>/<issue番号>-<slug>`、issueがなければ`<type>/<slug>`。既存PRを更新する場合は、そのbranchを使う。

作成直後に、`python3`、次に`python`で`-c 'import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)'`を実行し、最初に成功したinterpreterを使う。どちらも失敗したら停止する。
このスキルの`SKILL.md`がある実在directoryからhelperを解決し、そこへ`cd`せず、作成元と作成先のworktree rootを渡す。

```text
"<python>" "<skill-directory>/scripts/prepare-worktree.py" "<source-root>" "<destination-root>"
```

正常終了（no-op / matchなしを含む）なら実装へ進む。失敗したworktreeでは作業を始めない。
