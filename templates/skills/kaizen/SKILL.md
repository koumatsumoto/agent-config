---
name: km:kaizen
description: 開発ループ中に気づいた改善点を .kaizen/ に記録する capture 規約と、蓄積した改善点を棚卸しして反映先へ振り分ける sweep を担う。「改善点を棚卸しして」「kaizen して」「ワークフローの改善点を振り返って」「/km:kaizen」など改善 backlog の棚卸し依頼で使う。開発中の改善メモ記録は km:github-workflow の Report から参照される。skill の改善検証は km:skill-improve、計画は km:plan、差分レビューは km:review の責務で、それらの起動語では発火しない。
argument-hint: "[topic]"
---

# Kaizen

開発ループ（issue → 計画 → 実装 → レビュー → PR）そのものを継続的に改善するため、作業中に気づいた改善点を蓄積し、種類別に正しい反映先へ届ける。改善点に「気づく」ことはモデル自身ができるので、本スキルが提供するのは観点コーチングではなく **置き場・反映先 taxonomy・畳み込みのライフサイクル** に限定する。

2 つの面を持つ:

- **面 1: Capture**（受動）— 作業中に気づいた改善点を `.kaizen/` に 1 行で残す規約。km:github-workflow の開発・報告 step から参照される
- **面 2: Sweep**（能動）— 蓄積した改善点を棚卸しし、傾向を集約して反映先へ振り分ける。`/km:kaizen` の明示起動で回す

## Context

- Repo: !`git rev-parse --is-inside-work-tree 2>/dev/null || echo "(not a git repo)"`
- `.kaizen/` entries: !`ls .kaizen/*.md 2>/dev/null || echo "(none)"`
- kaizen ラベル issue: !`gh issue list --label kaizen --state open --json number,title -q '.[] | "#\(.number) \(.title)"' 2>/dev/null || echo "(none or gh unavailable)"`

Context はロード時のスナップショット。sweep の実処理は下記手順で取り直す。

## 面 1: Capture 規約

作業中に改善点に気づいたら、その場で `.kaizen/` に 1 行残す。

- **置き場**: repo 直下 `.kaizen/YYYYMMDD-<slug>.md`（PR / セッション単位。slug は作業ブランチや話題から作る）。gitignore されている前提で扱い、確認・設定はしない
- **記法**: `- [YYYY-MM-DD] [dest] 症状 / 摩擦 → 改善案`（1〜3 行）。dest は下表の 4 種
- **原則**:
  - 気づいた時点で書く。会話 context に留めない（context 圧縮でメモが蒸発するのを防ぐ、即時ディスク化が capture の核心）
  - 改善点が無ければ何も書かない。「改善点: なし」の類を残さない（儀式化の禁止）
  - entry は後に公開 issue 本文へ昇格しうる。秘密情報を書かない（下の secret check 対象）

| dest | 意味 | 行き先 |
| --- | --- | --- |
| `pr` | 今回の作業に関係する改善 | 同じ PR で対応して entry を消す |
| `repo` | この repo のプロセス・CI・docs 等 | Report 時に kaizen ラベル付き follow-up issue へ昇格 |
| `workflow` | 共通ワークフロー資産（skill / rules / 共通方針ファイル） | `.kaizen/` に残置し、正本 repo での sweep で回収 |
| `knowledge` | 恒久知識・ドメイン知見 | 実際にロードされる資産へ fold（経路は下の triage で振り分け） |

dest は改善点の**反映先**を決めるものであって、「今 PR で直すべき欠陥を直す」義務を免除しない。ある気づきが出荷物の欠陥（バグ・セキュリティ欠陥）を示すなら、dest に関わらず同 PR で修正し、恒久知識としての記録（fold）や issue 化は修正に**追加して**行う（記録が修正の代わりにならない）。一つの気づきが「直すべき欠陥」かつ「残すべき知見」の二面を持つときは両方を実行する。

### Report 時の triage

km:github-workflow の報告 step から参照される。その PR の `.kaizen/` entry を dest 別に片付ける:

- **`pr`**: 対応済みを確認して entry を消す
- **`repo`**: kaizen ラベル付き follow-up issue へ昇格して URL を報告する（ラベルが無ければ `gh label create kaizen` で作成）。昇格後 entry を消す
- **`workflow`**: `.kaizen/` に残置し、残置した旨と件数を報告する（worktree 掃除で消えても人間が気づけるようにするセーフティネット）
- **`knowledge`**: fold 先で振り分ける（fold は知見の記録であって、その知見が示す欠陥の修正ではない。欠陥なら上記のとおり同 PR でも直す）
  - fold 先が当該 repo 内のロードされる資産（repo の方針ファイル / docs / skill 本文）なら、今回の作業に関係する場合は同じ PR で fold し、無関係なら `repo` と同様に follow-up issue 化する
  - fold 先が共通ワークフロー資産なら、**dest を `workflow` に付け替えて残置する**（残置 entry を `workflow` 1 種に正規化し、sweep の回収対象を単純に保つ）
