# HTML Document — 作成ガイド

図・埋め込み・スタイル・安全対策の該当箇所を、作成直前に読む。

## 本文fragment

source fileには`<div class="container">`の内側だけを書く。`<!doctype html>`、`html`、`head`、`body`、CSP、Mermaid loader、CSS / JavaScriptの`BUILD:INLINE` marker、`RENDER:TITLE` / `RENDER:CONTENT` markerは複製しない。`--title`はplain textで渡し、render helperがHTML escapeする。通常は最上位の`h1`と同じ文言にする。

必要な部品だけを次のように組み合わせる。`nav`、callout、table、code、Mermaid、footerは内容に応じて省略できる。

```html
<header class="doc-header">
  <h1>ドキュメントタイトル</h1>
  <p class="subtitle">サブタイトル / 一文サマリー</p>
  <p class="meta">生成日: YYYY-MM-DD</p>
</header>

<nav class="toc">
  <strong>目次</strong>
  <ul><li><a href="#section-1">1. セクション</a></li></ul>
</nav>

<section>
  <h2 id="section-1">1. セクション</h2>
  <p>本文。</p>
  <div class="callout callout-note">
    <p class="callout-title">Note</p>
    <p>補足や前提。色分けは note / warning / important。</p>
  </div>
  <table>
    <thead><tr><th>項目</th><th>値</th></tr></thead>
    <tbody><tr><td>例</td><td>説明</td></tr></tbody>
  </table>
  <pre><code>if (a &lt; b &amp;&amp; b &gt; 0) {
  return true;
}</code></pre>
</section>

<footer class="doc-footer">
  <p>文書の補足。</p>
</footer>
```

## 図（Mermaid）

次の型だけを使い、外部icon・フォントを取得する`architecture-beta`やiconパックは使わない。

| 用途 | 図種 |
| --- | --- |
| 処理・構成・アーキテクチャ | `flowchart`。層・コンテナは`subgraph`で分ける |
| 時系列のやり取り | `sequenceDiagram` |
| 状態遷移 | `stateDiagram-v2` |
| データモデル・関連 | `erDiagram` |
| 構造・クラス関係 | `classDiagram` |
| スケジュール | `gantt` |
| 分解 | `mindmap` |
| 年表 | `timeline` |

`<figure class="diagram"><pre class="mermaid">...</pre><figcaption>図N: ...</figcaption></figure>`で配置する。`pre`により読込失敗・JS無効時もソースを読める。ラベルは短く要約し、長いログ・エラーを貼らない。`mindmap` / `timeline`は相対インデントをそろえ、末尾に空白だけの行を残さない。

## 埋め込みとエスケープ

エスケープを一次防御とする。未信頼データをスクリプトや属性へ流し込まない。

| 文脈 | 規則 |
| --- | --- |
| 本文 | `& < > " '`を実体参照化 |
| 属性 | 値をクォートし、`& < > " '`を実体参照化 |
| URL | 文書内`#anchor`または`https:`のみ。外部リンクに`rel="noopener noreferrer"`を付け、`javascript:` / `data:` / `vbscript:`を使わない |
| コード | `<pre><code>`内の`& < >`を実体参照化。`</script>` / `</pre>`などの閉じ偽装を防ぐ |
| 図ソース | 未信頼文字列を直接挿入しない。HTMLのテキストとして格納する文字はHTMLとして適切にエスケープし、Mermaid構文上の特殊文字はMermaidの記法で表す。表示内容の文字を削って安全化しない |

## CSP・SRI

- CSPを削除・緩和しない。`default-src 'none'` / `connect-src 'none'`を保ち、script・imgに外部ホストを追加しない。imgは`blob:`と、画像埋め込み時の`data:`だけに限る
- scriptは固定CDNのMermaidと図操作用inlineだけ。MermaidはSRI（`integrity`）と`crossorigin="anonymous"`付きUMDを使い、`securityLevel:'strict'`（内蔵DOMPurify）を維持する
- `'unsafe-inline'`を許すため、CSPはinline scriptによるXSSを止めない。`connect-src`などはfetch / XHR / beaconや許可外のimg・scriptを制限するが、meta CSPでは`location`変更や`window.open`による外部遷移を防げない。CSPをエスケープの代わりにしない
- `javascript:` URL、inlineイベントハンドラ、外部icon・フォントを使わず、資格情報・トークン・PIIを含めない

## レイアウトと画像

- スタイル変更には`document-template.css`を使い、印刷用の色保持・改ページ回避を保つ
- 外部画像は使わない。スクリーンショットはBase64で埋める。trusted shellの`img-src blob: data:`を保ち、connect / form / defaultなどの`'none'`は変えない
