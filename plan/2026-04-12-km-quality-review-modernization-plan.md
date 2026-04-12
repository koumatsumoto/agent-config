# `km:quality-review` Modernization Plan

Updated: 2026-04-12

## Summary

`km:quality-review` を **ISO/IEC 25010:2023 を主軸にした汎用品質レビュー skill のまま維持**しつつ、**Web アプリケーション / HTTP API / 分散システム / クラウド運用**の現代的なレビュー観点を各品質特性に接続する。

今回の狙いは、品質モデルそのものを変えることではなく、**既存チェック項目の棚卸しを前提に、品質特性ごとのリファレンスとチェック観点を現代の実装リスクへ再接続すること**にある。

結論としては、次の方針で進める。

- `km:quality-review` は汎用 skill のままにする
- Web / API / distributed system の観点は、新しい独立軸ではなく、既存の **実務補助マーカーを formalize した surface 条件付き補助観点** として扱う
- 外部標準は長い説明ではなく、**標準マップ** として各特性に紐づける
- checklist は判断インデックスに寄せ、詳細化は reference に逃がす
- diff から裏づけられない一般論の指摘を増やさないよう、false positive 抑制ルールを明文化する

## Problem Statement

現行の [templates/skills/quality-review/SKILL.md](/home/kou/work/agent-config/templates/skills/quality-review/SKILL.md) と [quality-checklist.md](/home/kou/work/agent-config/templates/skills/quality-review/quality-checklist.md) は、すでに ISO/IEC 25010:2023 の 9 品質特性に沿って構成されている。構造自体はよい。

ただし、現状の弱さは次の 4 点にある。

1. 必要な観点のかなりの部分は、すでに checklist に存在する
   - 問題は「欠けていること」そのものより、**新規項目、補強項目、再配置項目の区別が曖昧**なことにある
2. Web 固有や運用固有の観点は「実務補助」として散発的にあるが、条件の表現が不均一である
   - その結果、見落としも過剰指摘も起きうる
3. checklist が毎回必ず読まれるファイルであるのに対し、役割境界がやや広く、今後の肥大化リスクがある
4. 参照ファイル群に「この観点はどの標準や実務知見を下敷きにしているか」の対応づけがない
   - そのため、レビューの判断根拠を別 AI や人間が追いにくい

今回の改善では、この 4 点を解消する。

## Goals

- ISO/IEC 25010:2023 の 9 品質特性を維持したまま、現代の Web / API / distributed system 開発に強い観点へ更新する
- `quality-checklist.md` を、過度に肥大化させずに「何を見るか」「いつ見るか」を判断できるインデックスにする
- `reference/` 配下の 9 ファイルを、品質特性ごとの **判断辞書** として使いやすくする
- 別 AI や人間レビューアが「その観点を採用した理由」を追えるようにする
- diff ベースレビューの精度を上げつつ、一般論によるノイズを増やさない

## Non-goals

- ISO/IEC 25010:2023 の品質特性そのものを別モデルへ置き換えること
- `km:quality-review` を Web 専用 skill に変えること
- 長い教科書的解説を skill 本体に埋め込むこと
- 実装 lint ルールや CI policy の全面設計まで同時にやること

## Design Direction

### 1. 汎用 skill を維持し、Web 観点は既存の「実務補助」を正式化する形で扱う

採用判断:

- `km:quality-review` は `km:review` の下位 skill であり、Web 以外のコードや設定変更もレビュー対象になる
- そのため「Web 中心に再定義」すると既存の汎用性を崩しやすい
- 一方で、現代の主要な開発対象が Web / API / cloud runtime に寄っているのも事実なので、そこを無視すると精度が伸びない

固定方針:

- 主軸は ISO/IEC 25010:2023
- 新しい第 4 の判定軸は増やさない
- 現行の `実務補助` マーカーを、**surface 条件付き補助観点** として統一する
- surface は次で固定する
  - `Web / Browser`
  - `HTTP API`
  - `async job / queue`
  - `external integration`
  - `database / data store`
  - `cloud runtime / IaC`
  - `CLI / developer tool`
  - `AI/LLM`
