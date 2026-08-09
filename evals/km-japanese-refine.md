# km-japanese-refine 評価シナリオ集

変更箇所に応じて再走する題材と合否線。実行時には読まない。

## 再走トリガ

| 触った箇所 | 再走する題材 |
| --- | --- |
| description・起動条件 | explicit-trigger |
| 不変条件・削除条件 | contract-preservation, semantic-relations, negation-scope, quantifier-preservation, temporal-order, exception-binding, reference-resolution, intentional-duplication, over-compression, spec-boundary, no-change |
| 推敲工程・一般ガイドライン | terminology, logical-structure, markup-preservation, repository-terminology, genre-adaptation |
| `references/skill-description.md` | skill-description |
| 出力契約 | output-boundary, audit-output, repository-coverage |

## 題材と合否線

- **explicit-trigger** — description 一覧だけから skill を選ばせる。should:「この日本語を推敲して」「冗長な説明を削って」「自然で分かりやすい日本語にして」「意味を変えずに、この手順を簡潔にして」「この skill description を一行で的確にして」。should-not:「この英語を日本語に翻訳して」「この英語を自然で分かりやすい日本語にして」「この実装をレビューして」「README と実装の整合を確認して」「この仕様を再設計して」「日本語の typo を直した」。明示された日本語文の推敲では起動し、通常の実装、レビュー、翻訳、文書同期では自動起動しないことが合否線
- **contract-preservation** — 「利用者は申請を取り消してよい。ただし、承認後は管理者だけが取り消せる。監査ログは削除してはならない。」を簡潔にさせる。許可、例外、主体、禁止の強さがすべて残ることが合否線
- **semantic-relations** — 目的と機能、既存状態と新規行為、並置と因果、事実と根拠を含む文章を推敲させる。目的を実際の機能へ、既存状態を新規行為へ、並置を因果へ、根拠候補を断定へ変えないことが合否線
- **negation-scope** — 部分否定と全否定を含む文章を推敲させる。否定の有無と作用域が変わらないことが合否線
- **quantifier-preservation** — 「すべて」「のみ」「少なくとも」「最大」を含む文章を推敲させる。数量の範囲と上限・下限が変わらないことが合否線
- **temporal-order** — 完了後、実行中、実行前の条件を含む手順を推敲させる。時点、完了状態、処理順序を維持することが合否線
- **exception-binding** — 複数の条件と例外を含む規則を推敲させる。例外が適用される条件や指示を変えないことが合否線
- **reference-resolution** — 複数の参照候補とリンクを含む文を推敲させる。指示語の参照先とリンク先を維持することが合否線
- **intentional-duplication** — 独立して読み込まれる二つの文書に同じ安全契約を含めて推敲させる。編集上の重複とみなして片方を削らないことが合否線
- **redundancy-reduction** — 同じ目的の反復、一般的な LLM 能力の説明、空の導入と、プロジェクト固有の防御理由を混ぜた rule を推敲させる。前者を削り、防御理由と固有契約を残すことが合否線
- **terminology** — `focus` / `planning risk` とその日本語の二重表記、`approval_policy` のような識別子を含む文を推敲させる。不自然な英日混在を直し、一概念一用語にしつつ識別子を保持することが合否線
- **logical-structure** — OR 条件、順序付き手順、例外を一文へ詰めた文章を推敲させる。条件の論理、順序、例外が形式から再現できることが合否線
- **skill-description** — 内部手順、reference、レビュア人数、判定状態まで含む description を一行へ推敲させる。対象、目的、起動条件、必要な境界だけが残り、`references/skill-description.md` を description の対象と判定した後に読むことが合否線
- **spec-boundary** — 「大きな変更では追加レビューする」の「大きな」を明確にさせる。原文にない行数や金額を発明せず、本文の表現変更と「基準の定義」という仕様変更候補を分けることが合否線
- **minimal-intervention** — 「テストが成功したら、変更をコミットする。」を推敲させる。原文を維持し、変更不要と短く返すことが合否線
- **no-change** — 既に明確で用語も統一された文章を推敲させる。不要な言い換えをせず、変更不要と判断することが合否線
- **over-compression** — 条件、例外、根拠を含む長文を簡潔化させる。短さのために重要な命題を削らず、原文にない命題も追加しないことが合否線
- **markup-preservation** — YAMLフロントマター、コードフェンス、Markdownリンク、見出しID、プレースホルダーを含む文書を推敲させる。文章以外の構造と識別子が変わらないことが合否線
- **repository-terminology** — 複数ファイルで同じ一般概念を異なる語で呼ぶリポジトリを監査させる。一般概念を統一し、識別子と固定フィールド値は維持することが合否線
- **audit-output** — 複数ファイルを診断させる。各指摘に一意なID、場所、変更前後、理由、適用規則、変更種別があることが合否線
- **repository-coverage** — 変更不要・保護対象を含む追跡ファイル一式を監査させる。全ファイルの状態と指摘IDを欠落なく照合できることが合否線
- **genre-adaptation** — 同じ一文または単一段落を、レポート、番号付き手順、エラー、警告、規程としてそれぞれ整えさせる。短い入力でも `japanese-guidelines.md` を読み、意味台帳は共通のまま、用途に応じて結論、前提、危険、次の行動、法性の優先順が変わることが合否線
- **output-boundary** — 複数段落の推敲を依頼する。推敲後の本文を先に返し、全変更の逐語対照や一般的講評を自動追加しないことが合否線。意味上の判断や残る重要な曖昧さがある場合だけ補足する

## 落とし穴

- 短くなったことを成功とみなさない。意味、契約、判断可能性の損失は即失敗
- 保守的すぎて、重複や一般論をほとんど残す出力も成功としない
- 禁止語や単純な置換へ評価を寄せると、未知の文章への判断手順を測れない
- 変更後だけの成功から、旧版や skill なしの状態より改善したとは主張しない
- reference は先読みさせない。まず `SKILL.md` を読み、対象と条件に応じて必要な reference だけを読ませる
