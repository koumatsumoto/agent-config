---
name: km:html-document
description: Renders already-prepared content as a single security-hardened HTML document (1400px layout, Mermaid diagrams); 内容そのものは決めない。Use when the user says "HTML にして" / "HTML のレポート" / "HTML 文書にして"。
argument-hint: "[topic | output-path.html]"
---

# HTML Document

用意済みの内容を、単一の自己完結 HTML 文書として組む。扱うのは HTML のレイアウト・見た目・図・セキュリティ基盤だけで、**内容（何を書くか・どう構成するか）は決めない**。

## 責務 / 非責務

- 担う: レイアウトと各要素の見た目（1400px・見出し・表・callout・コード・図のスタイル）、Mermaid 図の描き方、安全な HTML（CSP/SRI/エスケープ）、単一ファイル出力
- 担わない: 文書の内容・章立て・見出し構成の意思決定（見出しレベルや TOC の要否を含む）、ジャンル別の書き方、本文生成。内容は呼び出し側が決める

## Context

- Output dir: !`pwd`
- Today: !`date +%Y-%m-%d`

## Success Criteria

- 単一 HTML（CSS を inline）で出力する
- コンテンツ幅 1400px の中央寄せで表示される
- Mermaid 図はカタログの型のみ。外部への発信は固定 CDN の mermaid 取得だけ
- 外部へのデータ送信が起きない（`connect-src 'none'` 等）。inline script は実行されない（XSS backstop）
- ブラウザで開いて CSP 違反・SRI mismatch・実行時エラーが出ず、図が自動描画される

## Workflow

1. 出力先を決める（既定 `./<slug>.html`、`$ARGUMENTS` にパスがあれば優先）。既存ファイルは上書き前に確認する
2. `references/document-template.html` を読み、レイアウト・CSS・CSP・図の読み込み・プレースホルダを把握する
3. 内容を文脈別エスケープ（下表）に従って流し込む。コードは escape 後に `<pre><code>` へ入れる
4. 説明に図が要る箇所へ Mermaid を作図し `<figure>` + `<figcaption>` で置く
5. 単一 `.html` として書き出す
6. ブラウザで開いて検証し、出力パスを報告する

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
- mermaid を更新する時は、テンプレート末尾の `<script src>` と CSP `script-src` のバージョンパス、`integrity`(SRI) を同時に差し替える（floating 版は SRI と両立しないため使わない）

## エスケープ

埋め込むデータは文脈ごとにエスケープする。主目的は壊れた HTML を防ぐ描画衛生で、セキュリティは CSP がバックストップになる（`script-src` が inline 実行を止める）。

| 文脈 | 規律 |
| --- | --- |
| 本文テキスト | `& < > " '` を実体参照化 |
| 属性値 | 値をクォートし `& < > " '` を実体参照化 |
| URL | 同一文書内 `#anchor` は可。外部は `https:` のみ + `rel="noopener noreferrer"`。`javascript:`/`data:`/`vbscript:` は不可 |
| コードブロック | `<pre><code>` 内で `& < >` を実体参照化（`</script>`/`</pre>` 等の閉じ偽装に注意） |
| 図ソース | `<pre class="mermaid">` はエスケープしない領域。未信頼文字列を入れない。値を入れるなら `% < > "` と改行を除去する |

## Security Rules

- CSP `<meta>` の外部送信の歯止め（`default-src 'none'` / `connect-src 'none'` 系）を消さない・緩めない
- script は固定 CDN の mermaid だけ。`script-src` に他ホスト・`'unsafe-inline'`・hash を足さない（inline script 不可が XSS backstop）。Mermaid は SRI(`integrity`) + `crossorigin="anonymous"` 付き UMD で読み、読込だけで既定 `securityLevel:'strict'`（内蔵 DOMPurify）で自動描画する。`loose` 化する init を足さない
- カタログ外の図種・外部 icon/フォント・固定 CDN 以外の外部リソース（画像/解析/トラッキング）を足さない。`javascript:` URL・inline イベントハンドラを使わない
- 秘密情報（資格情報・トークン・PII）を含めない

## Style / Layout

- コンテンツ幅 1400px の中央寄せ。CSS は inline `<style>` に持ち、コメント付きで調整しやすくする
- 配色・タイポグラフィ等の調整は CSS のみで行う
- 画像は既定で無効（`img-src 'none'`）。スクリーンショットが要る場合だけ CSP を `img-src data:` にし、inline base64 で埋める（connect/form/default 等の `'none'` は触らない）
- 印刷/PDF を想定し、テンプレートの print CSS（色保持・改ページ回避）を保つ

## Safety Rules

- ローカル `file://` 閲覧を前提とする（HTTP 配信のヘッダ防御は対象外）
- 既存ファイルは上書き前に確認する
- 文書の内容そのものを作るのはこのスキルの責務外。内容生成は呼び出し側に委ねる
