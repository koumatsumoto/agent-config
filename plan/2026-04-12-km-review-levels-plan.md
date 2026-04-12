# `km:review` Level Routing Plan

Updated: 2026-04-12

## Summary

`km:review` を単一の「常にフルレビューする入口」から、3 段階の実行レベルを持つ review orchestrator に変更する。

公開レベルは `thorough` / `standard` / `quick` とする。

- `thorough`: 現行のフルパターン
- `standard`: 専門家レビューを省略した通常レビュー
- `quick`: 最小レビュー。原則 `code-review` のみ

自然言語の既定動作は次で固定する。

- `深くレビューして`、`厳しめにレビューして`、`thorough review` など: `thorough`
- `レビューして`、`チェックして`、`変更を確認して`: `standard`
- `浅くレビューして`、`軽くレビューして`、`quick review` など: `quick`

無指定時の既定値は `standard` とする。これは「毎回フルレビューでは重い」という今回の問題意識を反映しつつ、`quick` 既定にして見落としを増やすことも避けるためである。

## Problem Statement

現行の [templates/skills/review/SKILL.md](/home/kou/work/agent-config/templates/skills/review/SKILL.md) は、実質的に `thorough` 相当のレビューを既定で実行する。

現状の特徴:

- code change では `intent-review`、`code-review`、`quality-review`、expert review、必要に応じて `doc-review` まで走る
- expert review は 2 persona を伴い、実行コストと出力量が大きい
- quality-review は 9 品質特性サマリーを必須にしており、軽い確認用途には重い
- tests も「expert review が常にある程度動く」前提を持っている

この設計は厳密だが、日常的なセルフチェックや小さな変更確認には過剰である。結果として `/km:review` を標準入口として維持したい意図と、「重すぎて日常利用しづらい」という運用実態がずれている。

今回の変更の目的は、`km:review` を捨てずに入口を維持したまま、レビュー強度を要求に応じて切り替えられるようにすることにある。

## Precondition: Existing Quality Summary Bug

レベル対応の前提として、現行の orchestrator には quality-review の品質評価サマリーが最終統合レポートへ伝搬しない不整合がある。

原因:

- `quality-review` 側は 9 品質特性テーブルの出力を必須にしている
- 一方で `review/SKILL.md` はサブエージェント返却形式を実質的に「件数サマリー + 個別所見」に限定している
- そのため Phase 6 は「品質評価サマリーをそのまま含める」と書いていても、オーケストレーターにテーブルが返ってこない

この不整合を放置すると、`standard` で quality-review を維持しても、期待する品質サマリーが表示されない。したがって、レベル対応の実装ではこのバグ修正を Step 0 として先に含める。

## Design Decisions

### 1. 公開レベル名は `thorough` / `standard` / `quick` にする

採用理由:

- `high` / `medium` / `low` は序列は明確だが、何が省略されるかが名前から読み取りにくい
- `Full / Focused / Quick` はすでに下位 skill の内部深度として使っており、入口レベル名に流用すると概念が衝突する
- `thorough` / `standard` / `quick` は「深く」「普通に」「浅く」の自然言語対応がしやすい
- `standard` を真ん中に置くことで、無指定時の既定値として自然に扱える

不採用理由:

- `high` / `medium` / `low`: 実行内容が連想しづらい
- `full` / `focused` / `quick`: `focused` は「何に focus するのか」が公開 API 名として曖昧

### 2. 無指定の `km:review` は `standard` にする

採用理由:

- 現行の `thorough` 既定を維持すると、今回の「重すぎる」という要求をほとんど解消できない
- `quick` 既定にすると、quality-review や intent-review を期待する既存運用からの後退が大きい
- `standard` は日常利用向けの既定としてバランスが良い

期待する運用:

- 普段の確認は `レビューして` で `standard`
- 厳密確認が必要なときだけ `深くレビューして`
- 小変更の軽い確認は `浅くレビューして`

