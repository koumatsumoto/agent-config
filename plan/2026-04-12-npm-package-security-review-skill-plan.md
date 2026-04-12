# npm Package Security Review Skill v1 Plan

## Summary

- v1 は、単一 npm package の社内採用前レビューを行う manual-only の specialized review skill として実装する
- 成果物は skill 本体、最小限の reference、レポート形式、Codex metadata、README のスキル一覧追記、skill test scenario 追加に限定する
- 出力は日本語の固定レポートのみとし、構造化 JSON、採点スクリプト、証跡収集スクリプト、fixture/snapshot、CI 組み込み、動的解析は v1 の対象外とする
- この skill は `km:review` のルーティング対象外とし、package 採用レビューを明示的に依頼されたときだけ使う

## Design Decisions

- specialized review skill として分離する  
  理由: 通常のコードレビュー要求と混ぜると誤起動しやすく、package 採用判断は入力、外部調査、出力形式、人間承認の前提が大きく異なるため
- manual-only にする  
  理由: package 採用レビューは意図が明確なときだけ使うべきで、汎用の「レビューして」から自動起動させる価値より誤反応のコストが大きい
- v1 では blocker-based decision を採用し、数値スコアは導入しない  
  理由: 初版で重要なのは説明可能な停止条件の統一であり、数値スコアは weight 調整、例外処理、unknown の扱いを増やしすぎるため
- GitHub URL は必須入力にしない  
  理由: npm package review の自然な最小入力は `package@version` と利用文脈であり、repository は npm metadata から辿るのが標準的だから
- package の install / execution は禁止する  
  理由: skill 自身が副作用や任意コード実行の入口にならないようにし、初版の安全性と再現性を優先するため
- 一次情報のみを根拠に使う  
  理由: advisory、release、maintainer activity、repository 状態は変化するため、最新確認が必要な review では cached な知識に依存できない
- 最終レポートは日本語固定にする  
  理由: 社内レビューの一次資料としてそのまま共有しやすく、判断理由・条件付き許容・未確認事項を読み手が追いやすいから
- `ALLOW` は厳格に制限する  
  理由: 危険な package に誤って `ALLOW` を出すのがこの skill の最大リスクだから

## Deliverables

- `templates/skills/npm-package-security-review/SKILL.md`
- `templates/skills/npm-package-security-review/reference/review-checklist.md`
- `templates/skills/npm-package-security-review/reference/decision-rules.md`
- `templates/skills/npm-package-security-review/report-format.md`
- `templates/skills/npm-package-security-review/agents/openai.yaml`
- `README.md` のスキル一覧 1 行追加
- `tests/skills/scenarios/trigger-and-entrypoints.yaml` への trigger case 追加
- `tests/skills/scenarios/review-quality.yaml` への output/decision case 追加
- `tests/skills/manifest.yaml` への case 登録

## Skill Contract

- skill 名は `km:npm-package-security-review`
- `description` のドラフトは次とする  
  `Reviews a single npm package for internal adoption risk. Use when a package or package@version is identified and you need a security-focused intake review before approval.`
- Claude 側は `disable-model-invocation: true`、Codex 側は `agents/openai.yaml` で `allow_implicit_invocation: false` を設定する
- `argument-hint` は `"[package[@version]]"` とする
- scoped package は許容する  
  例: `@angular/core@18.0.0`、`@scope/pkg`
- 最小入力は `package_name` または `package_name@version`
- 次の情報が不足する場合のみ確認する
  - exact version
  - 利用文脈
    - `production` / `development`
    - 主な runtime: `node-server` / `browser` / `cli` / `build-tool` / `test-tool` / `ci`
    - `secrets_access`
    - `data_sensitivity`: `low` / `medium` / `high`
  - 社内ポリシー要点
    - install scripts の扱い
    - 禁止ライセンス
    - 未メンテ許容期間など
- version 未指定時は latest を暗黙採用せず、exact version を確認する  
  理由: `ALLOW` / `REJECT` の根拠が version に強く依存するため

