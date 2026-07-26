# km-skill-improve scenario bank

## trigger-pairs: description 発火対

- 対象層: description（トリガー）— 対象範囲を挙動資産一般へ広げた境界の健全性ゲート
- 題材: description 一覧のみを与えて skill を選ばせる。should:「この skill を改善したいので効き目を検証して」「この rule の変更、挙動が良くなるか確かめて」/ should-not:「この skill にバグがないかレビューして」（km-review へ）「新しい skill を作って」（対象外・直接実装へ）
- 期待品質: should の 2 件で km-skill-improve が選ばれ、rule 変更でも発火する（skill 限定と読まれない）。should-not の 2 件では選ばれず、とくに「レビューして」が km-review へ流れる（正しさのレビューと挙動改善の検証の境界）
- 判定: 健全性ゲートとして確立（2026-07-26, #183 後の実走）。should 2 件・should-not 2 件すべて期待どおりに分岐し、rule 変更でも発火した（skill 限定と読まれない）。「この skill にバグがないかレビューして」が km-review へ流れたのは description 末尾の委譲文が決め手で、これが無ければ "skill" の語に引かれて誤射する。委譲文は load-bearing。description を変えるたびに必ず再走する
- トレードオフ / 注記: 「変更を検証して」がドメイン語を含まないため、通常のコード変更の検証依頼まで引き寄せる。冒頭の対象定義で救われているが、除外条項が description 後半にあるので、トリガ語を先に見るルータほど誤射しやすい構造は残る

## verification-design-with-bank: bank 付き対象への検証設計

- 対象層: 診断（記憶の読み込み）・eval-first・計測器選択・記憶フェーズ（書き戻し設計）
- 題材: scenario bank（evals/scenarios.md に既存 2 題材）を持つ対象 skill の複製 fixture を与え、「<既存 bank と別の層に効く>改善を入れて検証したい。分析と検証の設計一式を作って（実行は後で）」と依頼する。read-only sandbox・subagent 起動不可・ユーザ応答不可。成果物は分析 + 検証設計一式（題材・期待品質・起動プロンプト・後処理）
- 期待品質: bank を発見して読み、今回の変更が bank の守る挙動に触れるかを判定し、触れるなら回帰再走を一級手順として設計に組み込む。書き戻し先を正本の bank に向ける（fixture 複製に書き戻さない）。変更タイプに応じた floor / 統制 / blind 化手順・モデル固定・生成プロンプトへのトレース要求を含む
- 判定: 記憶・eval-first・トレース機構の採用根拠（2026-07-18, #140）

## light-consultation-no-ceremony: 表現整理相談の統制

- 対象層: 計測器の選択（self-check 行と回帰除外条項）・コスト原則
- 題材: bank を持つ対象 skill の「意味を変えない一文の言い回し整理」について「この程度の変更はどう検証すべき？」と相談する。read-only sandbox
- 期待品質: self-check のみを選択し、blind A/B・bank 回帰再走・bank 書き戻しを積まない。bank を読んだうえで「この変更は bank の守る挙動に触れない」と根拠を示して除外するのが最良。対象文が判断基準を内包する場合はその保存を self-check の実質として確認し、判断基準が変わるなら重い検証へ、というエスカレーション境界を示す
- 判定: 統制として維持（2026-07-18, #140）
- トレードオフ / 注記: 走レベルの事実誤認（対象文の実態の読み違え）が敗着になった走がある。skill 本文に帰着しない揺らぎとして扱う
