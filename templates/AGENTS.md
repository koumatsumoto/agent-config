# AI Agent Guideline

全プロジェクト共通の Codex CLI 動作指針。プロジェクト固有の設定は各リポジトリの AGENTS.md で上書きする。AGENTS.md が無いリポジトリでは CLAUDE.md も参照する。

## 主要原則

1. **Clarify First**: ユーザの指示は曖昧である前提に立つ。思い込みで着手せず、理解・要求・制約・検証可能な完了条件を言語化する。特に「これで何を達成したいのか」というビジネス価値が不明確な場合は、具体的な作業内容より先に質問する
2. **Build Working Code First**: ビジネス価値を最短で検証できる最小限の設計と動く成果を優先する。過剰な機能・抽象化・防御的処理・早すぎる最適化を足さない。重大な設計手戻りが見込まれないなら、動かして検証を回す
3. **Change Surgically**: 明示的な指示がない限り、依頼範囲だけを最低限の影響で触る。既存コードの様式・責務境界・周辺設計に合わせ、依頼範囲内で全体整合を優先する
4. **Review Thoroughly**: 最初に確認したビジネス価値・要求・完了条件に立ち返り、ゴールを達成しているかを最重視してレビューする。実装量ではなく成果を検証し、見落とし・不要な変更・スコープ外混入・検証不足を潰す

## ワークフロー

1. Plan: 入念な計画が必要なものは `km:plan` で計画を作り込み、GitHub issue にする。軽微なものは issue にせず、方針と完了条件だけ固めて進める
2. Branch: Git repo で PR delivery を前提にする作業では、基本的に作業ブランチを切る
3. Capture: 作業中にタスクと無関係な改善項目に気付いたら、現作業に混ぜず follow-up issue として残す。明らかな既存 issue がある場合は新規作成せず参照する
4. Review: 実装後は主要原則に基づいてレビューする。複雑な変更は `km:review` を使って深く確認する
5. Publish: 完了したらコミットし、PR にしてユーザへ報告する
6. Record: 作業中に気付いた作業方法の改善点は `.plan/` 配下の作業メモへ随時追記し、完了報告時にユーザへ共有する

## 運用ルールの参照

- GitHub delivery の詳細手順は `km:github-workflow` を参照する。`AGENTS.md` には全体の流れだけを書き、ブランチ・commit・PR・issue 連携・follow-up issue・完了報告の詳細は skill 側に寄せる
- 計画 issue 化や `.plan/` への materialize が必要な場合は `km:plan` を参照する
- レビューは `km:review` を入口にする。個別 review skill はターゲットが明確な場合だけ使う
- コミット作成は `km:commit` を参照する
- `.plan/` はローカル一時作業場。共有成果物では GitHub issue / PR / comment を正本にし、`.plan/` 配下の具体的なファイルを source of truth として参照しない

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

- 独立した調査や読み取りは並列化する
- `gh`、package manager、外部 API 確認などの CLI network は default で許可されている前提で使う
- 破壊的操作、権限変更、外部書き込みは必要性を説明してから進める
- 変更前後で確認手段を持つ。可能ならテスト、無理なら差分と静的確認を残す
