# AI Agent Guideline

全プロジェクト共通の Codex CLI 動作指針。プロジェクト固有の設定は各リポジトリの AGENTS.md で上書きする。AGENTS.md が無いリポジトリでは CLAUDE.md も参照する。

## 主要原則

1. **Clarify First**: 要求・制約・検証可能な完了条件を理解し、妥当な前提を置いて着手する。成果物を左右する前提は明示する。答えが「やること」を変える未決事項のときだけ、着手前に確認する。特にビジネス価値（これで何を達成したいのか）が不明確な場合は、具体的な作業内容より先に質問する
2. **Build Working Code First**: ビジネス価値を最短で検証できる最小限の動く成果を優先し、早く動かして検証する。作り込みは過不足を避け、リスクに見合わせる
3. **Change Surgically**: 明示的な指示がない限り、依頼範囲だけを最低限の影響で触る。既存コードの様式・責務境界・周辺設計に合わせ、全体整合を優先する
4. **Review Adversarially**: レビューは「正しい/十分」と仮定せず、まず壊そう・反証しようと試みる。最初に確認したビジネス価値・要求・完了条件に立ち返りゴール達成を最重視しつつ、見落とし・不要な変更・スコープ外混入・検証不足を能動的に探す。自分とサブエージェント（レビュア）の結論も疑い、主張は検証してから採用する

## ワークフロー

1. Plan: 入念な計画が必要なものは `km:plan` で計画を作り込み、GitHub issue にする。軽微なものは issue にせず、目的・方針・完了条件・検証方法を固めて進める
2. Develop: Git repo で PR delivery を前提にする作業では基本的に作業ブランチを切り、既存コードの様式・責務境界・周辺設計に合わせて最小限の動く変更を実装する
3. Record: 作業中に気付いた改善点は現作業に混ぜず記録する。作業方法の改善点は `.plan/` 配下の作業メモへ随時追記する。タスクと無関係な改善項目（作業方法の改善を含む）は完了報告でユーザへ共有し、指示があれば follow-up issue にする
4. Review: 実装後は主要原則と完了条件に基づいてレビューする。複雑な変更は `km:review` を使って深く確認し、見落とし・不要な変更・検証不足を潰す
5. Report: レビューと検証が済んだらコミットし、PR にしてユーザへ報告する。PR URL、変更要約、検証結果、記録した改善点を共有する

## 運用ルールの参照

- GitHub delivery の詳細手順は `km:github-workflow` を参照する。`AGENTS.md` には全体の流れだけを書き、ブランチ・commit・PR・issue 連携・follow-up issue・完了報告の詳細は skill 側に寄せる
- 計画 issue 化や `.plan/` への materialize が必要な場合は `km:plan` を参照する
- レビューは `km:review` を入口にする。個別 review skill はターゲットが明確な場合だけ使う
- コミット作成は `km:commit` を参照する
- `.plan/` はローカル一時作業場。共有成果物では GitHub issue / PR / comment を正本にし、`.plan/` 配下の具体的なファイルを source of truth として参照しない

## 成果物への記録方針

成果物（コードコメント / docstring / README / skill・rule doc 等）には、**現状の状態とその意図（現設計の WHY: 設計判断・制約・防御の目的）を現在形で書く**。読み手が必要なのは「今この対象が何をし、なぜそうなっているか」であって、どう変遷したかではない。

- **進行管理・中間の作業背景は書かない**: 進捗・TODO 的な作業メモ・誰がいつ・「旧 X」「従来は Y だったが今は Z」「〜から格上げ / 再設計」「どの PR 由来」など、変遷や由来を成果物本文に混ぜない。設計変更の履歴は commit / PR に属する
- **意図に過去の事象を持ち込まない**: 防御・制約の理由は「何を防ぐ / 満たすために今こうなっているか」を現在形で書く。「以前は壊れた」「かつて〜だった」のような過去の事象・状態への言及はしない
- **出典としての issue / PR 番号**: 仕様・判断の根拠としての番号は、判断理由を本文に書いたうえで補助的に残してよい。番号を「この変更の由来」（〜で追加 / 格上げ 等）として使わない
- **TODO コメント**: 「現設計の既知の制約・未対応点」を示す TODO だけ可。担当・期日・進捗のような進行管理は書かず、対応予定がある作業は issue 化する
- **commit message / PR body**: 設計判断・動機・背景は書いてよいが、過剰なローカルの進捗管理（内部タスク ID、逐次の作業ログ、レビュー反映の往復履歴）は書かない。最終差分を理解するのに必要な背景だけを的確に
- **例外**: migration guide / deprecation 注記 / CHANGELOG は「旧→新の状態遷移の説明」自体が用途なので、状態遷移を書いてよい

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
