# AI Agent Guideline

全プロジェクト共通の Claude Code 動作指針。プロジェクト固有の設定は各リポジトリの CLAUDE.md で上書きする。

## 主要原則

1. **Clarify First**: 不明点と完了条件を着手前に固める。検証可能な成功条件を言語化する
2. **Working Code First**: 最小限の動くコードを素早く提示する。投機的な機能・抽象化・防御的処理を足さない
3. **Surgical Changes**: 依頼範囲だけを触り、既存コードの様式に合わせる。無関係な改善や dead code 整理を混ぜない
4. **Refactor Within Scope**: 動いた後の改善は依頼範囲内に限定する
5. **Review Thoroughly**: 完了条件と最初の仕様に立ち返り、見落としを潰す

## ワークフロー

### 1. 仕様の詳細化と完了条件

- ユーザの指示は曖昧であることを前提とする。何度でも質問し、仕様を詳細化する
- 着手前に検証可能な完了条件を言語化する
- 複雑な作業では Plan Mode で計画を作成してから着手する

### 2. 実装

- まず最小限の動くコードを書く。投機的な抽象化や防御的処理は加えない
- 依頼範囲外のコードは触らない
- 独立したタスクは並列実行し、効率的に作業を進める

### 3. リファクタリング

- 動くコードが確認できたら、依頼範囲内で保守性・可読性を整える
- 既存コードの様式に合わせる。無関係な dead code の整理は混ぜない

### 4. レビュー

- `/km:review` でレビュー強度を選べる統合レビューを実行する（無指定は standard）
- 個別に実行したい場合だけ `/km:intent-review`, `/km:code-review`, `/km:quality-review`, `/km:doc-review` を直接呼び出す
- IMPORTANT: 完了条件と最初の仕様に立ち返り、見落としがないか入念に確認する

### 5. 完了

- レビューと検証が完了したら `/km:commit` でコミットする

## Skill 運用

- レビュー系は `/km:review` を入口にし、個別 skill はターゲットが明確なときだけ使う
- 下位 review skill は明示起動のみ（manual-only）に寄せ、`/km:review` を既定入口として残す
- `/km:commit` と `/km:github-workflow` はユーザーの自然言語要求から起動しうる workflow skill として扱う
- `/km:github-workflow` は GitHub 管理リポジトリで、PR / issue を伴う delivery 意図が明確な発話にだけ使う
- `/km:plan` は計画作成と `.plan/` 出力、GitHub issue 化が明示された発話にだけ使い、実装・PR 化は `/km:github-workflow` に委ねる
- skill を更新する場合は SKILL 本体を概要に保ち、詳細な例や参照情報は別ファイルに分離する
