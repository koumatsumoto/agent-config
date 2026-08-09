# km-skill-improve scenario bank

挙動を変えたときに何を測り直すかの対応表と、その題材。runtime では読まない。

## 再走トリガ

| 触った箇所 | 再走する題材 |
| --- | --- |
| description | trigger-pairs |
| 診断（記憶の読み込み）・eval-first の順序・記憶フェーズ | verification-design-with-bank |
| 計測器の選択表・コスト原則 | light-consultation-no-ceremony / verification-design-with-bank |

## 題材と合否線

- **trigger-pairs** — description 一覧のみから skill を選ばせる。should:「この skill を改善したいので効き目を検証して」「この rule の変更、挙動が良くなるか確かめて」/ should-not:「この skill にバグがないかレビューして」（km-review へ）「新しい skill を作って」（対象外・直接実装へ）。rule 変更でも発火し（skill 限定と読まれない）、「レビューして」は km-review へ流れる
- **verification-design-with-bank** — bank を持つ対象 skill の複製 fixture を与え、「<既存 bank と別の層に効く>改善を入れて検証したい。分析と検証の設計一式を作って（実行は後で）」と依頼する。read-only sandbox・subagent 起動不可・ユーザ応答不可。bank を発見して読み、変更が bank の守る挙動に触れるかを判定し、触れるなら回帰再走を一級手順として設計へ組み込む。書き戻し先は正本の bank（fixture 複製に書き戻さない）。変更タイプに応じた floor / 統制 / blind 化手順・モデル固定・トレース要求を含む
- **light-consultation-no-ceremony** — bank を持つ対象 skill の「意味を変えない一文の言い回し整理」について「この程度の変更はどう検証すべき？」と相談する。read-only sandbox。self-check のみを選び、blind A/B・回帰再走・bank 書き戻しを積まないのが合否線。bank を読んだうえで「この変更は bank の守る挙動に触れない」と根拠を示して除外するのが最良。対象文が判断基準を内包するならその保存を self-check の実質とし、判断基準が変わるなら重い検証へ、というエスカレーション境界を示す

## 落とし穴

- description 末尾の委譲文（レビューは km-review へ）は load-bearing。これが無いと「skill」の語に引かれて km-review 相当の依頼を誤射する
- 「変更を検証して」はドメイン語を含まないため通常のコード変更の検証依頼まで引き寄せる。冒頭の対象定義で救われるが、除外条項が description 後半にあるのでトリガ語を先に見るルータほど誤射しやすい
- light-consultation-no-ceremony は走レベルの事実誤認（対象文の実態の読み違え）で敗着になることがある。skill 本文に帰着しない揺らぎとして扱う
