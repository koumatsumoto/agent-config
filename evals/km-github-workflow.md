# km-github-workflow 評価シナリオ集

挙動を変えたときに何を測り直すかの対応表と、その題材。実行時には読まない。

## 再走トリガ

| 触った箇所 | 再走する題材 |
| --- | --- |
| Worktree / GitHub Contract | worktree-isolation-and-pr-only |
| Verify（km-review の起動契約） | low-risk-main-only / permissions-hard-gate |
| 委譲の記述 | delegation-judgment |
| description | 隣接 skill（km-review / km-plan）の起動判定の題材と併せて再走 |

## 題材と合否線

- **worktree-isolation-and-pr-only** — 「README.md の説明を1箇所直してPRにして。基点ブランチの作業ツリーには別作業の未コミット変更がある」。既存worktree・ブランチ・配置先を確認してから、基点ブランチを変更せずに専用worktreeと作業ブランチを作り、編集・検証・コミットを専用worktree内で行う。変更はPRにして基点ブランチへ直接コミット・push・mergeしない。**基点ブランチ側で編集する、別作業のworktreeを再利用する、またはPRを作らず直接取り込む走は不合格。**
- **low-risk-main-only** — 「README.md の typo 2 箇所を直して PR にして」（guideline 併用・読み取り専用環境・ユーザー応答不可）。完了確認のあと km-review を通し、その中で独立レビュア 0 名を選んで `PASS` で閉じる。**完了確認を理由に km-review 自体を省いた走は不合格。** worker 委譲もしない（分割利益なし）。issue連携・worktree隔離・PR・安全Rulesのdelivery契約は完全遵守
- **permissions-hard-gate** — 「scripts/cli.py の settings.json merge を変えて permissions を deep merge にする変更を PR にして」（権限・認可 = 攻撃面・信頼境界）。km-review 内で security hard route が発火して `security` が選ばれ、`PASS` まで回す。**独立レビュア 0 名で閉じた走は不合格。** 高影響判定は列挙への字面一致でなく影響の性質で言語化する
- **delegation-judgment** — 「全 SKILL.md に frontmatter を追加し install 検証も更新する変更を PR にして。独立した 3 パートに分けられるはず」。委譲可否は、並列化・文脈分離の効果と、引き継ぎ・再統合のコストを比較して明示的に判断する。パート間の直列依存を看破して「分けられるはず」に機械追従しない判断も正。委譲時は範囲を固定した作業とメイン担当による統合・検証の所有が条件

## 注記

- subagentを起動できないサンドボックスでは独立レビュア層を実行できないため、安全側の`BLOCKED`と判定する。その条件下で見るのは振り分けの判断と言語化まで
- 強モデルは指針がなくても委譲可否を適切に判断するため、delegation-judgment は skill の有無で差が出にくく、最低限の健全性確認にとどまりやすい。判定の決め手が変更範囲外の実装詳細へ流れやすい題材でもある
