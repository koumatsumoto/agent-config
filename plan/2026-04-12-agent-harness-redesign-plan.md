# Agent Harness Simplification Plan

Updated: 2026-04-12

## Purpose

この文書は、`agent-config` リポジトリの Claude Code / Codex CLI 向け設定テンプレートを、過剰な抽象化や生成基盤を導入せずに改善するための実装計画である。

この計画では次を固定方針とする。

- `templates/` は引き続き正本とする
- `authoring/` や generator ベースの source/artifact 分離は導入しない
- 人間が `templates/` を直接読めば成果物と意図が分かる状態を維持する
- docs は参考資料として扱い、運用契約は template 側に寄せる

狙いは「構造を増やして解く」ことではなく、「既存構造の責務を明確にして drift を減らす」ことである。

## Executive Summary

現状の repo は、テンプレート主体のシンプルな構成を保ちながら、Claude / Codex 共通の skills・guidelines・install scripts を運用できている。ここは維持すべき強みである。

一方で、コードベース上で確認できる問題はある。

- README が quickstart・運用契約・参考情報を同時に持っている
- README の `## Codex 設定方針` には、profile 定義のような template 側と重複する内容と、`config.toml` の設計理由のような README 固有の説明が混在している
- README の skill 説明は一部で invocation policy を含み、[templates/AGENTS.md](/home/kou/projects/agent-config/templates/AGENTS.md) / [templates/CLAUDE.md](/home/kou/projects/agent-config/templates/CLAUDE.md) の `## Skill 運用` と責務が競合している
- `templates/AGENTS.md` と `templates/CLAUDE.md` の `## Skill 運用` セクションは一字一句同じであり、意図的重複なのか管理対象の重複なのかが未定義
- [templates/skills/review/SKILL.md](/home/kou/projects/agent-config/templates/skills/review/SKILL.md) の expert persona は存在するが、現状は 2 つの軽量定義しかなく、別ファイル化の必要性はまだ弱い
- `docs/` 配下の文書は、参考資料・歴史的メモ・規範的記述が混ざっており、どれが runtime contract なのかを曖昧にしている

したがって、この計画は以下に絞る。

1. README / `templates/AGENTS.md` / `templates/CLAUDE.md` の責務を明確化する
2. `AGENTS.md` ↔ `CLAUDE.md` 間の意図的重複を定義し、drift を管理対象にする
3. `km:review` は単一入口として維持し、expert persona の外出しは今回は見送る
4. docs はファイル単位で「残す / 縮退 / 削除 / 非規範化」を決める
5. install / verify / tests は既存資産を活かして最小限の補強だけ行う

## Non-Goals

今回やらないことを明確にする。

- `authoring/` の導入
- generator 前提の source/artifact 分離
- 大規模な build system の追加
- `templates/` 直編集の廃止
- install を manifest-driven framework に置き換えること
- reviewer persona を新しい agent framework や custom agent 群に展開すること
- docs を大規模な handbook に再編すること

## Design Principles

### 1. Templates Remain the Source of Truth

配布物と正本を分けない。

理由:

- `templates/` を読めば最終成果物そのものを確認できる
- レビュー時に source / generator / artifact の 3 層を追わずに済む
- この repo の価値は「すぐ読めるテンプレート集」であり、それを壊さない方が重要

### 2. Runtime Contracts Must Live Near Runtime Files

運用契約は配布されるファイルに置く。README と docs は説明補助に留める。

### 3. Intentional Duplication Is Acceptable When Self-Containment Matters

重複はすべて悪ではない。各 client の root instruction を単体で読んで意味が通ることには価値がある。その代わり、意図的重複は明示し、drift を検出する。

### 4. Do Not Introduce a New Abstraction Until the Current One Hurts

review persona のような軽量定義は、実害が出るまでインラインのまま維持する。抽象化は保守性改善が明確なときだけ行う。

## Current-State Diagnosis

### What Is Already Good

- [templates/AGENTS.md](/home/kou/projects/agent-config/templates/AGENTS.md) と [templates/CLAUDE.md](/home/kou/projects/agent-config/templates/CLAUDE.md) は短く、運用ポリシーが把握しやすい
- `km:review` を review の入口に寄せた設計は妥当
- [tests/skills/](/home/kou/projects/agent-config/tests/skills) に trigger / routing / workflow の回帰資産がある
- [install.sh](/home/kou/projects/agent-config/install.sh), [scripts/verify-install.sh](/home/kou/projects/agent-config/scripts/verify-install.sh), [clean.sh](/home/kou/projects/agent-config/clean.sh) は現状シンプルで理解しやすい
- docs に判断の背景が残っており、設計史を追える

