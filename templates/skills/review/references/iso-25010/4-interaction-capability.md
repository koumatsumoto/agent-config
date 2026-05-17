# インタラクション能力 (Interaction Capability)

ISO/IEC 25010:2023。「利用者と製品との相互作用を成立させる程度」を見る。Web UI / CLI / API のいずれにも適用する。

## 適切度認知性 (Appropriateness Recognizability)

- [ ] 用途・対象ユーザーが UI / コマンド名 / `--help` から識別できるか
- [ ] 初見ユーザが「これで自分の目的を達成できる」と判断できるか

## 学習性 (Learnability)

- [ ] 初期化 → 設定 → 実行の導線が自然で発見可能か
- [ ] よく使う操作にショートカット / バッチ操作 / sensible default があるか
- [ ] 失敗から復帰する方法 (undo / 取消 / 再試行) が学習しやすいか

## 操作性 (Operability)

- [ ] フォーカス可能要素 / キーボード操作 / shortcut 競合回避が成立しているか
- [ ] 反応性・フィードバック (loading / success / error) が明示されるか
- [ ] CLI で長時間処理に進捗表示があるか
- [ ] 物理的・認知的負担が大きい連続操作になっていないか
- [ ] ラベル / placeholder / コマンド名 / パラメータ名が機能を直接表現するか

## ユーザーエラー防止 (User Error Protection)

- [ ] 型・範囲・必須項目の入力時検証があるか
- [ ] 破壊的操作の事前検証 (確認 / Undo / dry-run / 差分プレビュー) があるか (利用者エラー回避視点。事故防止の冗長確認は 9-安全性側)
- [ ] 似た選択肢 (削除 / アーカイブなど) を視覚的・物理的に区別しているか
- [ ] 連続クリック / 重複送信を防ぐ仕組みがあるか

## ユーザー支援 (User Assistance)

- [ ] エラーメッセージが原因・次の行動を示すか
- [ ] コンテキストヘルプ / `--help` / ドキュメント導線があるか
- [ ] 失敗時のトラブルシュート手順が runtime ログ / メッセージから辿れるか
- [ ] ドキュメント (man / `--help` / API doc) と実装が一致するか

## ユーザーエンゲージメント (User Engagement)

- [ ] 進捗・完了・達成のフィードバックが適切か (ダークパターン / FOMO / 依存性誘発を回避)
- [ ] エラー時にもユーザを突き放さない (humanized error)

## 包摂性 (Inclusivity)

- [ ] WCAG 2.2 のレベル AA を満たすか (alt / 見出し階層 / コントラスト / フォーカス可視)
- [ ] WCAG 2.2 新規 SC (Focus Not Obscured / Target Size 24×24 / Dragging Movements / Consistent Help / Redundant Entry / Accessible Authentication) を考慮しているか
- [ ] i18n / l10n / RTL / 異なる入力方式 (タッチ / スクリーンリーダー / 音声) に対応するか
- [ ] 低帯域・低性能端末・古いブラウザでも基本機能が利用可能か
- [ ] 言語・地域依存の前提 (姓名順 / 住所形式 / 通貨 / 時間表記 / 数値) を吸収するか
- [ ] 動的 UI に対し ARIA live region / role / state が適切か

## 参照

- ISO/IEC 25010:2023
- WCAG 2.2 (Level AA)
- W3C ARIA Authoring Practices Guide
- Nielsen Norman Group usability heuristics
