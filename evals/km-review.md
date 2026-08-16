# km-review 評価シナリオ集

挙動を変えたときに何を測り直すかの対応表と、その題材。実行時には読まない。

## 再走トリガ

| 触った箇所 | 再走する題材 |
| --- | --- |
| description | trigger-pairs |
| 対象 / `--repo` / `--recheck` | target-modes / blocker-only-recheck |
| メインレビュー | main-fixes-first / behavior-asset / doc-sync |
| 人数・観点・security経路 | minor-main-only / one-reviewer / two-reviewers / security-route / lens-routing |
| severity / blocking / status / 判定 | severity-blocking / blocker-convergence |
| dispatch / レポート | dispatch-isolation / integration-only |

## 題材と合否線

- **trigger-pairs** — should:「この変更をレビューして」「セキュリティ観点で確認して」「typoを直したのでレビューして」/ should-not:「実装が終わったのでPRにして」（`km-github-workflow`）「skillの変更効果を実シナリオで評価して」（`km-skill-eval`）
- **target-modes** — 未コミット差分、明示されたPR・commit範囲、`--repo <subtree>`、対象なしを並べる。`--repo`では未変更行と既存問題も対象にし、対象なしは`NOOP`
- **minor-main-only** — 局所的で容易に戻せ、直接検証できる差分。`km-review`は実行し、メイン担当が反証・検証したうえで独立レビュア0名、`PASS`
- **main-fixes-first** — 書き込み可能な差分に明確なHIGHを1件含める。メイン担当が独立レビュー前に修正・再検証し、`resolved`として最終報告へ残す。修正後に重要な残存リスクがなければ0名
- **one-reviewer** — メインレビュー後にも判定を変えうる重要な残存リスクが一つの観点に集約できる。対応する1名だけを選ぶ
- **two-reviewers** — 異なる二観点に重大な残存リスクが具体化し、片方では代替できない難しい変更。理由を観点ごとに残し、2名だけを並列起動する。大規模・重要というラベルだけで2名にしない
- **security-route** — (a) securityに関する語を含むが信頼境界・攻撃面を変えない変更ではカテゴリだけでsecurityを選ばない。(b) 信頼境界または攻撃面を実質的に変える場合は、選択する1〜2名にsecurityを含める
- **lens-routing** — 責務境界・成果・実挙動・攻撃面のいずれかへ主要リスクが明確に寄る題材で、`architect` / `product` / `reliability` / `security`から対応する観点を選ぶ
- **behavior-asset** — 新しい副経路が本経路のgateを継承せず、referenceや下流skillとの契約もずれる変更。挙動資産を文章校正として扱わずcode-equivalentとして反証し、silent dropと不要なcontext増大を捕捉する
- **doc-sync** — 公開フラグまたは既定値を変更し、READMEとhelpに旧記述を残す。最終候補で関連文書を同期し、一般的な文章改善へ広げない
- **severity-blocking** — CRITICAL / HIGH / MEDIUM / LOWを各1件含む。severityを影響度として付け、CRITICAL/HIGHを原則blocker、MEDIUM/LOWを原則non-blockingとする。完了条件を満たせないMEDIUMだけはblockerにできる。真偽未確定はseverityを付けず確認推奨
- **blocker-convergence** — 未解決blocker1件とnon-blocking2件。blockerだけを修正して関連検証を行い、non-blockingをゼロにするために再レビューせず`PASS`
- **blocker-only-recheck** — `integration.md`の未解決blockerと修正差分を使い、解消・隣接契約・修正起因の回帰だけを見る。対象を特定できなければ通常レビューへ戻す
- **dispatch-isolation** — subagentへ最終候補、レビュー基準、共通契約、選択roleだけを渡す。メイン所見、暫定判定、他role・他レビュア結果を渡さない。2名は独立に並列起動する
- **integration-only** — role別レポートや完了マーカーを作らず、統合結果だけを`.km-review/<scope>/integration.md`へ残す

## 題材構築の落とし穴

- 対象差分は適用可能なpatchまたは実在するgit差分にする
- routing評価では、期待する観点以外の本物のblockerを混ぜない
- 独立レビュアを利用できず必要なリスクを解消できない場合は`BLOCKED`
