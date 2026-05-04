# AI Agent Guideline

全プロジェクト共通の Codex CLI 動作指針。プロジェクト固有の設定は各リポジトリの AGENTS.md で上書きする。AGENTS.md が無いリポジトリでは CLAUDE.md も参照する。

## 主要原則

1. **Clarify First**: 不明点を解消し、検証可能な完了条件を言語化してから着手する。影響が軽微なら前提を明示して前進する
2. **Working Code First**: 最小限の動くコードを素早く提示する。投機的な機能・抽象化・防御的処理を足さない
3. **Surgical Changes**: 依頼範囲だけを触る。既存コードの様式に合わせ、リファクタも範囲内に留める
4. **Review Thoroughly**: 完了条件と最初の仕様に立ち返り、見落としを潰す

## Codex CLI 運用

### Profile の使い分け

- 作業前に profile を選ぶ。通常実装は default、最新確認は `research`、レビューは `review`、読み取り専用探索は `readonly`
- default: `gpt-5.5 medium + workspace-write + on-request + cached web + shell network`。通常の編集と gh / package manager はそのまま動かし、sandbox 外実行が必要な操作だけ確認する既定
- `research`: `gpt-5.5 high + workspace-write + on-request + live web + shell network`。最新確認や外部仕様調査を進める
- `review`: `read-only + never + cached web + high reasoning`。レビュー、監査、影響調査
- `readonly`: 読み取り専用で安全にコードベースを探索したいとき
- `interactive`: `workspace-write + on-request + cached web + shell network`。承認付きの対話運用に戻したいとき
- `autonomous`: `workspace-write + never + cached web + shell network`。承認待ちを完全に避けたいが sandbox は残したいとき
- `full_trust`: `danger-full-access + never`。sandbox も外した完全信頼運用を明示したいときだけ使う

### 最新性の確認

- 最新情報、価格、仕様、法令、外部 API、ニュース性のある内容は cached search に頼らず `research` profile で確認する
- 既知のリポジトリ内情報は web より先にローカルファイルを読む
- 外部仕様を参照したら、判断と事実を分けて要約する

### 実装ルール

- 複雑な変更や外部調査を伴う変更は、まず Plan mode で論点と方針を固める
- 独立した調査や読み取りは並列化する
- `gh`、package manager、外部 API 確認などの CLI network は default で許可されている前提で使う
- 破壊的操作、権限変更、外部書き込みは必要性を説明してから進める
- 変更前後で確認手段を持つ。可能ならテスト、無理なら差分と静的確認を残す

### レビューと完了

- 実装後は `/km:review` を基準に確認する。必要に応じて深さも指定する
- 個別に実行したい場合だけ `/km:intent-review`, `/km:code-review`, `/km:quality-review`, `/km:doc-review` を使う
- レビューと検証が完了したら `/km:commit` でコミットする

### Skill 運用

- レビュー系は `/km:review` を入口にし、個別 skill はターゲットが明確なときだけ使う
- 下位 review skill は明示起動のみ（manual-only）に寄せ、`/km:review` を既定入口として残す
- `/km:commit` と `/km:github-workflow` はユーザーの自然言語要求から起動しうる workflow skill として扱う
- `/km:github-workflow` は GitHub 管理リポジトリで、PR / issue を伴う delivery 意図が明確な発話にだけ使う
- `/km:plan` は計画作成と `.plan/` 出力、GitHub issue 化が明示された発話にだけ使い、実装・PR 化は `/km:github-workflow` に委ねる
- skill を更新する場合は SKILL 本体を概要に保ち、詳細な例や参照情報は別ファイルに分離する