## Workflow Design

- `SKILL.md` は既存 review skill と同様に Phase 構造で記述する
- Phase 1: 入力確認
  - `package_name` または `package@version` を解釈する
  - scoped package を正しく扱う
  - exact version がない場合は確認し、揃うまで `ALLOW` 判定に進まない
  - 利用文脈と社内ポリシー要点が不足していれば追加確認する
- Phase 2: 一次情報の収集
  - npm registry / npm package page で package metadata を確認する
  - npm metadata の repository / homepage / publisher 情報から GitHub repository を特定する
  - repository が特定できたら GitHub 上の release、commit、SECURITY.md、CI 状態を確認する
  - advisory 情報を確認する
  - 外部ソースの取得失敗、repository 不在、rate limit、応答不整合があれば `unknown` として記録し、必要に応じて `NEEDS_HUMAN_REVIEW` に倒す
- Phase 3: 7 観点の評価
  - `reference/review-checklist.md` に沿って
    - identity / provenance
    - known vulnerabilities
    - install / runtime behavior
    - maintainer / repo health
    - dependency surface
    - license / policy fit
    - usage-context impact
    を確認する
- Phase 4: 判定
  - `reference/decision-rules.md` に沿って blocker を先に判定する
  - blocker がなければ `ALLOW_WITH_CONDITIONS` / `ALLOW` を検討する
  - production、`secrets_access=true`、`data_sensitivity=high` の場合は同じ信号でも一段厳しく扱う
- Phase 5: レポート生成
  - `report-format.md` に沿って日本語レポートを出力する
  - 判定理由、主要指摘、証跡 URL、絶対日付、未確認事項を必ず含める

## Evidence Sources And Collection Rules

- npm 情報は npm registry または npm package page の一次情報を使う
- repository 情報は GitHub repository の公開ページを第一候補にし、必要に応じて GitHub API 相当の一次情報を使う
- advisory 情報は GitHub Security Advisories を第一候補とし、必要に応じて npm advisory 系の一次情報で補完する
- 取得手段は skill 実行環境の browse / fetch capabilities を優先し、`gh` コマンドや package install には依存しない  
  理由: この repo の skill は端末依存コマンドより、モデルが読める一次情報ソースへの誘導を優先するため
- ソース間に不整合がある場合は、値を統合して確定させず不整合自体をレポートする
- 外部ソース障害時の扱いは次で固定する
  - npm metadata が取れない: `NEEDS_HUMAN_REVIEW`
  - repository が存在しない、またはリンク解決できない: `NEEDS_HUMAN_REVIEW` 以上
  - advisory source が取得不能: `ALLOW` は出さない
  - 一部証跡のみ取得失敗: `unknown` として残し、判定への影響を明記する

## Decision Rules

- `reference/decision-rules.md` は次の 4 判定だけを定義する
  - `ALLOW`
  - `ALLOW_WITH_CONDITIONS`
  - `NEEDS_HUMAN_REVIEW`
  - `REJECT`
- `ALLOW`
  - exact version 解決済み
  - package と repository の対応確認済み
  - Critical / High の未解決 advisory なし
  - 明確に危険な install/runtime 挙動なし
  - org policy 違反なし
  - 主要 unknown なし
- `ALLOW_WITH_CONDITIONS`
  - 明確な blocker はない
  - ただし version pin、dev-only 限定、install scripts 無効化、用途制限、追加監視など運用条件が必要
- `NEEDS_HUMAN_REVIEW`
  - 証跡不足
  - package と repository の対応が曖昧
  - 外部ソース障害で主要信号が欠落
  - 利用文脈依存の高トレードオフ
  - 権限やデータ影響が大きく画一判断できない
- `REJECT`
  - org policy 違反
  - 未解決 Critical advisory
  - 明確に危険な install/runtime 挙動
  - 信頼できない provenance
