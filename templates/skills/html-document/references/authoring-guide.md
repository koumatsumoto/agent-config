# HTML Document — Authoring Guide

`km:html-document` で本文を組むときの詳細リファレンス。図種の選び方、エスケープ規律、セキュリティ基盤（CSP/SRI）、スタイル調整をまとめる。SKILL.md の Workflow から参照する。

## 図（Mermaid）

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
- `document-template.js` が各 `figure.diagram` にホイール拡縮・ドラッグ移動・WebP 別タブ表示を付ける。`figure class="diagram"` 構造を保てば自動で有効になる（個別のボタン markup は不要）。図ラベルは init の `htmlLabels:false` で SVG `<text>` 化し、canvas 汚染なしに WebP 化できるようにしている
- mermaid を更新する時は、`document-template.html` の `<script src>` と CSP `script-src` のバージョンパス、`integrity`(SRI) を同時に差し替える（floating 版は SRI と両立しないため使わない）

## エスケープ

埋め込むデータは文脈ごとにエスケープする。`script-src` は図操作のため `'unsafe-inline'` を許可しており inline 実行を止めないので、エスケープ漏れはそのまま実行され得る。未信頼データを script・属性に流し込まない規律が重要。CSP は外部送信（`connect-src 'none'`）を止める egress バックストップを担う。

| 文脈 | 規律 |
| --- | --- |
| 本文テキスト | `& < > " '` を実体参照化 |
| 属性値 | 値をクォートし `& < > " '` を実体参照化 |
| URL | 同一文書内 `#anchor` は可。外部は `https:` のみ + `rel="noopener noreferrer"`。`javascript:`/`data:`/`vbscript:` は不可 |
| コードブロック | `<pre><code>` 内で `& < >` を実体参照化（`</script>`/`</pre>` 等の閉じ偽装に注意） |
| 図ソース | `<pre class="mermaid">` はエスケープしない領域。未信頼文字列を入れない。値を入れるなら `% < > "` と改行を除去する |

## セキュリティ（CSP / SRI）

- CSP `<meta>` の外部送信の歯止め（`default-src 'none'` / `connect-src 'none'`、`img-src` は `blob:`(/`data:`) のみ、script/img に外部ホストを足さない）を消さない・緩めない。これが egress backstop の本体
- script は固定 CDN の mermaid と図操作の inline script だけ。`script-src` に外部ホストを足さない。Mermaid は SRI(`integrity`) + `crossorigin="anonymous"` 付き UMD で読み、既定 `securityLevel:'strict'`（内蔵 DOMPurify）で自動描画する。`loose` 化しない
- `'unsafe-inline'` を許可しているため inline script は XSS backstop にならない。`connect-src 'none'` 等は fetch/XHR/beacon と外部 img/script を塞ぐが、top-level navigation（`location` 変更・`window.open` の外部 URL）は meta CSP では塞げない。未信頼データを埋める運用では**エスケープ規律が一次防御線**（CSP は受動経路の backstop）。`javascript:` URL・inline イベントハンドラ・外部 icon/フォントは使わない
- 秘密情報（資格情報・トークン・PII）を含めない

## スタイル / レイアウト

- コンテンツ幅 1400px の中央寄せ。CSS は `document-template.css` にあり、ビルドで `<style>` に挿入される。配色・タイポグラフィ等の調整はこのファイルで行う
- 外部画像は無効（`img-src blob:` は図の画像化用のローカル blob のみ）。スクリーンショットを埋める場合は `img-src blob: data:` にし、inline base64 で埋める（connect/form/default 等の `'none'` は触らない）
- 印刷/PDF を想定し、`document-template.css` の print CSS（色保持・改ページ回避）を保つ