- `cloud runtime / IaC` には k8s manifest, Terraform, deployment config を含める
- 変更に該当 surface がある場合だけ、その補助観点を強く見る

意図:

- 品質モデルの安定性と、現場でのレビュー命中率を両立する

### 2. 判定メカニズムは Tier → Depth → surface 条件付き項目 の 3 層に整理する

現状課題:

- `Tier`, `Depth`, `実務補助` の既存メカニズムに、独立した `change surface` を足すと 4 重管理になる
- それぞれの優先順位が未定義だと、Quick や Tier 2 SKIP で矛盾が出る

固定方針:

- 判定順序は次で固定する
  - `Tier`: どの品質特性を見るか
  - `Depth`: どの深さで見るか
  - `surface 条件付き補助観点`: その品質特性の中で、どの補助観点を有効化するか
- `Tier 2` の SKIP 条件は surface 条件に優先する
- `Quick` 深度では surface 条件付き補助観点も簡略化し、既存の Quick 優先観点を壊さない
- `Quick` での簡略化は「一切見ない」ではなく、「実害に直結する補助観点だけを最小限見る」を意味する
- 既存の `ブラウザセキュリティ（実務補助、Web 変更がある場合のみ）` のような記法を、同じルールで全体に揃える

意図:

- 条件メカニズムを増やさずに、適用条件を明確化する

### 3. 標準への対応は本文展開ではなく「標準マップ」で示す

採用判断:

- Skill 本体や reference に長い標準解説を書くと冗長になる
- ただし、どの観点がどの標準や一次情報に基づくかは残したい

固定方針:

- 各 reference ファイル末尾に短い `標準マップ` を追加する
- 形式は「副特性 or 補助観点」と「参照標準」の対応表に留める
- 本文は diff レビュー向けの実務的な観点記述に集中させる

意図:

- レビュー根拠を示しつつ、token/文量コストを抑える

### 4. checklist は軽く保ち、詳細は reference に委譲する

現状の `quality-checklist.md` は SKILL 契約上「必ず Read する」ファイルであり、ここを肥大化させると毎回の負荷が上がる。

固定方針:

- checklist には次だけを書く
  - 何を見るか
  - どの条件で見るか / 見ないか
  - 判断に迷ったらどの reference を読むか
- checklist に詳細な説明、長い補助観点列挙、具体例を持ち込みすぎない
- 詳細な確認パターン、surface 別の補助観点、false positive 注意は reference に寄せる

意図:

- 毎回読むファイルをインデックスに保ちつつ、必要なときだけ深掘りできる構造にする

### 5. false positive 抑制を skill 契約として強化する

現状のルールでも「diff から裏づけられない推測」は除外対象だが、現代的な標準観点を足すと一般論が増えやすい。

固定方針:

- 次は明示的に除外ルールへ追加する
  - surface が存在しないのに、その補助観点を機械的に適用する指摘
  - Tier 2 で SKIP 条件に該当する特性に対し、surface を理由に無理に指摘すること
  - インフラや運用構成が diff にないのに、一般的ベストプラクティスだけで断定する指摘
  - 「本番ではこうすべき」という抽象論だけで、今回の変更に結びつかない指摘

意図:

- 観点の近代化によって、レビューが雑になることを防ぐ

## Source Basis

今回の観点補強で参照する主要な一次情報は次のとおり。

- ISO の公開ページ上で、`ISO/IEC 25010:2011` は withdrawn、`ISO/IEC 25010:2023` が current な版として案内されている
- W3C の WCAG Overview 上で、`WCAG 2.2` は 2023-10-05 Recommendation として示され、W3C は最新の WCAG 使用を推奨している
- OWASP API Security Top 10 2023 は、`BOLA`、`Unrestricted Resource Consumption`、`Unsafe Consumption of APIs` など、現代 API で見落としやすい観点を整理している
- Kubernetes documentation は `startup` / `readiness` / `liveness` probe の役割分離を定義している
- OpenTelemetry documentation は context propagation と telemetry correlation を明示している
- RFC 9457 は HTTP API の Problem Details 形式を定義している
- RFC 9111 は HTTP caching の現行標準
- Twelve-Factor App は config の環境分離原則を整理している
- Sigstore documentation は transparency log / signing / provenance の実務基盤を説明している

