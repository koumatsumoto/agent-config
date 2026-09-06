# HTML Document — 作成ガイド

図・埋め込み・スタイル・安全対策の該当箇所を、作成直前に読む。

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
- 外部画像は使わない。スクリーンショットはBase64で埋め、その場合だけ`img-src blob: data:`にする。connect / form / defaultなどの`'none'`は変えない
