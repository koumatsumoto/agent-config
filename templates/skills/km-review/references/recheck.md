# recheck

新しい全体レビューではない。直前の未解決blockerが解消したか、その修正が新しい重大な回帰を持ち込んでいないかだけを確認する。

直前のblockerとレビュー基準は、同一セッションの会話または`.km-review/<scope>/integration.md`から取得する。同じレビュー対象のrecheckでは同じscopeのintegration.mdを正本にする。対象と一致しない、またはblockerを特定できない場合は通常レビューに戻す。

1. メイン担当がblockerを修正し、関連検証を実行する
2. blockerの解消、修正箇所が変えた隣接契約、修正起因の回帰を確認する
3. 独立確認が必要なら、該当観点を1名、互いに代替できない二つのblocker群がある場合だけ2名使う
4. `references/verdict.md`に従って結果を更新する

独立レビュアを使う場合は `references/dispatch.md` に従う。
独立レビュアには対象blockerと修正内容を渡す。前回通過済みの領域、無関係な既存問題、新しいMEDIUM・LOWの探索へ広げない。
既存のfindingは保持し、解消したblockerを`resolved`へ更新し、新規findingだけを追加する。
SKILL.mdのsecurity必須割り当てはrecheckでも維持する。

未解決blockerがなくなれば `PASS`。解消しない場合やユーザー判断が必要な場合は `BLOCKED` のまま、論点と最小の選択肢を示す。
修正で外部観測面または文書が変わった場合は、PASS前に `references/doc-review.md` を実施する。
