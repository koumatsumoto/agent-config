# Agent Harness Modernization Plan

Updated: 2026-04-12

> Note: この文書は一次情報の補助分析ノート。実行計画の正本は [plan/2026-04-12-agent-harness-redesign-plan.md](./2026-04-12-agent-harness-redesign-plan.md) とする。ここで挙げた論点のうち、低コストで有効なものだけを redesign-plan に取り込む。

## Purpose

Anthropic Claude Code と OpenAI Codex CLI の最新仕様を一次情報で再確認したうえで、`agent-config` の `templates/AGENTS.md`、`templates/CLAUDE.md`、`templates/rules/`、`templates/skills/` を改善するための実装計画をまとめる。

この計画は「文言を少し整える」段階ではなく、クロスクライアント運用で壊れやすい設計を減らし、保守しやすい instruction harness に寄せることを目的とする。

## Refreshed Inputs

2026-04-12 時点で以下を確認した。

- OpenAI Developers: Codex `AGENTS.md`, `rules`, `skills`, `config-reference`, `subagents`
- OpenAI Cookbook: Codex Prompting Guide (2026-02-25)
- Anthropic Claude Code Docs: `memory`, `slash-commands`, `sub-agents`, `hooks`
- ローカル実装:
  - `templates/AGENTS.md`
  - `templates/CLAUDE.md`
  - `templates/rules/*.md`
  - `templates/skills/**`
  - `tests/skills/**`
  - `.claude/skills/config-review/**`

## External Design Constraints

一次情報から、この repo が前提にすべき制約は次の通り。

1. `CLAUDE.md` / `AGENTS.md` は短い常設契約に寄せるべき
   - Claude Code は「常に必要な事実だけを書き、手順や部分コードベース固有の内容は skill か path-scoped rule に移す」方針を明示している。
   - Codex も `AGENTS.md` を root から cwd まで連結し、`project_doc_max_bytes` 上限内で扱うため、root 文書の肥大化は不利。

2. skill は「起動条件」と「実行契約」を分けて明示するべき
   - Claude は `description`、`disable-model-invocation`, `paths`, `context: fork`, `agent`, `allowed-tools`, `hooks` を前提に skill を制御する。
   - Codex は `description` と `agents/openai.yaml` の `allow_implicit_invocation` を使って暗黙起動を制御する。

3. Claude と Codex の subagent モデルは似ているが同一ではない
   - Claude は skill / subagent 定義側で fork 実行やツール制約を前提に書ける。
   - Codex は subagent workflow を標準搭載しているが、公式 docs は「明示的に依頼されたときだけ spawn する」としている。

4. shared skill に vendor-specific runtime syntax を埋め込むと移植性が落ちる
   - Claude は `!` command や skill-local hooks を持つ。
   - Codex docs には同等の `SKILL.md` inline shell syntax がない。shared skill にこれを直書きすると、片側だけに意味がある記法が残る。

5. harness は instruction quality だけでなく evalability が必要
   - OpenAI の prompting / eval guidance は、実行可能な手順、検証ループ、回帰評価を重視している。
   - この repo でも `tests/skills/` は既にあるが、現状は「現在の設計判断を固定する静的検査」が中心で、方針転換への追従性が弱い。

## Current-State Findings

### Finding 1: shared skill が本当の意味で shared ではない

`templates/skills/commit/SKILL.md` と `templates/skills/github-workflow/SKILL.md` は Claude 向けの `!` command syntax を使っている。一方で Codex 側では `agents/openai.yaml` による起動制御しか持たず、skill 本体は plain instruction として扱われる。

結果:

- Claude では runtime-assisted skill
- Codex では mostly prose instruction

という非対称状態になっている。

このズレは軽微な見た目の問題ではなく、再現性・テスト性・保守性を下げる。

### Finding 2: `km:review` の並列レビュー設計が Codex の最新 subagent 契約とずれている

`templates/skills/review/SKILL.md` は Phase 3-4 でサブエージェントを同時起動する前提を書いているが、Codex の最新 docs は subagent spawn を explicit ask 前提としている。

現状の問題は 2 つある。

- shared skill の本文が client 差を吸収していない
- `run_in_background: true` のような harness 依存の疑似 API が本文に残っている

このままだと、どの client でどこまで guarantee される挙動かが曖昧になる。

### Finding 3: workflow skill の auto-invocation 方針が安全性と衝突しやすい

`tests/skills/verify` 系は `commit`, `github-workflow`, `review` を auto-invocable として固定している。だが `commit` と `github-workflow` は git add / commit / push / PR 作成という明確な side effect を持つ。

現状でも自然言語起点の操作性は良いが、次のリスクがある。

- 曖昧な依頼文で workflow skill が発火しやすい
- review と publish の境界が skill metadata だけでは弱い
- 方針変更したい場合、静的検査が先にブロッカーになる

