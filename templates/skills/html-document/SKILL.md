---
name: km:html-document
description: Renders already-prepared content as a single security-hardened HTML document (1400px layout, Mermaid diagrams); 内容そのものは決めない。Use when the user says "HTML にして" / "HTML のレポート" / "HTML 文書にして"。
argument-hint: "[topic | output-path.html]"
---

# HTML Document

用意済みの内容を、単一の自己完結 HTML 文書として組む。扱うのは HTML の構造・レイアウト・図・セキュリティ基盤だけで、**内容（何を書くか）は決めない**。

## 責務 / 非責務

- 担う: 見出し階層、レイアウト（1400px・表・callout・コード・図）、Mermaid 図の描き方、安全な HTML（CSP/SRI/エスケープ）、単一ファイル出力
- 担わない: 文書の内容・章立ての意思決定、ジャンル別の書き方、本文生成。内容は呼び出し側が決める

## Context

- Output dir: !`pwd`
- Today: !`date +%Y-%m-%d`

## Success Criteria

- 単一 HTML（CSS・図の初期化を inline）で出力する
- コンテンツ幅 1400px の中央寄せ、見出し階層が整う（H1 は 1 つ）、長文は TOC＋アンカーを付ける
- Mermaid 図はカタログの型のみ。外部への発信は固定 CDN の script 取得だけ
- 埋め込みデータは文脈別にエスケープし、スクリプトとして実行されない
- ブラウザで開いて CSP 違反・SRI mismatch・実行時エラーが出ない

## Workflow

1. 出力先を決める（既定 `./<slug>.html`、`$ARGUMENTS` にパスがあれば優先）。既存ファイルは上書き前に確認する
2. `references/document-template.html` を読み、構造・CSS・CSP・図の初期化・プレースホルダを把握する
3. 内容を見出し階層と文脈別エスケープ（下表）に従って流し込む。コードは escape 後に `<pre><code>` へ入れる
4. 説明に図が要る箇所へ Mermaid を作図し `<figure>` + `<figcaption>` で置く
5. 長文なら先頭に TOC を置き、各見出しに `id` を付けてアンカーリンクする
6. 単一 `.html` として書き出す
7. ブラウザで開いて検証し、出力パスを報告する

## HTML 構造

- H1 は文書タイトルの 1 つだけ。H2 = セクション、H3 = サブセクション。レベルを飛ばさない
- 長文は先頭に TOC を置き、各見出しに `id` を付け、`#id` でアンカーリンクする

## Diagram Guidance

説明に図が要る箇所だけ Mermaid を使う。カタログの型に限る（外部 icon/フォントを取得する `architecture-beta` や icon パックは使わない）。

| 用途 | 図種 |
| --- | --- |
| 処理フロー | `flowchart` |
| 構成・アーキテクチャ | `flowchart` + `subgraph`（グルーピングで層/コンテナを表す） |
| 時系列のやり取り | `sequenceDiagram` |
| 状態遷移 | `stateDiagram-v2` |
| データモデル/関連 | `erDiagram` |
| 構造/クラス関係 | `classDiagram` |
| スケジュール | `gantt` |
| 分解 | `mindmap` |
| 年表 | `timeline` |

- 図は `<figure class="diagram"><pre class="mermaid">...</pre><figcaption>図N: ...</figcaption></figure>` で置く。`<pre>` にすると読込失敗・JS 無効時もソースが読める
- ノードのラベルは要約した短文にする（長いログ・エラー文字列をそのまま貼らない）
- `mindmap` / `timeline` は字下げに敏感。`<pre class="mermaid">` 内は相対インデントを揃え、末尾に空白だけの行を残さない

## エスケープ

埋め込むデータは文脈ごとにエスケープする。エスケープは唯一の防御ではなく、CSP がバックストップになる。

| 文脈 | 規律 |
| --- | --- |
| 本文テキスト | `& < > " '` を実体参照化 |
| 属性値 | 値をクォートし `& < > " '` を実体参照化 |
| URL | 同一文書内 `#anchor` は可。外部は `https:` のみ + `rel="noopener noreferrer"`。`javascript:`/`data:`/`vbscript:` は不可 |
| コードブロック | `<pre><code>` 内で `& < >` を実体参照化（`</script>`/`</pre>` 等の閉じ偽装に注意） |
| 図ソース | `<pre class="mermaid">` はエスケープしない領域。未信頼文字列を入れない。値を入れるなら `% < > "` と改行を除去する |

## Security Rules

- CSP `<meta>`（`default-src 'none'` ベース）を消さない・緩めない
- Mermaid は UMD を バージョン固定 + SRI(`integrity`) + `crossorigin="anonymous"` で読む。ESM core・SRI 無しは不可
- 初期化は `securityLevel: 'strict'`（内蔵 DOMPurify が出力をサニタイズする主防御）。`loose` 化しない
- init `<script>` は CSP の `sha256` とバイト一致が必須。**この 1 行は編集しない**。変える場合は `sha256` を再計算して CSP も合わせる
- カタログ外の型・外部 icon/フォント取得・固定 CDN 以外の外部リソース（フォント/画像/解析/トラッキング）を足さない
- inline イベントハンドラ・`javascript:` URL を使わない
- 秘密情報（資格情報・トークン・PII）を含めない

## Style / Layout

- コンテンツ幅 1400px の中央寄せ。CSS は inline `<style>` に持ち、コメント付きで調整しやすくする
- 配色・タイポグラフィ等の調整は CSS のみで行う（init `<script>` には触れない）
- 画像は既定で無効（`img-src 'none'`）。スクリーンショットが要る場合だけ CSP を `img-src data:` にし、inline base64 で埋める（他ディレクティブは据え置き）
- 印刷/PDF を想定し、テンプレートの print CSS（色保持・改ページ回避）を保つ

## Safety Rules

- ローカル `file://` 閲覧を前提とする（HTTP 配信のヘッダ防御は対象外）
- 既存ファイルは上書き前に確認する
- 文書の内容そのものを作るのはこのスキルの責務外。内容生成は呼び出し側に委ねる