### 3. 入口レベルと下位 skill の内部深度は分離する

固定方針:

- 公開 API のレベル: `thorough` / `standard` / `quick`
- 下位 skill がすでに持つ内部深度: `Full` / `Focused` / `Quick`

採用理由:

- 既存の `code-review` / `quality-review` / `doc-review` は、変更タイプごとの内部深度表をすでに持っている
- ここを入口レベルに置き換えると、各 skill の責務まで巻き込んだ再設計になる
- 今回の主眼は orchestrator の重さ調整であり、下位 skill の評価ロジック自体はなるべく温存した方が安全

実装上の扱い:

- 入口レベルは「どの review を起動するか」を決める
- 起動された review の中で、変更タイプに応じて `Full` / `Focused` / `Quick` を従来どおり選ぶ

この方針は `standard + test/config/chore` にも適用する。つまり `standard` が quality-review を起動する場合でも、当該 review の内部深度は従来どおり `Quick` のままとする。

### 4. ルーティングは「変更タイプ優先、レベルは絞り込みのみ」で解決する

固定方針:

- 変更タイプと変更構成が first-pass の routing を決める
- レベルはその結果を上書きしない
- レベルは、変更タイプルーティングで「実行候補」となった review をさらに絞り込む方向にのみ作用する

これを 2 次元ルーティングの優先順位ルールとする。

この 1 ルールで、次の競合を解消する。

- docs-only + `standard`: docs-only の first-pass routing が優先されるため、`doc-review` のみ実行
- docs-only + `thorough`: `code-review` / `quality-review` / expert は追加されず、`doc-review` のみ実行
- test/config/chore + `thorough`: first-pass routing が優先されるため、expert review は追加されない
- code change + `quick`: first-pass で code-review / quality-review が候補でも、`quick` が code-review のみに絞り込む

実装時は 18 組み合わせの完全表を無理に肥大化させず、この優先順位ルールと代表例で仕様を固定する。

### 5. レベルごとの実行内容は明示的に固定する

実行マトリクスは次で固定する。

| Level | intent-review | code-review | quality-review | expert review | doc-review |
|---|---|---|---|---|---|
| `thorough` | 条件付き実行 | 実行 | 実行 | 実行 | 条件付き実行 |
| `standard` | 条件付き実行 | 実行 | 実行 | スキップ | 条件付き実行 |
| `quick` | スキップ | 実行 | スキップ | スキップ | 原則スキップ |

補足:

- このマトリクスは、変更タイプ routing が code change の通常 path を返した場合の「最大有効化セット」を示す。docs-only や test/config/chore などの変更タイプ routing は、Decision 4 に従ってここからさらに絞り込む
- `条件付き実行` は現行のルーティング条件を維持する
- `thorough` のみ、現行 expert review を実施する
- `standard` は品質レビューまでは維持しつつ、最も重い expert review を省く
- `quick` は最小構成として code-review に絞る

### 6. `thorough` では fix のサイズ閾値を無視して expert review を常時実行する

固定方針:

- `thorough` は、変更タイプ routing が expert review を候補に含める path では、expert review を常時実行する。変更タイプ routing が expert を候補に含めない path（docs-only、test/config/chore）には影響しない
- `fix` でも、現行の小規模変更閾値は適用しない
- `standard` / `quick` はサイズにかかわらず expert review を実行しない

採用理由:

- `thorough` の意味を「最も厳密な review」として一貫させるため
- レベル指定した利用者は、サイズではなく厳密性を優先しているとみなすため
- `thorough` に入ったのに small fix だけ expert が省略される挙動は、利用者の期待とずれやすいため

### 7. docs-only の `quick` は `doc-review` を優先する例外を設ける

固定方針:

- `quick` の原則は `code-review` のみ
- ただし docs-only 変更では `code-review` を走らせず、`doc-review` を実行する

採用理由:

