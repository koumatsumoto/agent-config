# km-review scenario bank

## levelless-depth-decision: レベル無指定時の深さ自己決定

- 対象層: 深さとレビュアの決定・独立レビュア起動判断・結果契約
- 題材: 「この diff をレビューして」（レベル・深さの指定なし）。2 ファイル中規模 diff に仕込み 2 階層: (i) 高影響 — エラーハンドラが api_token（環境変数由来の秘密）・permissions を含む実効 settings 全体を stderr へ dump（額面は「調査しやすさのためのエラーメッセージ改善」にカモフラージュ）/ (ii) 軽微 — エラーメッセージ接頭辞の不統一
- 期待品質: (i) を CRITICAL/HIGH で捕捉し BLOCKED（絶対条件。落とせば他観点に関わらず不合格）。リスク軸（規模・新規経路・不可逆性・攻撃面・挙動資産）を明示分解して深さとレビュア選択（security / adversary 起動、architect 非起動の根拠）を導出し、深さと理由を報告に 1 行残す。(ii) は LOW 級・簡潔に留める。結果契約（重大度・PASS/BLOCKED・偽陽性確認・アクションリスト）を維持
- 判定: 適応型深度の採用根拠（2026-07-18, #142）。常時フル構成の変異は architect 空振り・計量なしの過剰儀式で不採用。トリガ語限定の狭い description は (ii) 検出漏れと「セキュリティ観点で徹底的に見て」の under-trigger を示した。SKILL.md を契約中心に圧縮（手続き叙述・逐語テンプレート排除）した構成でも本題材を再走し、捕捉・BLOCKED・深度根拠を維持。**Claude 5 世代向けに情報設計を再構築した構成（2026-07-26, #179 / #183）でも再走**し、(i) を HIGH + BLOCKED で捕捉、5 リスク軸の明示分解から `thorough`（3 名全員）を導出、結果契約を維持することを確認した
- トレードオフ / 注記: confirmed かつ影響が壊滅的な秘密漏出は CRITICAL が正（HIGH 据え置きは calibration の弱み）。深さラベルは起動構成と整合させる（該当レビュアのみは「standard + 昇格」、`thorough` は 3 名全員）
- 題材構築の落とし穴（2026-07-26 の走で顕在化）: (a) 対象差分は **`git apply --check` を通る well-formed な patch** にする。壊れた patch はレビュアが「根拠が検証不能な提示に依存している」と正しく指摘し、本来測りたい層の評価が濁る。(b) 軽微側 (ii) の文字列を **repo に実在する文言と衝突させない**。衝突すると値・契約の drift（`generalist-review.md` の無条件チェック）に該当して MEDIUM 級が正解になり、「LOW 級・簡潔」の期待が成立しなくなる

## trigger-pairs: description 発火対

- 対象層: description（トリガー）— add-on 再定位の健全性ゲート
- 題材: should:「この変更、独立した視点で敵対的に深くレビューしてほしい」「セキュリティ観点で徹底的に見て」/ should-not:「実装終わったので仕上げて PR にして」「typo 直した、確認して」（低〜中リスクの一般的 diff の文脈で、description 一覧のみから判定させる）
- 期待品質: should で km-review が選ばれ、should-not は km-github-workflow の完了確認・メインの軽量確認へ流れる（"Routine post-implementation completion checks belong to the caller" が効く）
- 判定: 健全性ゲートとして維持（2026-07-18, #142）。description を変えるたびに必ず再走する
