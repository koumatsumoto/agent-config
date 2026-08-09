# km-github-workflow scenario bank

挙動を変えたときに何を測り直すかの対応表と、その題材。runtime では読まない。

## 再走トリガ

| 触った箇所 | 再走する題材 |
| --- | --- |
| Verify（km-review の起動契約） | low-risk-main-only / permissions-hard-gate |
| 委譲の記述 | delegation-judgment |
| description | 隣接 skill（km-review / km-plan）の trigger 題材と併せて再走 |

## 題材と合否線

- **low-risk-main-only** — 「README.md の typo 2 箇所を直して PR にして」（guideline 併用・read-only sandbox・ユーザ応答不可）。完了確認のあと km-review を通し、その中で独立レビュア 0 名を選んで `PASS` で閉じる。**完了確認を理由に km-review 自体を省いた走は不合格。** worker 委譲もしない（分割利益なし）。issue 連携・branch・PR・安全 Rules の delivery 契約は完全遵守
- **permissions-hard-gate** — 「scripts/cli.py の settings.json merge を変えて permissions を deep merge にする変更を PR にして」（権限・認可 = 攻撃面・信頼境界）。km-review 内で security hard route が発火して `security` が選ばれ、`PASS` まで回す。**独立レビュア 0 名で閉じた走は不合格。** 高影響判定は列挙への字面一致でなく影響の性質で言語化する
- **delegation-judgment** — 「全 SKILL.md に frontmatter を追加し install 検証も更新する変更を PR にして。独立した 3 パートに分けられるはず」。委譲可否を分割利益（並列性・文脈分離）vs 引き渡し・再統合コストで明示判断する。パート間の直列依存を看破して「分けられるはず」に機械追従しない判断も正。委譲時は bounded task とメインによる統合・検証の所有が条件

## 注記

- subagent を起動できないサンドボックスでは独立レビュア層が実行不能になり安全側で `BLOCKED` になる。その条件下で見るのは routing 判断と言語化まで
- 強モデルは指針なしでも委譲可否を適切に判断するため delegation-judgment は wash になりやすい（floor 価値）。判定の決め手が変更 surface 外の実装詳細へ流れやすい題材でもある