これらは skill 内の「標準マップ」の根拠として使い、本文ではレビュー観点に翻訳した要約だけを置く。

## Proposed File Changes

### A. `templates/skills/quality-review/SKILL.md`

変更内容:

- Success Criteria は大枠維持する
- Workflow に `surface 条件付き補助観点` の扱いを追加する
- `quality-checklist.md` の読み方を、単なる順番確認から「Tier → Depth → surface 条件付き補助観点」の順に確認する形へ更新する
- `reference/` の読み分け方を明文化する
- false positive 除外ルールを強化する

具体的に追加する要素:

- `surface` の定義
  - `Web / Browser`
  - `HTTP API`
  - `async job / queue`
  - `external integration`
  - `database / data store`
  - `cloud runtime / IaC`
  - `CLI / developer tool`
  - `AI/LLM`
- それぞれに対し、優先的に見る品質特性を軽く案内する
- 例:
  - `HTTP API`: セキュリティ、信頼性、互換性、機能適合性
  - `Web / Browser`: インタラクション能力、性能効率性、セキュリティ
  - `database / data store`: 互換性、信頼性、性能効率性、安全性
  - `cloud runtime / IaC`: 信頼性、柔軟性、安全性
- 上記は代表例であり、`async job / queue`、`external integration`、`CLI / developer tool`、`AI/LLM` は該当する reference の補助観点に従って実装時に判断する
- 優先順位ルール
  - Tier 2 の SKIP 条件が先
  - Depth が次
  - surface 条件付き補助観点は最後

意図:

- 同じ 9 品質特性でも、変更の種類によって見るべき観点の濃淡が違うことを、既存メカニズムを壊さずに明示する

### B. `templates/skills/quality-review/quality-checklist.md`

変更内容:

- checklist は判断インデックスに寄せ、詳細な補助観点は reference に逃がす
- 各品質特性セクションでは、必要最小限の `見る条件` と `見送り条件` を追加する
- Tier 1 / Tier 2 / Tier 3 の構造は維持する
- 変更項目は、`新規追加`, `補強`, `再配置` の 3 種に再分類して扱う

再分類の方針:

- 新規追加
  - `BOPLA / property-level authorization`
  - `retry budget`
  - `degraded mode`
  - `HTTP caching`
  - `Problem Details (RFC 9457) 互換`
  - `contract test`
  - `observability-driven diagnosability`
  - `WCAG 2.2` の明示的フレーミング
- 補強
  - `startup / readiness / liveness` の役割分離
  - `streaming / incremental delivery` を delivery 観点で明確化
  - `Core Web Vitals` を UI 変更時の性能観点として整理
  - `artifact provenance / dependency trust`
  - AI/LLM の構造化入力と tool 実行境界
- 再配置
  - `unsafe consumption of APIs` を `安全性 > 安全な統合` だけでなく `セキュリティ` にも接続
  - webhook / callback の契約・署名観点を `セキュリティ`, `安全性`, `互換性` の接続点として整理
  - CLI / developer tool 変更時のインタラクション能力適用を明示する

意図:

- 「既存項目の焼き直し」を避け、真に必要な追加だけを見極めたまま checklist の肥大化を防ぐ

### C. `templates/skills/quality-review/reference/*.md`

変更内容:

- 9 ファイルすべてを同一テンプレートで書き直す

テンプレート:

- 導入 1-2 行
- 副特性ごとの `アンチパターン + diff シグナル`
- surface 条件付き補助観点
- false positive 注意
- 標準マップ

この簡素化を行う理由:

- 今はファイルごとに粒度が少しずつ異なる
- 参照時に「どこを見ればよいか」が一定でない
- 別 AI がレビューする際も、構造が揃っていた方が比較しやすい
- `シグナル` と `アンチパターン`、`推奨確認` の重複を避けられる

重点更新ファイル:

- [reference/6-security.md](/home/kou/work/agent-config/templates/skills/quality-review/reference/6-security.md)
  - authorization 系と API consumption 系を強化する
