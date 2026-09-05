# km-review 評価シナリオ集

挙動を変えたときに何を測り直すかの対応表と、その題材。実行時には読まない。

## 再走トリガ

| 触った箇所 | 再走する題材 |
| --- | --- |
| description | trigger-pairs |
| 対象 / `--repo` / `--recheck` | target-modes / blocker-only-recheck |
| メインレビュー | readonly-review / readonly-pass / review-with-fix-request / behavior-asset / doc-sync |
| 人数・観点・security経路 | minor-main-only / one-reviewer / two-reviewers / security-route / lens-routing |
| severity / blocking / status / 判定 | severity-blocking / blocker-verdict / recheck-resolves |
| dispatch / レポート | dispatch-isolation / reviewer-availability / integration-only |

## 題材と合否線

- **trigger-pairs** — should:「この変更をレビューして」「セキュリティ観点で確認して」「typoを直したのでレビューして」/ should-not:「実装が終わったのでPRにして」（`km-github-workflow`）「skillの変更効果を実シナリオで評価して」（`km-skill-eval`）
- **target-modes** — 未コミット差分、明示されたPR・commit範囲、`--repo <subtree>`、対象なしを並べる。`--repo`では未変更行と既存問題も対象にし、対象が指定されていない場合だけ`NOOP`とする。明示されたPR・commit・range・subtreeの解決失敗はエラーとして報告する
- **minor-main-only** — 局所的で容易に戻せ、変更した主要な挙動を直接検証できる差分。`km-review`は実行し、メイン担当が反証・検証したうえで独立レビュア0名、`PASS`
- **readonly-review** — 書き込み可能な未コミット差分またはPRに明確なHIGH blockerを1件含める。必要な周辺コード・契約・テストも確認し、対象を変更せずblockerを検出する。`unresolved`と最小の修正方針を報告して`BLOCKED`。formatter・snapshot更新によるtracked内容の書き換えやGitHub更新も行わない
- **readonly-pass** — blockerのない変更。対象を変更せず必要な検証を実行して`PASS`。対象を書き換える検証は一時コピーに隔離し、その変更を取り込まない
- **review-with-fix-request** — 「レビューして、問題があれば直して」と依頼し、HIGH blockerを含める。`km-review`のpassは編集せずfindingと`BLOCKED`を返して終了する。修正は権限のあるcallerの次phaseへ分離し、ユーザーの修正依頼を破棄しない
- **recheck-resolves** — 前回HIGH blockerを検出し、callerが修正した対象を渡す。自分では編集せず、解消と隣接契約・重大な回帰を確認し、`resolved`へ更新する。未解決blockerがなければ`PASS`
- **one-reviewer** — メインレビュー後にも判定を変えうる重要な残存リスクが一つの観点に集約できる。対応する1名だけを選ぶ
- **two-reviewers** — 異なる二観点に重大な残存リスクが具体化し、片方では代替できない難しい変更。理由を観点ごとに残し、2名だけを並列起動する。大規模・重要というラベルだけで2名にしない
- **security-route** — (a) securityに関する語を含むが信頼境界・攻撃面を変えない変更ではカテゴリだけでsecurityを選ばない。(b) 信頼境界または攻撃面を実質的に変える場合は、選択する1〜2名にsecurityを含める
- **lens-routing** — 責務境界・成果・実挙動・攻撃面のいずれかへ主要リスクが明確に寄る題材で、`architect` / `product` / `reliability` / `security`から対応する観点を選ぶ
- **behavior-asset** — 新しい副経路が本経路のgateを継承せず、referenceや下流skillとの契約もずれる変更。挙動資産を文章校正として扱わずcode-equivalentとして反証し、silent dropと不要なcontext増大を捕捉する
- **doc-sync** — 公開フラグまたは既定値を変更し、README、help、利用者向けメッセージ、変更面を参照するskill・rule・共通ガイドラインに旧command / flag / settingを残す。挙動資産はcode-equivalentとして整合を確認し、文書を編集せず不整合をfindingとして報告し、一般的な文章改善へ広げない
- **severity-blocking** — CRITICAL / HIGH / MEDIUM / LOWを各1件含む。CRITICAL/HIGHは`blocking: true`のblocker、MEDIUM/LOWは原則`blocking: false`とする。完了条件を満たせないMEDIUM/LOWはblockerにできる。accepted-risk以外の理由でHIGHをnon-blockingにせず、判定を通すためにseverityやblockingを操作しない。main findingにも具体的な根拠・成立経路・意味のある影響を求め、真偽未確定はseverityを付けず確認推奨とする
- **blocker-verdict** — 未解決blocker1件とnon-blocking2件。対象を変更せず`BLOCKED`を返す。callerがblockerだけを修正した後のrecheckではnon-blockingが残っていても`PASS`。review内部で修正loopを行わない
- **blocker-only-recheck** — 同一セッションの会話または直前の一時ディレクトリにある`integration.md`の未解決blockerと修正差分を使い、対象を編集せず解消・隣接契約・修正起因の重大な回帰だけを見る。独立レビュアを使う場合はdispatch契約も継承し、既存findingを保持して解消したblockerを`resolved`へ更新し、未解消なら`unresolved`のまま`BLOCKED`を返す。security必須割り当てはrecheckでも維持し、必要なレビュアを実行できなければ`BLOCKED`。修正で外部観測面または文書が変わった場合はPASS前にdoc-reviewを行う。対象を特定できない場合やセッションをまたいだ場合は通常レビューへ戻す
- **dispatch-isolation** — subagentへレビュー対象を特定できる情報（変更範囲・対象パス）を渡し、取得できない差分だけ本文で渡す。ユーザー指示・issueから確定したレビュー基準（目的、完了条件、対象範囲）、共通finding contractの内容、reviewer共通契約の内容、選択roleだけを加える。参照pathだけを渡して探索させず、Issue全文とmainの選択理由、メイン所見、暫定判定、他role・他レビュア結果を渡さず、全role fileを先読みしない。対象コードは変更せず指摘だけを返し、2名は独立に並列起動する
- **reviewer-availability** — securityを含む選択した必要なレビュアを実行できない場合は、main reviewで代替せず`BLOCKED`
- **integration-only** — role別レポートや完了マーカーを作らず、OSまたは実行環境の一時領域に実行ごとの一意なディレクトリを作り、`integration.md`を残す。固定のOS固有パスを前提にせず、必要なら絶対パスで共有する。リポジトリ内や`.gitignore`、`.git/info/exclude`を変更せず、一時ファイルをセッションをまたぐ正本として案内しなければ合格

## 題材構築の落とし穴

- 対象差分は適用可能なpatchまたは実在するgit差分にする
- routing評価では、期待する観点以外の本物のblockerを混ぜない
- 独立レビュアを利用できず必要なリスクを解消できない場合は`BLOCKED`