### Problems Worth Fixing

#### A. README and templates compete for authority

[README.md](/home/kou/projects/agent-config/README.md) の以下は、README 固有の案内価値よりも runtime contract 寄りである。

- `## Codex 設定方針`（現行 107-124 行）のうち:
  - 109-117 行: `config.toml` の設計理由。README 固有の価値がある
  - 119-124 行: 推奨 profile 定義。`templates/AGENTS.md` と重複している
- `## スキル一覧` のうち invocation policy に踏み込む説明（現行 211-221 行）

一方、README 固有の価値が高い箇所も明確にある。

- `## 反映先マッピング`（現行 158-169 行）
- `## 公式仕様（参照元）`（現行 171-184 行）
- install / verify / clean の使い方

つまり README 全体が問題なのではなく、責務が混ざっているのが問題である。

#### B. `AGENTS.md` and `CLAUDE.md` have one intentional duplicate block that is currently undocumented

[templates/AGENTS.md](/home/kou/projects/agent-config/templates/AGENTS.md) 42-47 行と [templates/CLAUDE.md](/home/kou/projects/agent-config/templates/CLAUDE.md) 39-44 行の `## Skill 運用` セクションは一字一句同じである。

この重複は「両 client で同じ invocation policy を単体で読める」利点があるため、現時点では保持する価値がある。ただし、意図的であることが計画にも検証にも表れていない。

#### C. The “rules” naming collision is real but small

現状の [templates/rules/](/home/kou/projects/agent-config/templates/rules) は Claude 用 markdown rules 2 ファイルのみであり、構造変更の優先度は高くない。対応は README 上の用語注記で十分である。

#### D. `km:review` personas are too small to justify extraction

[templates/skills/review/SKILL.md](/home/kou/projects/agent-config/templates/skills/review/SKILL.md) 89-90 行にある expert persona は 2 つだけで、いずれも短い。

- セキュリティ専門家
- シニア QA アーキテクト

この規模では、supporting file や named role への切り出しは新しい抽象化コストの方が大きい。今回は見送る。

#### E. Docs need explicit file-by-file disposition

現状の docs は役に立つが、扱いを決めないと将来も規範文書のように読まれる。

対象ファイル:

- `docs/claude-code-best-practices-2026.md`
- `docs/typescript-best-practices-2026.md`
- `docs/python-best-practices-2026.md`
- `docs/20260315-templates-md-context-reduction.md`
- `docs/20260411-skill-authoring-review.md`
- `docs/claude-code-terminal-customization.md`

## Target State

### 1. README is a repository guide, not a behavior contract

README は次だけを担う。

- repo の目的
- 何がどこに配布されるか
- install / verify / clean の使い方
- 公式リンク集
- skill 一覧の簡潔な紹介
- `config.toml` の主要設定についての高レベルな設計理由

README は次を担わない。

- Codex profile の定義
- review / workflow skill の詳細な起動ポリシー
- Claude / Codex 各 client の行動契約

### 2. `templates/AGENTS.md` and `templates/CLAUDE.md` are the authoritative runtime contracts

- client 固有の行動契約は各 template に置く
- `## Skill 運用` セクションの重複は、現時点では意図的重複として維持する
- ただし template 本体には内部コメントを入れず、README・計画・検証側で drift 管理する

### 3. `km:review` remains the only review entrypoint, with personas kept inline

- `km:review` を単一入口として維持する
- expert persona は現状の 2 つをインラインのまま維持する
- docs-reviewer / config-reviewer など新しい persona は今回追加しない
- reviewer role の切り出しは、persona が肥大化した時点で再検討する

### 4. Docs become clearly non-normative or are removed

各 docs ファイルの扱いを事前に決める。

- `docs/claude-code-best-practices-2026.md`: 残す。reference-only にする
- `docs/typescript-best-practices-2026.md`: 残す。reference-only にする
- `docs/python-best-practices-2026.md`: 残す。reference-only にする
- `docs/claude-code-terminal-customization.md`: 残す。optional reference にする
- `docs/20260411-skill-authoring-review.md`: 残す。historical design note にする。live policy ではないと明記する
- `docs/20260315-templates-md-context-reduction.md`: 現行の live guidance と競合しやすいため、削除するか、最大 30 行程度の superseded stub に縮退する。実装では stub 化を推奨する

## Planned Changes

### A. Re-scope README

#### Remove or shrink