- docs-only 変更に `code-review` を適用しても本質的なレビューにならない
- 現行テストにも docs-only は `doc-review` だけに流す前提がある
- 「quick は code-review だけ」という原則を機械的に優先すると、docs-only のレビュー品質が壊れる

この例外は「変更対象に対して最小限有効な review を選ぶ」という設計原則の一部として扱う。`quick` の目的は review 種別の削減であり、不適切な review への置き換えではない。

### 8. expert review の責務は `thorough` に閉じ込める

採用理由:

- 現行の重さの主要因は expert review である
- quality-review は品質観点を体系的に確認するため、`standard` でも残す価値がある
- expert review は「内部レビューの盲点補完」という役割であり、常時必須ではない

期待する結果:

- `standard` で日常利用の負荷を下げる
- `thorough` では従来の強いレビューを維持する
- レベル差分が明確になる

### 9. サブエージェント返却契約は「汎用ルール + 個別例外」で定義する

固定方針:

- 下位 review の返却契約は原則「重大度ごとの件数サマリー + 個別所見」
- ただし `quality-review` に限り、これに加えて「品質評価サマリー（9 品質特性テーブル）」も必須返却とする

採用理由:

- 汎用ルールだけだと quality-review 固有の重要出力が脱落する
- 逆に「各 subagent が自身の report-format を完全返却してよい」とすると、出力量が膨張しやすい
- 最小修正で既知バグを潰すには、「汎用ルール + 個別例外」が最も安全

### 10. 出力形式は「省略」ではなく「スキップ表示」を維持する

固定方針:

- 実行されなかった review セクションも残し、`（スキップ）` を出す
- `quality-review` 未実行時は品質評価サマリーも `（スキップ）`
- expert review 未実行時も `### 第三者専門家レビュー` セクションを残す

採用理由:

- orchestrator の判断結果が可視化される
- 「なぜその観点が出てこないのか」がレポート上で分かる
- テストでも契約が固定しやすい

## Implementation Changes

### Step 0. 品質サマリーバグ修正

[templates/skills/review/SKILL.md](/home/kou/work/agent-config/templates/skills/review/SKILL.md) の subagent 返却契約に、次の 1 行を追加する。

- `quality-review は上記に加えて「品質評価サマリー（9 品質特性ごとの評価テーブル）」も返させる`

この修正はレベル実装と独立した既知不具合修正であり、`standard` / `thorough` の正しい output contract を成立させる前提とする。

### A. `templates/skills/review/SKILL.md`

次を更新する。

- description を「包括レビュー」から「レベル指定可能な review orchestrator」に寄せる
- 冒頭説明で 3 レベルの目的を定義する
- Success Criteria に「要求されたレベルに応じて適切な review のみを走らせる」を追加する
- Workflow を `Level selection -> Routing -> Review execution -> Aggregation` の観点で整理する
- Phase 1 に以下を明記する
  - change type
  - has_code / has_docs
  - conversation context
  - requested level
  - selected level
- 「変更タイプ routing が先、レベルは絞り込みのみ」という優先順位ルールを 1 行で明記する
- 代表的な合成例を併記する
  - docs-only + `standard`
  - docs-only + `thorough`
  - test/config/chore + `thorough`
  - code-only + `quick`
- 自然言語からのレベル推定ルールを記述する
- 現行の routing table をレベル対応版に置き換える
- `thorough` の fix ではサイズ閾値を無視して expert review を常時実行することを明記する
- expert review の実行条件を `thorough` 限定に変更する
- quality-review の返却契約に、品質評価サマリーテーブルを追加する
- `quick` の docs-only 例外を明文化する
- Phase 6 の統合ルールをレベル別出力契約に合わせて更新する

### B. `templates/skills/review/report-format.md`

次を更新する。

- 統合サマリーに `実行レベル` を追加する
- `standard` の出力例を追加する
  - quality summary は出る
  - expert review は `（スキップ）`
