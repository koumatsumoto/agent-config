# 独立レビュアの起動

メインレビューと対象を変更しない検証を終えた同じ候補に対し、観点ごとに独立したsubagentを使う。2名は互いの結果を渡さず並列実行する。

次を渡す。契約はpathだけでなく内容そのものを渡し、subagentへ探索させない。

- 変更範囲・対象パス。差分の本文はsubagent自身が取得できない場合だけ渡す
- ユーザー指示・issueで確定した目的、完了条件、対象範囲
- `references/finding-contract.md`、`reviewers/contract.md`、選んだ`reviewers/<role>.md`の内容
- 挙動資産なら`reviewers/behavior-asset.md`の内容

メイン担当の所見・修正理由・暫定判定・選択理由、他レビュアの結果は渡さない。`--recheck`では対象blockerと修正内容を渡してよい。
メイン担当が結果を直接回収し、`references/verdict.md`で統合する。role別報告ファイル・完了マーカーは作らない。
必要なレビュアを実行できなければ`BLOCKED`とし、SKILL.mdのsecurity必須割り当てをメインレビューで代替しない。