- `## Codex 設定方針`（現行 107-124 行）は一括削除しない
  - 109-117 行の `config.toml` 設計理由は残す
  - 119-124 行の `### 推奨 profile` は削除し、`templates/AGENTS.md` を参照する短い 1-2 行の案内に置き換える
- `## スキル一覧`（現行 211-221 行）は残すが、description は 1 行紹介に留める。`明示起動のみ`, `既定のレビュー入口`, `workflow skill` のような invocation policy 説明は削る

#### Keep

- `## 反映先マッピング`（現行 158-169 行）
- `## 公式仕様（参照元）`（現行 171-184 行）
- install / verify / clean の手順

#### Add

- `templates/rules/` は「現時点では Claude 用 markdown rules」であり、Codex `.rules` はまだこの repo の管理対象ではない、という 1 行の用語注記

### B. Keep `templates/AGENTS.md` stable

維持する内容:

- `### Profile の使い分け`
- `### 調査ルール`
- `### 実装ルール`
- `### レビューと完了`
- `### Skill 運用`

方針:

- 本体には internal note を追加しない
- `### Skill 運用` の intentional duplication は README / 計画 / 検証側で管理する

削る対象:

- なし。現状 47 行と短く、責務は適切

### C. Keep `templates/CLAUDE.md` stable

維持する内容:

- `### 1. 仕様の詳細化`
- `### 2. 実装`
- `### 3. リファクタリング`
- `### 4. レビュー`
- `### 5. 完了`
- `## Skill 運用`

方針:

- 本体には internal note を追加しない
- `## Skill 運用` の intentional duplication は README / 計画 / 検証側で管理する

削る対象:

- なし。現状 44 行と短く、README と異なり runtime contract として必要な密度である

### D. Keep `km:review` simple

今回は review persona をリファクタしない。これは独立した変更フェーズではなく、他フェーズで逸脱しないための制約として扱う。

- [templates/skills/review/SKILL.md](/home/kou/projects/agent-config/templates/skills/review/SKILL.md) の expert persona はインラインのまま維持する
- 新しい persona は追加しない
- reviewer supporting files ディレクトリは作らない
- `km:review` の行数は現状 146 行以下を維持するか、少なくとも増やさない

この項目は「新しい設計」を入れるフェーズではなく、「過剰抽象化を避ける」という制約を明文化するものである。

### E. Reduce docs with explicit dispositions

各ファイルの処遇を以下で固定する。

- `docs/claude-code-best-practices-2026.md`
  - Keep
  - 先頭に `Reference only. Not a runtime contract.` 相当の注記を追加
- `docs/typescript-best-practices-2026.md`
  - Keep
  - 先頭に reference-only 注記を追加
- `docs/python-best-practices-2026.md`
  - Keep
  - 先頭に reference-only 注記を追加
- `docs/claude-code-terminal-customization.md`
  - Keep
  - 先頭に optional reference 注記を追加
- `docs/20260411-skill-authoring-review.md`
  - Keep
  - historical design note として注記する
  - live policy は `templates/AGENTS.md`, `templates/CLAUDE.md`, `templates/skills/*`, `tests/skills/*` にあると明記する
- `docs/20260315-templates-md-context-reduction.md`
  - Shrink
  - 本文を短い superseded note に置き換えるか、別ファイルへ退避したうえで stub のみ残す
  - 参照先は `docs/20260411-skill-authoring-review.md` に統一する

### F. Keep install / verify / tests simple, but tie them to the new responsibility split

#### install.sh impact

- 今回の計画では `templates/` 配下の tree 構造を変えない
- reviewer supporting files を追加しないため、`sync_template_tree()` への構造的影響は発生しない
- `templates/AGENTS.md` / `templates/CLAUDE.md` の内容変更は、再インストール前には当然 drift として扱われる。これは正常な挙動であり、計画側で明記する

#### verify-install.sh impact

- 新しい tree を追加しないため、`scripts/verify-install.sh` の managed file scope は変更しない前提
- ただし Phase 1 実施後に `bash install.sh` と `bash scripts/verify-install.sh` を通して、template 更新が正常に配布されることを確認する

#### verify-skill-tests.sh / tests/skills impact

- 新しいテスト基盤は作らない
- 既存の `tests/skills/manifest.yaml`, `tests/skills/scenarios/`, `scripts/verify-skill-tests.sh` に追加する

## Implementation Phases

依存関係を先に固定する。

