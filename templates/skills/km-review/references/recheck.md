# recheck

対象を編集せず、直前の未解決blockerの解消と、修正による重大な回帰だけを確認する。新しい全体レビューはしない。
blockerとレビュー基準は同一セッションの会話か、直前の一時ディレクトリの`integration.md`から取得する。対象不一致、blockerを特定できない、またはセッションをまたいで一時ファイルが使えない場合は通常レビューへ戻す。

1. 現在の対象とblockerを照合し、対象を編集しない関連検証を実行する。
2. blockerの解消、修正で変わった隣接契約、修正起因の重大な回帰を確認する。
3. 独立確認が必要なら該当観点を1名使い、互いに代替できない二つのblocker群がある場合だけ2名使う。SKILL.mdのsecurity必須割り当ては維持する。
4. `references/verdict.md`に従い、既存findingを保持する。解消を確認したblockerだけ`resolved`へ更新し、未解消は`unresolved`のまま、新規findingだけ追加する。

独立レビュアの起動は`references/dispatch.md`に従い、対象blockerと修正内容を渡す。前回通過した領域、無関係な既存問題、新しいMEDIUM・LOWの探索へ広げない。
外部観測面または文書が修正で変わった場合は、PASS前に`references/doc-review.md`を実施する。
必要なレビュー・検証が完了し、未解決blockerがなければ`PASS`。未解消、検証未完了、重大な不確実性、またはユーザー判断が必要なら`BLOCKED`とし、論点と最小の選択肢を示す。