ここは「auto-invocable を絶対維持する」より、「どこまでを明示的要求とみなすか」を設計し直す方が健全。

### Finding 4: `AGENTS.md` / `CLAUDE.md` は短いが、instruction allocation policy がまだ弱い

両ファイルは比較的短く保たれている点は良い。ただし、最新 docs が強調する以下のルールが明文化されていない。

- root instruction に書くべき内容と書かない内容
- path-specific な知識は rules / nested instructions に逃がすこと
- multi-step procedure は skill に寄せること
- client ごとの override / layering を使って root を太らせないこと

今の内容は「運用ポリシー」にはなっているが、「instruction budget をどう守るか」の設計規律までは届いていない。

### Finding 5: `templates/rules/` は Claude 専用なのに、今後の Codex `.rules` と概念衝突しやすい

README には注記があるが、`templates/rules/` という名前だけを見ると「両 client 共通の rules repository」に見えやすい。最新の Codex `rules` は approval / sandbox 寄りの別概念であり、同名だが責務が違う。

現状ではまだ実害は小さいが、将来 `templates/codex-*` を追加すると混乱が起きやすい。

### Finding 6: test 資産はあるが、policy evolution への耐性が足りない

`tests/skills/` と `scripts/verify-skill-tests.sh` は価値が高い。一方で、現在の verifier は次のような「今の判断」を hard-code している。

- workflow skill は `agents/openai.yaml` を持たない
- workflow skill は auto-invocable のまま
- review persona は 2 つ固定

これでは設計変更を試すたびにテストが壊れる。必要なのは hard-coded policy ではなく、「policy manifest を正として検査する」方式である。

## Improvement Strategy

### Priority A: cross-client contract を分離する

最優先でやるべきことは、shared skill を「1 本の本文で両 client の runtime 差を隠す」設計から外すこと。

方針:

- `SKILL.md` は vendor-neutral な実行契約に寄せる
- Claude 固有機能は Claude 側 metadata / supporting file に分離する
- Codex 固有機能は `agents/openai.yaml` と Codex 向け supporting file に分離する

最低限の実装イメージ:

- shared `SKILL.md`: 目的、起動条件、手順、停止条件、出力契約
- Claude overlay: `disable-model-invocation`, `context`, `agent`, `allowed-tools`, `hooks`, `!` command を使うならここに閉じ込める
- Codex overlay: `agents/openai.yaml` と、必要なら Codex-specific instructions file

### Priority B: `km:review` を「概念上の orchestrator」と「client 実装」に分ける

`km:review` の本質はレビュー観点の orchestrator であり、parallel execution API ではない。

改善方針:

- `SKILL.md` 本文から harness 固有語を消す
- 「内部レビュー」「第三者レビュー」「doc review」の論理フェーズだけを残す
- 実行方式は client 別に記述する
  - Claude: forked subagents を使ってよい
  - Codex: explicit subagent request がある場合のみ subagents。そうでない場合は sequential fallback を正規経路にする

これにより、skill 本文が製品仕様変更に強くなる。

### Priority C: workflow skill の起動安全性を明示設計に変える

次の 3 択を比較したうえで、repo 方針として 1 つに固定する。

1. 現状維持
   - 利点: 自然言語で起動しやすい
   - 欠点: side effect workflow の誤起動リスクが残る

2. manual-only 化
   - 利点: 最も安全
   - 欠点: 現在の UX と互換性が落ちる

3. 条件付き auto-invocation
   - 利点: UX と安全性の折衷
   - 欠点: trigger 契約を厳密にテストする必要がある

推奨は 3。

具体策:

- `commit`: 「この変更をコミットして」「変更を保存して」のような明示要求のみ許可
- `github-workflow`: branch / push / PR の明示要求がある場合のみ許可
- それ以外の近接表現では、skill 発火前に clarification を要求する

### Priority D: root instructions に instruction allocation policy を追加する

`templates/AGENTS.md` と `templates/CLAUDE.md` の改善は、ルールを増やすことではなく、どこに何を書くかを明文化すること。

追加すべき要点:

- repo-wide で毎回必要な事実だけを書く
- file-type / subtree 固有の知識は `rules/` または nested instruction に移す
- multi-step procedure は `skills/` に置く
- root 文書が肥大化したら分解を優先する

これにより、今後の template 拡張で root guidance が再び太るのを防げる。

### Priority E: rules の責務命名を将来互換にする

すぐに directory rename までは不要だが、少なくとも設計文書と README では次を固定する。

- `templates/rules/` は Claude markdown rules のみ
- Codex `.rules` は別物であり、将来導入するなら別ディレクトリで持つ
- shared repository で generic 名称を使う場合は、責務注記を README だけでなく plan / tests にも入れる