- Phase 1 は最初に実施する。README / AGENTS / CLAUDE の責務定義が後続フェーズの前提になるため
- Phase 2 は独立フェーズにしない。review persona の扱いは Phase 1 と Phase 4 の制約条件として扱う
- Phase 3（docs reduction）は、Phase 1 完了後に実施する
- Phase 4（verification updates）は Phase 1 と Phase 3 の内容確定後に実施する
- ただし install 影響確認は Phase 1 の直後にも実施する

### Phase 1: Responsibility Cleanup

対象:

- [README.md](/home/kou/projects/agent-config/README.md)
- [templates/AGENTS.md](/home/kou/projects/agent-config/templates/AGENTS.md)
- [templates/CLAUDE.md](/home/kou/projects/agent-config/templates/CLAUDE.md)
- 影響確認として [install.sh](/home/kou/projects/agent-config/install.sh) / [scripts/verify-install.sh](/home/kou/projects/agent-config/scripts/verify-install.sh)

作業:

- README の `## Codex 設定方針` を分割し、`config.toml` 設計理由は残しつつ、`### 推奨 profile` は削除して template 参照に置き換える
- README の skill 一覧から invocation policy 表現を削る
- README に `templates/rules/` の用語注記を追加する
- `templates/AGENTS.md` と `templates/CLAUDE.md` の `## Skill 運用` セクションは本文を変えずに維持し、README / 検証側で intentional duplication として扱う
- review persona に関しては新規ファイルや新 persona を追加しないことを確認する
- template 変更後に install / verify-install へ影響がないか確認する

完了条件:

- README に `config.toml` 設計理由を説明する短い節が残っている
- README から `### 推奨 profile` 見出しが消えている
- README の skill 一覧に `明示起動のみ`, `既定のレビュー入口`, `workflow skill` の文言がない
- `templates/AGENTS.md` と `templates/CLAUDE.md` の `## Skill 運用` セクションが引き続き同一である
- reviewer supporting files 用の新ディレクトリが存在しない
- `bash install.sh` と `bash scripts/verify-install.sh` が通る

### Phase 2: Docs Reduction

対象:

- [docs/claude-code-best-practices-2026.md](/home/kou/projects/agent-config/docs/claude-code-best-practices-2026.md)
- [docs/typescript-best-practices-2026.md](/home/kou/projects/agent-config/docs/typescript-best-practices-2026.md)
- [docs/python-best-practices-2026.md](/home/kou/projects/agent-config/docs/python-best-practices-2026.md)
- [docs/claude-code-terminal-customization.md](/home/kou/projects/agent-config/docs/claude-code-terminal-customization.md)
- [docs/20260411-skill-authoring-review.md](/home/kou/projects/agent-config/docs/20260411-skill-authoring-review.md)
- [docs/20260315-templates-md-context-reduction.md](/home/kou/projects/agent-config/docs/20260315-templates-md-context-reduction.md)

作業:

- 4 つの reference docs に non-normative 注記を追加する
- `20260411-skill-authoring-review.md` を historical note として明示する
- `20260315-templates-md-context-reduction.md` を superseded stub へ縮退する
- README から docs を runtime contract の根拠として読ませる表現を減らす

完了条件:

- 上記 5 ファイルの先頭に reference-only または historical note がある
- `20260315-templates-md-context-reduction.md` が短い superseded stub になっている

### Phase 3: Verification Updates

対象:

- [scripts/verify-skill-tests.sh](/home/kou/projects/agent-config/scripts/verify-skill-tests.sh)
- [tests/skills/manifest.yaml](/home/kou/projects/agent-config/tests/skills/manifest.yaml)
- [tests/skills/scenarios/workflow-and-state.yaml](/home/kou/projects/agent-config/tests/skills/scenarios/workflow-and-state.yaml)

作業:

- 既存の `docs-policy-drift` ケースを更新し、README から runtime contract を減らした後の期待値に合わせる
- 必要なら `tests/skills/scenarios/` に 1 ケース追加し、`AGENTS.md` ↔ `CLAUDE.md` の `Skill 運用` 一致を検証する
- `scripts/verify-skill-tests.sh` に以下の lightweight checks を追加する
  - `README.md` に `### 推奨 profile` 見出しが存在しない
  - `README.md` に `明示起動のみ` と `既定のレビュー入口` が skill 一覧説明として残っていない
  - `templates/AGENTS.md` と `templates/CLAUDE.md` の `## Skill 運用` セクションから「意図的重複」の注記行を除外し、残りの bullet 群を順序込みで比較する
  - bullet 数は固定値で持たず、抽出した bullet 配列同士の一致で検証する
  - review persona については、`templates/skills/review/SKILL.md` に numbered persona が 2 件あることだけを確認し、新ディレクトリ不在チェックと併用する