- `ALLOW` の hard rule
  - version 未特定では出さない
  - package / repository 対応が曖昧なら出さない
  - advisory source 未確認では出さない
  - 主要 unknown が残るなら出さない
  - production / `secrets_access=true` / `data_sensitivity=high` の場合は保守的に倒す

## Report Requirements

- レポートは日本語で出力する
- `report-format.md` は次の必須セクションを定義する
  - `レビュー対象`
  - `利用文脈`
  - `最終判定`
  - `主要な判断理由`
  - `カテゴリ評価`
  - `主要な指摘`
  - `必要条件`
  - `人間確認が必要な点`
  - `主要な証跡`
  - `不確実性 / 未確認事項`
- 冒頭サマリーは package 名、version、repository、最終判定、review confidence を含める
- 判定理由は 2-4 点に絞り、各点に根拠を添える
- 各主要指摘は `重大度`、`観点`、`問題`、`根拠`、`推奨対応` の形式に固定する
- 証跡は URL と絶対日付付きで列挙する
- 断定的な安全保証表現は禁止し、「確認できた範囲では」と「未確認事項」を分ける
- `ALLOW_WITH_CONDITIONS` では条件を実施可能な文で書く
  - 例: `version を 1.2.3 に固定する`
  - 例: `本番依存ではなく devDependency に限定する`
  - 例: `install scripts を無効化できる環境でのみ使う`
- `NEEDS_HUMAN_REVIEW` では、何が不足していて誰が確認すべきかを明示する
- `REJECT` では、拒否理由を `policy` / `vulnerability` / `provenance` / `behavior` のいずれかに分類する

## Test Plan

- scenario の配置は既存パターンに合わせる
  - trigger case は `tests/skills/scenarios/trigger-and-entrypoints.yaml` に追記する
  - output / decision case は `tests/skills/scenarios/review-quality.yaml` に追記する
  理由: 既存のテスト資産は関心事別に編成されており、新 skill だけ別ファイルにすると一貫性が落ちるため
- `tests/skills/manifest.yaml` の追加エントリには tags を明記する
  - trigger case: `[trigger, review, npm]`
  - decision / output case: `[quality, review, npm]`
  - install verify case を追加する場合: `[workflow, docs, npm]` ではなく `[workflow, install, npm]`
- シナリオは次の 6 件に固定する
  1. 明示的な npm package 採用レビュー依頼で `km:npm-package-security-review` が入口になる
  2. 汎用の「レビューして」ではこの skill が入口にならない
  3. exact version がない場合に `ALLOW` を出さない
  4. package / repository 対応が曖昧な場合に `ALLOW` を出さず、`NEEDS_HUMAN_REVIEW` 以上に止める
  5. 未解決 Critical advisory または禁止ライセンスで `REJECT` になる
  6. 出力が日本語で、必須セクション・判定理由・証跡 URL・絶対日付を欠かない
- 追加の検証として、`install.sh` と `scripts/verify-install.sh` により新 skill が `~/.claude/skills/` と `~/.agents/skills/` に同期される前提を確認する  
  理由: 既存スクリプトは `templates/skills` を木ごと同期するためコード変更は不要だが、新ディレクトリ追加が実際に managed tree として検証されることは acceptance に含めるべきだから
- v1 の検証は既存の skill test kit に合わせた scenario ベースの手動検証を基本とする
- rubric の追加は、既存 rubrics で manual-only / output contract / policy drift を表現できない場合のみ行う

## Assumptions

- 対象は単一 npm package の採用前レビューのみで、PR 差分レビューや継続監視は扱わない
- version は exact version を原則とし、range 指定だけでは `ALLOW` を出さない
- 社内ポリシーは固定 schema ではなく、skill 実行時に与える要点として扱う
- GitHub repository は npm metadata から導出するのを既定とし、曖昧な場合はユーザー確認を優先する
- 判定は最終承認ではなく一次レビューであり、判断不能時は安全側に倒して `NEEDS_HUMAN_REVIEW` を使う