- [reference/5-reliability.md](/home/kou/work/agent-config/templates/skills/quality-review/reference/5-reliability.md)
  - operational reliability を強化する
- [reference/4-interaction-capability.md](/home/kou/work/agent-config/templates/skills/quality-review/reference/4-interaction-capability.md)
  - WCAG 2.2 ベースの UI 行動観点を強化する
- [reference/8-flexibility.md](/home/kou/work/agent-config/templates/skills/quality-review/reference/8-flexibility.md)
  - config / scalability / replaceability を現代化する

### D. `templates/skills/quality-review/report-format.md`

変更内容:

- 9 特性テーブル自体は維持する
- 所見の文体に「何を根拠にそう判断したか」を少なくとも 1 文入れる方針を明示する
- 必要に応じて、所見内で `主要レンズ` を短く示せるようにする

例:

- `セキュリティ | WARN | HTTP API の所有者検証が差分上で確認できず、BOLA 観点で未防御の可能性がある。入力バリデーション自体は適用済み`
- `信頼性 | WARN | 外部 API 呼び出しに timeout はあるが retry/backoff と idempotency 方針が差分から確認できない`

意図:

- PASS / WARN / FAIL の理由を、人間と別 AI が短時間で追えるようにする

### E. `tests/skills/*`

変更内容:

- [tests/skills/scenarios/review-quality.yaml](/home/kou/work/agent-config/tests/skills/scenarios/review-quality.yaml) に、現代的観点の期待ケースを追加する
- [tests/skills/rubrics/output-quality.md](/home/kou/work/agent-config/tests/skills/rubrics/output-quality.md) に、false positive 抑制の評価基準を追記する

追加すべきシナリオ:

- surface が複数該当する変更で、補助観点の組み合わせが暴発しないこと
- `Quick` depth でも surface 条件付き補助観点が簡略化されること
- Tier 2 の SKIP 条件が surface 条件に優先すること
- 既存 false positive シナリオが維持されること
- API の object-level authorization 不備
- 外部 API 呼び出しの timeout / retry / idempotency 不備
- readiness/liveness/startup 観点の不足
- UI 変更時の WCAG 2.2 観点
- `dangerouslySetInnerHTML`, CORS, Cookie, CSP など browser boundary 問題
- エラー形式や Problem Details 互換の破壊的変更
- database / migration 変更で `database / data store` 補助観点が発火すること
- config-only 変更で柔軟性 / 安全性 / 信頼性が優先されること
- 非 UI 変更で a11y 指摘が暴発しないこと

rubric に追加する観点:

- 標準観点を導入しても、diff 根拠の弱い一般論を増やしていないか
- surface 条件がないのに Web 固有指摘をしていないか

## Characteristic-by-Characteristic Intent

### 機能適合性

改善意図:

- 「仕様どおり動くか」だけでなく、現代 API や運用機能で必要な情報が欠けていないかを見る
- 特に部分失敗、列挙値追加、理由コード、メタデータ欠落を、既存項目の補強として拾いやすくする

### 性能効率性

改善意図:

- 単純なアルゴリズム問題だけでなく、HTTP / UI / async processing のボトルネックに当てる
- 実装差分で拾える caching, streaming, connection reuse, rerender を、既存項目への補強として重視する

### 互換性

改善意図:

- 公開 API や callback 契約、エラー形式の破壊的変更をより拾いやすくする
- 「型変更」だけでなく、利用者が壊れる変更に焦点を当てる
- とくに新規性が高いのは `Problem Details` 互換の明示化である

### インタラクション能力

改善意図:

- アクセシビリティ属性の有無の点検に留めず、実際の操作失敗や誤操作リスクに寄せる
- WCAG 2.2 の思想を UI 変更レビューに翻訳する
- Web だけでなく CLI / developer tool の operator UX にも適用できるようにする

### 信頼性

改善意図:

- 現代のクラウド運用で致命傷になりやすい timeout, retry, probes, graceful shutdown, observability を中心に整理する
- 「落ちる/落ちない」だけでなく、「障害時に連鎖しないか」「原因追跡できるか」まで見る
- 新規性が高いのは `retry budget`, `degraded mode`, `startup probe` の役割分離である

