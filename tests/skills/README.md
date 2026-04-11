# Skills Test Kit

`templates/skills/` の変更を継続的に検証するためのテスト資産。

このディレクトリは 2 つの用途を持つ。

1. 手動テストの手順書として使う
2. 将来スクリプトや eval runner で自動化するときの fixture と rubric の置き場にする

## 構成

- `manifest.yaml`
  - 全テストケースの一覧と目的
- `scenarios/`
  - skill ごとのシナリオ定義
- `rubrics/`
  - 期待挙動と採点観点
- `runs/`
  - 実行結果の保存先。`result-template.md` をコピーして使う

## テスト観点

このリポジトリの skill は、主に次を検証する。

1. Trigger
   - どの自然言語要求でどの skill が入口になるか
2. Routing
   - `km:review` が変更種別と会話コンテキストに応じて正しく振り分けるか
3. Output Quality
   - report-format と blocking 判定が壊れていないか
4. Workflow
   - `km:commit` と `km:github-workflow` が運用期待どおりに起動・継続するか
5. Policy Drift
   - README / AGENTS / CLAUDE / test docs の説明が skill 実装とズレていないか

## 手動実行の基本手順

1. 検証対象ブランチを checkout する
2. `templates/skills/` と `tests/skills/` を読む
3. `manifest.yaml` のケースを上から実行する
4. 各ケースごとに次を記録する
   - 実行日時
   - クライアント: Claude / Codex
   - 使用 profile や model
   - 入力文
   - 実際に起動した skill
   - 想定との一致 / 不一致
   - 問題点
5. 結果を `runs/YYYY-MM-DD-<label>.md` に残す
   - 形式は `runs/result-template.md` を使う

## 失敗の分類

- `trigger_failure`
  - 想定した skill が起動しない
- `routing_failure`
  - `km:review` の振り分けが誤る
- `quality_failure`
  - 出力品質、重大度、false positive 制御が不適切
- `workflow_failure`
  - commit / PR フローが途中で壊れる
- `doc_drift`
  - 説明文書と skill 実装が食い違う

## 将来の自動化方針

- `manifest.yaml` を index として読む
- `scenarios/*.yaml` を入力 fixture として使う
- `rubrics/*.md` を評価規準として runner に渡す
- `runs/` には人間のレビュー結果か、自動評価サマリーを保存する

まずは手動評価を正とし、十分にケースが固まってから自動化する。

## 機械的整合チェック

テスト資産そのものが壊れていないかは次で確認できる。

```bash
bash scripts/verify-skill-tests.sh
```

## Runner

runner は manifest を読んでケース一覧表示、dry-run、手動実行用の run sheet 生成を行う。

```bash
python3 scripts/run-skill-tests.py list
python3 scripts/run-skill-tests.py dry-run --tag review
python3 scripts/run-skill-tests.py scaffold --label smoke --client Codex --model gpt-5.4
python3 scripts/run-skill-tests.py summary --run-file tests/skills/runs/2026-04-11-smoke.md
python3 scripts/run-skill-tests.py validate-run --run-file tests/skills/runs/2026-04-11-smoke.md
```

現時点の runner は skill 実行そのものを自動化しない。役割は次の 5 つに絞る。

1. manifest と scenario を一貫した順序で読み込む
2. 実行対象ケースを filter する
3. 手動または将来の自動 eval 用の run sheet を生成する
4. run sheet の記入結果を集計する
5. run sheet の必須項目を検証する