- **一回限り・その日限りの事情**: 捨てる

改善点がゼロなら triage は何も報告しない（定型ノイズを出さない）。報告はユーザー向けの結果（何を直したか / どの issue を立てたか / どこに記録したか / 何を後続に残したか）で書き、`dest` / `残置` / `sweep` / `secret check` のような内部機構の語をそのままユーザー報告に持ち込まない。

## 面 2: Sweep（`/km:kaizen`）

改善 backlog の棚卸しセッション。任意の repo で実行でき、その repo の kaizen ラベル issue と `.kaizen/` 残置分を対象にする。skill / rules など**共通ワークフロー資産の正本 repo**（どの repo が正本かは利用者の文脈が決める）で実行したときだけ、他 repo の `.kaizen/` を横断回収する。

1. **収集**: 当該 repo の kaizen ラベル issue と `.kaizen/` 残置 entry を集める。横断回収は次の規約で行う:
   - **事前確認 gate**: 横断回収に入る前に「この repo を正本として、他 repo の `.kaizen/` から `workflow` 行き entry を回収・削除してよいか」をユーザーに確認する。repo 外への副作用と公開 issue 昇格を伴うため、文脈からの推測だけで実行しない
   - 承認後、`find ~ -maxdepth 2 -type d -name .kaizen` で他 repo の `.kaizen/` を探索し、`workflow` 行き entry を回収して正本 repo の kaizen ラベル issue に昇格する（secret check を通す）
   - 元 repo からの entry 削除（重複回収の防止）は、**issue 昇格の成功を確認してから**行う
   - 他 repo への読み書きが permission / sandbox で許可されない場合は縮退し、entry は残置のまま、スキャン結果（repo と件数）だけ報告する
2. **傾向分析**: 複数 PR・複数 repo 横断で同型の摩擦を集約する。**同じ型が 2 回以上現れたら rule / skill / チェックリスト化の候補**として恒久化を提案する（単発の摩擦は恒久化しない）
3. **fold 振り分け**: 反映先別に振り分ける
   - **skill の変更** → km:skill-improve へ handoff する。sweep 内で共有 skill を自分で編集して自己検証で採用しない（変更の検証・採用判定はあちらの責務。共有 skill は全 repo に波及するため、著者バイアスのない独立検証に載せる）
   - **共通方針ファイル / rules / repo プロセス** → 通常の issue → PR delivery（km:github-workflow）
   - **恒久知識** → 実際にロードされる資産へ fold
   - **価値を説明できないもの** → 棄却
4. **掃き出し**: 反映済み・棄却は issue close / entry 削除で片付ける。**backlog（kaizen ラベル issue と `.kaizen/`）は常に「未反映だけ」**を保つ

## Rules

- backlog（kaizen ラベル issue と `.kaizen/`）は常に「未反映だけ」を保つ。畳んだ / 棄却したものは issue close / entry 削除で掃き出す（判断の履歴は commit / issue に残り、backlog には残さない）
- `.plan/`（計画の一時作業場）と `.kaizen/`（改善メモの一時作業場）を混ぜない。改善メモを `.plan/` に書かない
- `KAIZEN.md` / `KNOWLEDGE.md` のような集約ファイルを作らない。恒久知識は実際にロードされる資産へ畳み、畳み先の無い知識は捨てる（自動ロードされないファイルに溜めた知識は死蔵する）
- 「こういう観点で改善点を探せ」式のコーチングを書かない。capture は気づきの永続化とルーティングに徹する
- issue 昇格の全経路（Report triage・sweep 横断回収）で secret check を通す。判定対象は credential / token 類に加え、**実在の個人パス・非公開 repo 名・個人環境の識別子**を含む（entry の症状記述に混入しやすい）
- gitignore の確認・編集はしない

## 責務の境界

- **km:skill-improve**: skill 変更の A/B 運用テスト・採用判定を担う。sweep で skill 変更を fold すると決めたら、検証はこちらへ handoff する。本スキルは検証・採用判定のロジックを持たない
- **km:plan**: 計画の一時作業場は `.plan/`、改善メモの一時作業場は `.kaizen/`。両者を混ぜない
- **km:review**: レビュー中に気づいた改善点も capture 規約（面 1）に流す。ただしレビューの合否判定・指摘の反映には関与しない（それは km:review の責務）