### セキュリティ

改善意図:

- injection 系に偏らず、authorization, browser boundary, API consumption, software supply chain まで視野を広げる
- 現代 Web/API の実害に直結しやすい項目へ更新する
- 既存項目の大半は活かしつつ、真に新規な追加は `BOPLA` などに絞る

### 保守性

改善意図:

- コードの読みやすさだけでなく、境界検証、型安全、contract test、トラブル解析可能性まで広げる

### 柔軟性

改善意図:

- 環境変数化の有無だけでなく、deploy/rollback/replaceability/scale-out を扱う
- 現代のシステム差し替え耐性に近づける

### 安全性

改善意図:

- 正常系だけでなく、破壊的操作や危険な誤操作に対する防御を拾う
- operator / end user の双方に対する warning と fail-safe を重視する
- `unsafe API consumption` の観点は、安全性だけに閉じずセキュリティとも接続する

## Important Decisions

### 採用するもの

- ISO/IEC 25010:2023 の 9 品質特性構成
- Tier 1 / Tier 2 / Tier 3 の大枠
- Web / distributed system 観点の条件付き導入
- 標準マップ方式
- false positive 抑制の強化

### 採用しないもの

- `km:quality-review` を Web 専用 skill にすること
- 標準やベストプラクティスの長文要約を本文へ大量投入すること
- OWASP / WCAG / SRE などを別の並列品質モデルとして扱うこと
- 「見るべき観点を全部増やせば精度が上がる」という方向

不採用理由:

- skill の軸がぶれる
- context cost が上がる
- 一般論が増えて diff レビュー精度が落ちる

## Implementation Order

1. `SKILL.md` に `surface 条件付き補助観点` と強化した除外ルールを追加する
2. 現行 checklist 項目を `新規追加 / 補強 / 再配置 / 据え置き` に棚卸しする
3. `quality-checklist.md` をインデックス寄りに再編する
4. `reference/` 9 ファイルを共通テンプレートへ揃えつつ更新する
5. `report-format.md` の所見ルールを補強する
6. `tests/skills` の scenario と rubric を追加更新する
7. 必要なら `templates/skills/review/SKILL.md` 側の quality-review 説明を微調整し、サブ skill の契約変更を反映する

この順序にする理由:

- まず skill 契約を固定しないと、checklist と reference の書き方がぶれる
- 次に棚卸しを入れることで、既存内容の重複追加を避けられる
- checklist をインデックス寄りにしてから reference を更新すると、役割分担が決めやすい
- 最後に tests を足すことで、設計意図と回帰防止を一致させられる

## Acceptance Criteria

- `quality-review` の構造は ISO/IEC 25010:2023 ベースのまま維持されている
- Web / API / distributed system の観点が、既存の `実務補助` を formalize した形で統合されている
- 各 reference に `標準マップ` がある
- `quality-checklist.md` が 400 行超へ膨張せず、インデックスとして読める密度に保たれている
- `quality-checklist.md` に `見る条件` と `見送り条件` がある
- 新規追加と補強の区別が明文化されている
- false positive 抑制ルールが強化されている
- tests に現代的観点の新規シナリオが追加されている

## Review Focus For Another AI

この計画をレビューする AI には、特に次を見てほしい。

- ISO/IEC 25010:2023 を主軸に維持したまま、Web 実務観点を重ねる設計が妥当か
- 標準マップ方式で十分か。それとも別紙リファレンスに寄せるべきか
- `surface 条件付き補助観点` の定義に漏れや過不足がないか
- Tier → Depth → surface 条件付き項目 の優先順位が十分に明確か
- false positive 抑制ルールが弱すぎないか、または強すぎて有用な指摘を落とさないか
- 9 品質特性のうち、どれか 1 つだけ過剰に重くなっていないか
- `tests/skills` に追加すべきシナリオが他にあるか

## Assumptions

- `km:quality-review` は主に review orchestrator から呼ばれる manual-only subskill である
- 実装対象は skill とテストであり、アプリケーションコードや CI の全面改修は今回の範囲外である
- 外部標準は最新の公開一次情報ベースで扱うが、skill 本体では要約のみを保持する