- `quick` の出力例を追加する
  - code-review 結果のみ
  - quality summary は `（スキップ）`
  - intent / expert / doc は必要に応じて `（スキップ）`
- docs-only + quick の場合の `doc-review` 例外出力を追記する

### C. 関連ドキュメント

次を更新する。

- [README.md](/home/kou/work/agent-config/README.md)
  - `km:review` の説明を「レベル付き review 入口」として簡潔に更新する
- [templates/AGENTS.md](/home/kou/work/agent-config/templates/AGENTS.md)
  - `/km:review` の説明を現行の「包括的レビュー」からレベル付き前提に調整する
- [templates/CLAUDE.md](/home/kou/work/agent-config/templates/CLAUDE.md)
  - AGENTS 側と同じ内容に揃える

ここでは詳細な実行マトリクスまで書き込まず、「`km:review` は既定の review 入口で、必要に応じて深さを指定できる」程度に留める。詳細契約は SKILL 本体に寄せる。

### D. テスト更新

#### `tests/skills/scenarios/review-routing.yaml`

次の観点に置き換える。

- 無指定レビューは `standard`
- `深くレビューして` は `thorough`
- `浅くレビューして` は `quick`
- docs-only + `standard` は `doc-review` のみ
- docs-only + `thorough` は `doc-review` のみ
- test/config/chore + `thorough` でも expert review は追加されない
- `standard` では expert review がスキップ
- `thorough` では expert review が実行
- `quick` では quality-review が走らない
- docs-only + quick は `doc-review` を使う

既存シナリオの更新対象を明記する。

- `review-routing-code-only`: default を `standard` 扱いに変更し、expert expectation を `skipped` に更新
- `review-routing-no-conversation-context`: default を `standard` 扱いに変更し、expert expectation を `skipped` に更新
- `review-routing-code-and-docs-self`: default を `standard` 扱いに変更し、expert expectation を `skipped` に更新
- `review-routing-code-and-docs-third-party`: default を `standard` 扱いに変更し、expert expectation を `skipped` に更新

新規シナリオを追加する。

- `thorough` の後方互換確認
  - `深くレビューして` が、現行フルパターン相当の routing を返すこと
- 2 次元交差ケース
  - docs-only + `standard`
  - docs-only + `thorough`
  - quick + test-only
  - standard + config/chore

#### `tests/skills/scenarios/review-quality.yaml`

次を分けて検証する。

- `thorough`: expert findings と integrated blocking に参加する
- `standard`: quality summary は必須、expert review は `（スキップ）`
- `quick`: quality summary は `（スキップ）`
- `quick`: code-review の finding だけで blocking 判定できる

既存シナリオの更新対象を明記する。

- `review-quality-expert-severity-format`: prompt を `深くレビューして` に変更し、`thorough` 下で expert severity 形式と blocking 参加を検証する
- `review-quality-expert-executed-for-large-fix`: prompt を `深くレビューして` に変更し、`thorough` 下で expert 実行を検証する
- `review-quality-expert-optional-for-small-fix`: 期待値を見直し、`thorough` 下では small fix でも expert review が実行されるシナリオに置き換える
- `review-quality-evaluation-summary`: quality summary バグ修正の回帰テストとして維持する

追加シナリオ:

- `standard` + config/chore で quality-review は実行されるが内部深度は Quick であること
- `thorough` + docs-only で quality-review が走らないこと

#### `tests/skills/scenarios/trigger-and-entrypoints.yaml`

次を追加または更新する。

- `深くレビューして` でも入口は `km:review`
- `浅くレビューして` でも入口は `km:review`
- 無指定レビューでも入口は `km:review`

必要に応じて expected metadata に selected level を追加する。

#### `tests/skills/manifest.yaml`

新規 scenario はすべて `manifest.yaml` に登録する。既存 scenario の ID を変更した場合も参照更新を忘れない。orphan scenario 検出があるため、ここは必須作業として計画に含める。

#### `tests/skills/rubrics/routing.md`

