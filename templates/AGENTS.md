# AI Agent Guideline

全プロジェクト共通の Codex CLI 動作指針。プロジェクト固有の設定は各リポジトリの AGENTS.md で上書きする。AGENTS.md が無いリポジトリでは CLAUDE.md も参照する。

## 主要原則

1. **Clarify, Then Commit**: 不明点が成果物に影響する場合は先に確認する。影響が軽微なら前提を明示して前進する
2. **Use The Right Profile First**: 作業前に profile を選ぶ。通常実装は default、最新確認は `research`、レビューは `review`、高速な軽作業は `quick`
3. **Verify Freshness Explicitly**: 最新情報、価格、仕様、法令、外部 API、ニュース性のある内容は cached search に頼らず `research` profile で確認する
4. **Working Code First**: まず動く変更を作り、確認後に整える
5. **Review Thoroughly**: 作業後は最初の依頼に立ち返ってレビューし、見落としを潰す

## Codex CLI 運用

### Profile の使い分け

- default: `workspace-write + on-request + cached web`。通常の開発と調査
- `research`: `workspace-write + on-request + live web + high reasoning`。最新確認や外部仕様調査
- `review`: `read-only + never + cached web + high reasoning`。レビュー、監査、影響調査
- `quick`: `workspace-write + on-request + cached web + fast tier`。定型修正や軽い確認
- `readonly`: 読み取り専用で安全にコードベースを探索したいとき

### 調査ルール

- 最新性が少しでも重要なら live web で一次情報を確認する
- 既知のリポジトリ内情報は web より先にローカルファイルを読む
- 外部仕様を参照したら、判断と事実を分けて要約する

### 実装ルール

- まず小さく動く差分を作り、その後に保守性を整える
- 独立した調査や読み取りは並列化する
- 破壊的操作、権限変更、外部書き込みは必要性を説明してから進める
- 変更前後で確認手段を持つ。可能ならテスト、無理なら差分と静的確認を残す

### レビューと完了

- 実装後は `/km:review` を基準に確認する
- 個別に実行したい場合だけ `/km:intent-review`, `/km:code-review`, `/km:quality-review`, `/km:doc-review` を使う
- レビューと検証が完了したら `/km:commit` でコミットする

### Skill 運用

- レビュー系は `/km:review` を入口にし、個別 skill はターゲットが明確なときだけ使う
- 下位 review skill は明示起動のみ（manual-only）に寄せ、`/km:review` を既定入口として残す
- `/km:commit` と `/km:github-workflow` はユーザーの自然言語要求から起動しうる workflow skill として扱う
- skill を更新する場合は SKILL 本体を概要に保ち、詳細な例や参照情報は別ファイルに分離する