将来的に Codex 側 rules を扱うなら、`templates/codex-rules/` のような分離を検討する。

### Priority F: tests を policy hard-code から policy-driven に変える

`scripts/verify-skill-tests.sh` と `tests/skills/` を、現在の判断を固定するものから、宣言的 policy manifest を検証するものへ進化させる。

案:

- `tests/skills/policy.yaml` を新設する
- skill ごとの属性を宣言する
  - invocation policy
  - side-effect level
  - client-specific metadata requirements
  - subagent allowance
- verifier はこの manifest を読んでチェックする

これで workflow skill の auto/manual 方針を変えても、コードに hard-code せずテストを更新できる。

## Proposed Work Plan

### Phase 1: contract inventory

対象:

- `templates/AGENTS.md`
- `templates/CLAUDE.md`
- `templates/skills/**`
- `tests/skills/**`

成果物:

- client-neutral contract と client-specific contract の棚卸し表
- Claude-only syntax / Codex-only metadata の一覧

完了条件:

- すべての skill について「shared / Claude-only / Codex-only」の境界が説明できる

### Phase 2: root instruction cleanup

変更方針:

- `templates/AGENTS.md` に AGENTS allocation policy を追加
- `templates/CLAUDE.md` に CLAUDE allocation policy を追加
- どちらにも「長くなったら rules / skills / nested docs へ逃がす」原則を入れる

完了条件:

- root instructions に procedure-heavy な追記を避ける明示規約が入る
- `Skill 運用` の重複は残す場合でも「意図的重複」の理由が説明できる

### Phase 3: skill contract split

変更方針:

- `commit`, `github-workflow`, `review` を優先対象にする
- shared `SKILL.md` から vendor-specific runtime syntax を減らす
- Claude / Codex 向け差分は metadata or supporting files に移す

完了条件:

- shared 本文に「片方だけで意味を持つ記法」が極力残らない
- `km:review` の本文から harness 固有 API 語が消える

### Phase 4: workflow safety redesign

変更方針:

- `commit` / `github-workflow` の起動条件を policy と tests で明文化する
- 必要なら `review` 完了確認、publish 前確認、既存 PR 再利用確認を stricter にする

完了条件:

- ambiguous prompt で workflow skill が走らない
- 明示要求では従来通り短手数で動く

### Phase 5: policy-driven verification

変更方針:

- `tests/skills/policy.yaml` を導入
- `scripts/verify-skill-tests.sh` の hard-coded assumptions を manifest 参照型に置き換える
- trigger / routing / safety を regression case 化する

完了条件:

- 設計変更時に verifier のコードを書き換えず policy 更新で追従できる
- auto/manual invocation の判断をテストで説明可能になる

## Explicit Non-Goals

- 今すぐ Codex 用 `.rules` を導入すること
- すべての skill を custom subagent / custom agent 化すること
- docs を全面再編して handbook 化すること
- Claude と Codex の差を完全に隠すこと

差は消すのではなく、正しい層に隔離する。

## Recommended First Slice

最初の 1 スライスは次に絞るのがよい。

1. `AGENTS.md` / `CLAUDE.md` に allocation policy を追加
2. `review`, `commit`, `github-workflow` の shared contract 見直し
3. `tests/skills/policy.yaml` の導入

この 3 つで、instruction budget、shared skill portability、workflow safety、test maintainability の主要リスクを同時に下げられる。

## Self-Review

### Coverage Check

- skills: covered
- rules: covered
- `AGENTS.md`: covered
- `CLAUDE.md`: covered
- tests / verification: covered
- cross-client differences: covered

### Risk Check

- 最新 docs 依存の論点を一次情報ベースに寄せた
- ローカル実装の具体的な壊れやすさに接続した
- 実装順序を small slice に分解した

### Remaining Uncertainty

- Claude 側で shared skill に vendor-specific frontmatter をどこまで混在させるのが保守上許容か
- Codex 側 workflow skill を最終的に auto / conditional / manual のどれで固定するか

この 2 点は実装前に方針決定が必要だが、どちらもこの計画で比較軸までは定義できている。

## Sources

- OpenAI: `https://developers.openai.com/codex/guides/agents-md`
- OpenAI: `https://developers.openai.com/codex/skills`
- OpenAI: `https://developers.openai.com/codex/rules`
- OpenAI: `https://developers.openai.com/codex/subagents`
- OpenAI: `https://developers.openai.com/codex/config-reference`
- OpenAI Cookbook: `https://developers.openai.com/cookbook/examples/gpt-5/codex_prompting_guide`
- Anthropic: `https://code.claude.com/docs/en/memory`
- Anthropic: `https://code.claude.com/docs/en/slash-commands`
- Anthropic: `https://code.claude.com/docs/en/sub-agents`
- Anthropic: `https://code.claude.com/docs/en/hooks`
