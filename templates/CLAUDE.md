# AI Agent Guideline

全プロジェクト共通の Claude Code 動作指針。プロジェクト固有の設定は各リポジトリの CLAUDE.md で上書きする。

## 主要原則

1. **Clarify First**: 不明点を解消し、検証可能な完了条件を言語化してから着手する
2. **Working Code First**: 最小限の動くコードを素早く提示する。投機的な機能・抽象化・防御的処理を足さない
3. **Surgical Changes**: 依頼範囲だけを触る。既存コードの様式に合わせ、リファクタも範囲内に留める
4. **Review Thoroughly**: 完了条件と最初の仕様に立ち返り、見落としを潰す

## ワークフロー

### 1. 仕様の詳細化

- ユーザの指示は曖昧である前提に立ち、不明点は積極的に質問して仕様を詳細化する
- 複雑な作業では Plan Mode で計画を作成してから着手する

### 2. 実装

- 独立したタスクは並列実行し、効率的に作業を進める

### 3. リファクタリング

- 動いた後に、依頼範囲内で読みやすさを整える

### 4. レビュー

- `/km:review` でレビュー強度を選べる統合レビューを実行する（無指定は standard）
- 個別に実行したい場合だけ `/km:intent-review`, `/km:code-review`, `/km:quality-review`, `/km:doc-review` を直接呼び出す

### 5. 完了

- レビューと検証が完了したら `/km:commit` でコミットする

## Skill 運用

- レビュー系は `/km:review` を入口にし、個別 skill はターゲットが明確なときだけ使う
- 下位 review skill は明示起動のみ（manual-only）に寄せ、`/km:review` を既定入口として残す
- `/km:commit` と `/km:github-workflow` はユーザーの自然言語要求から起動しうる workflow skill として扱う
- `/km:github-workflow` は GitHub 管理リポジトリで、PR / issue を伴う delivery 意図が明確な発話にだけ使う。計画作成や `.plan/` 出力、計画 issue 化を含む依頼では `/km:plan` を先に実行し、生成された issue 番号で `/km:github-workflow` を起動する
- `/km:plan` は計画作成と `.plan/` 出力、計画の GitHub issue 化が明示された発話にだけ使い、実装・PR 化は `/km:github-workflow` に委ねる。GitHub 管理 repo では `.plan/` 出力と issue 化を 1 セットの workflow として進める
- 単独の "issue にして" や変更差分の "レビューして" は `/km:plan` の trigger にしない（前者は `/km:github-workflow`、後者は `/km:review` に寄せる）
- `.plan/` はローカル一時作業場であり、issue 本文・PR 本文・commit message・issue/PR comments など共有される成果物から `.plan/` への参照リンクを書かない。共有用の正本は GitHub issue / PR の URL に集約する
- skill を更新する場合は SKILL 本体を概要に保ち、詳細な例や参照情報は別ファイルに分離する