完了条件:

- `bash scripts/verify-skill-tests.sh` が新しい責務分離を検証する
- `tests/skills/manifest.yaml` に docs/policy drift 系ケースが維持または追加されている
- 追加検証は既存の test harness の中で完結している

## Test Plan

新しいテスト計画は、既存資産を拡張する形で定義する。

### 1. Existing script-based verification

- [scripts/verify-install.sh](/home/kou/projects/agent-config/scripts/verify-install.sh)
  - template 内容変更後に install 先への配布が期待通りか確認する
- [scripts/verify-skill-tests.sh](/home/kou/projects/agent-config/scripts/verify-skill-tests.sh)
  - 新しい責務分離と intentional duplication を機械検証する

### 2. Existing scenario framework

- [tests/skills/manifest.yaml](/home/kou/projects/agent-config/tests/skills/manifest.yaml)
  - docs/policy drift ケースの index として使う
- [tests/skills/scenarios/workflow-and-state.yaml](/home/kou/projects/agent-config/tests/skills/scenarios/workflow-and-state.yaml)
  - `docs-policy-drift` を更新し、README / AGENTS / CLAUDE の責務分離を反映する

### 3. Concrete checks to add

- README:
  - `config.toml` の設計理由は残る
  - `### 推奨 profile` がない
  - profile 定義は `templates/AGENTS.md` に委譲されている
  - skill 一覧は 1 行紹介に留まり、起動ポリシーを持たない
- AGENTS / CLAUDE:
  - `## Skill 運用` セクションが両方に存在する
  - bullet 配列が一致する
- Review:
  - `km:review` の expert persona は 2 つだけ
  - 新しい reviewer directory は追加されていない
- Docs:
  - 参考資料として残す文書には non-normative 注記がある
  - `20260315-templates-md-context-reduction.md` は superseded stub になっている

## Risks And Mitigations

### Risk: README cleanup removes too much context

Mitigation:

- `## 反映先マッピング`, `## 公式仕様（参照元）`, install / verify / clean の手順は README に残す
- `config.toml` の設計理由は README に残す
- 削る対象は `### 推奨 profile` と invocation policy 詳細に限定する

### Risk: Intentional duplication between AGENTS and CLAUDE drifts

Mitigation:

- この重複を計画上「意図的」と定義する
- `verify-skill-tests.sh` で section parity を検証する

### Risk: Reviewer abstraction creeps back in

Mitigation:

- 今回は reviewer supporting files を作らない
- 新 persona は追加しない
- 再検討条件は「persona が増える」「1 persona の定義が大幅に長くなる」のいずれかに限定する

### Risk: Docs still look authoritative

Mitigation:

- file 単位で non-normative / historical note を付ける
- runtime policy は template 側で完結させる

## Recommended First Slice

最初にやるべき実装は次の順がよい。

1. README から `## Codex 設定方針` と skill invocation policy 詳細を削る
2. `templates/AGENTS.md` と `templates/CLAUDE.md` の `Skill 運用` 一致を README / 検証側で管理前提にする
3. install / verify-install がその変更で壊れないことを確認する
4. docs の file-by-file disposition を反映する
5. `verify-skill-tests.sh` と `docs-policy-drift` ケースを更新する

理由:

- 最大の重複源である README ↔ template を、README 固有の設計理由は残しつつ整理できる
- `AGENTS.md` ↔ `CLAUDE.md` の重複を「管理対象の意図的重複」として固定できる
- review system は今回ほぼ現状維持なので、独立フェーズを立てずに制約として扱える

## Review Questions For Another AI

この計画を別 AI がレビューする場合、確認してほしい論点は以下。

1. README から削る対象と残す対象は十分具体的か
2. `AGENTS.md` ↔ `CLAUDE.md` の `Skill 運用` を意図的重複として維持する判断は妥当か
3. `km:review` の persona 外出しを今回は見送る判断は妥当か
4. docs の file-by-file disposition は妥当か
5. install / verify-install への影響分析は十分か
6. Test Plan は既存の `tests/skills/` / `verify-skill-tests.sh` を十分活用しているか

## Assumptions

- この repo は引き続き Claude Code と Codex CLI を両対応とする
- `templates/` を正本として維持する
- `templates/AGENTS.md` と `templates/CLAUDE.md` の一部重複は自己完結性のために許容する
- docs は削除または縮退しても runtime behavior に影響しない
- review の入口は `km:review` のままとする
