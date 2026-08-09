# km-japanese-refine scenario bank

変更箇所に応じて再走する題材と合否線。runtime では読まない。

## 再走トリガ

| 触った箇所 | 再走する題材 |
| --- | --- |
| description・起動条件 | explicit-trigger |
| 不変条件・削除条件 | contract-preservation, semantic-relations, redundancy-reduction, spec-boundary, minimal-intervention |
| 推敲工程・一般ガイドライン | terminology, logical-structure, genre-adaptation |
| `references/skill-description.md` | skill-description |
| 出力契約 | output-boundary |

## 題材と合否線

- **explicit-trigger** — description 一覧だけから skill を選ばせる。should:「この日本語を推敲して」「冗長な説明を削って」「自然で分かりやすい日本語にして」「意味を変えずに、この手順を簡潔にして」「この skill description を一行で的確にして」。should-not:「この英語を日本語に翻訳して」「この英語を自然で分かりやすい日本語にして」「この実装をレビューして」「README と実装の整合を確認して」「この仕様を再設計して」「日本語の typo を直した」。明示された日本語文の推敲では起動し、通常の実装、レビュー、翻訳、文書同期では自動起動しないことが合否線
- **contract-preservation** — 「利用者は申請を取り消してよい。ただし、承認後は管理者だけが取り消せる。監査ログは削除してはならない。」を簡潔にさせる。許可、例外、主体、禁止の強さがすべて残ることが合否線
- **semantic-relations** — 目的と機能、既存状態と新規行為、並置と因果、事実と根拠を含む文章を推敲させる。目的を実際の機能へ、既存状態を新規行為へ、並置を因果へ、根拠候補を断定へ変えないことが合否線
- **redundancy-reduction** — 同じ目的の反復、一般的な LLM 能力の説明、空の導入と、プロジェクト固有の防御理由を混ぜた rule を推敲させる。前者を削り、防御理由と固有契約を残すことが合否線
- **terminology** — `focus` / `planning risk` とその日本語の二重表記、`approval_policy` のような識別子を含む文を推敲させる。不自然な英日混在を直し、一概念一用語にしつつ識別子を保持することが合否線
- **logical-structure** — OR 条件、順序付き手順、例外を一文へ詰めた文章を推敲させる。条件の論理、順序、例外が形式から再現できることが合否線
- **skill-description** — 内部手順、reference、レビュア人数、判定状態まで含む description を一行へ推敲させる。対象、目的、起動条件、必要な境界だけが残り、`references/skill-description.md` を description の対象と判定した後に読むことが合否線
- **spec-boundary** — 「大きな変更では追加レビューする」の「大きな」を明確にさせる。原文にない行数や金額を発明せず、本文の表現変更と「基準の定義」という仕様変更候補を分けることが合否線
- **minimal-intervention** — 「テストが成功したら、変更をコミットする。」を推敲させる。原文を維持し、変更不要と短く返すことが合否線
- **genre-adaptation** — 同じ一文または単一段落を、レポート、番号付き手順、エラー、警告、規程としてそれぞれ整えさせる。短い入力でも `japanese-guidelines.md` を読み、意味台帳は共通のまま、用途に応じて結論、前提、危険、次の行動、法性の優先順が変わることが合否線
- **output-boundary** — 複数段落の推敲を依頼する。推敲後の本文を先に返し、全変更の逐語対照や一般的講評を自動追加しないことが合否線。意味上の判断や残る重要な曖昧さがある場合だけ補足する

## 落とし穴

- 短くなったことを成功とみなさない。意味、契約、判断可能性の損失は即失敗
- 保守的すぎて、重複や一般論をほとんど残す出力も成功としない
- 禁止語や単純な置換へ評価を寄せると、未知の文章への判断手順を測れない
- candidate 単独の成功から、旧版や skill 無しの状態より改善したとは主張しない
- reference は先読みさせない。まず `SKILL.md` を読み、対象と条件に応じて必要な reference だけを読ませる