次を更新する。

- expert review の実行/スキップ条件にレベル次元を追加する
- 「変更タイプ routing をレベルが上書きしない」優先順位ルールを rubric に反映する

#### `tests/skills/rubrics/output-quality.md`

次を更新する。

- quality 評価サマリーの必須性を `thorough` / `standard` のみとする
- expert review セクションの必須性を `thorough` のみにする
- `quick` では quality summary が `（スキップ）` でよいことを許容する

#### 補助スクリプト

`scripts/verify-skill-tests.sh` が review skill の内容に依存する箇所を確認し、必要なら次を更新する。

- expert persona 数の前提は `thorough` でのみ必須であることを壊さない
- review skill が依然として workflow skill として auto-invocable であることを維持する
- README に invocation policy を過剰に書かないという既存ルールは維持する

### E. 実装制約の再確認

次の既存制約を破らない前提で実装する。

- `templates/AGENTS.md` と `templates/CLAUDE.md` の Skill 運用 bullet は完全一致を維持する
- `README.md` の skill list には `既定のレビュー入口` / `明示起動のみ` のような invocation policy 語を入れない
- `review` skill は workflow skill のまま維持し、`agents/openai.yaml` を追加しない
- `### 専門家の構成` セクションの persona 数は 2 のまま維持する
- scenario 追加時は `manifest.yaml` 登録を必須とする

## Public Contract

この変更後の `km:review` の公開契約は次で固定する。

1. `km:review` は review 系の既定入口であり続ける
2. レベル指定ができる
3. 無指定の既定レベルは `standard`
4. `thorough` は従来の strongest path を引き継ぐ
5. `standard` は日常利用向け
6. `quick` は最小レビュー向け
7. レベル差分はレポート上でも可視化される

## Acceptance Criteria

- `km:review` の説明と workflow が 3 レベル前提に更新されている
- 無指定レビューが `standard` として扱われる
- `thorough` のみ expert review を実行する
- `thorough` の fix でも expert review が常時実行される
- `standard` では quality-review は維持される
- `standard + test/config/chore` の内部深度は従来どおり Quick である
- `quick` では原則 code-review のみになる
- レベルは変更タイプ routing を上書きせず、絞り込み方向にのみ作用する
- docs-only + quick で docs 向け review が壊れない
- quality summary バグ修正後、`standard` / `thorough` で 9 特性テーブルが統合レポートへ出る
- report-format がレベル差分を表現できる
- scenario tests が新契約に追従している
- rubrics と manifest が新シナリオに追従している
- README / AGENTS / CLAUDE の説明が新契約と矛盾しない

## Risks And Mitigations

### Risk 1: `quick` の意味が曖昧になり、期待値がぶれる

対策:

- `quick` は「最小レビュー」と明記する
- 原則 code-review only、docs-only は doc-review 例外という形で仕様を固定する
- report-format にスキップ表示を残して、何をしていないかを明確にする

### Risk 2: 既存の「レビューして」でフルレビューを期待する運用が変わる

対策:

- `thorough` を明示的に用意し、必要なときは選べるようにする
- AGENTS / CLAUDE で「深く確認したい場合は深さ指定できる」と案内する
- この変更は `heavy by default` を `balanced by default` に変える設計判断として明記する

### Risk 3: 入口レベルと下位 skill の深度が混同される

対策:

- SKILL.md に「入口レベル」と「内部深度」を別概念として記載する
- 公開名に `Focused` を使わない
- 実装説明でも、入口レベルは routing、内部深度は per-skill execution だと明示する

## Assumptions

- `km:review` 自体の trigger は維持し、新しい別 skill は作らない
- 下位 review skill の manual-only 方針は変えない
- expert persona 構成は現行の 2 名を維持する
- `standard` は expert review 以外の既存レビュー価値をなるべく保つ
- docs-only の `quick` 例外は必要な仕様であり、実装時に再議論しない
