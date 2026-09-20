---
name: km-html-document
description: 用意済みの内容を単一HTML文書にする。「HTMLレポートにして」などの依頼で使い、内容自体は決めない。
argument-hint: "[topic | output-path.html]"
---

# HTML Document

本文の内容・構成は呼び出し側が決め、このスキルはHTMLのレイアウト・図・安全対策を担う。
CSSと操作用JavaScriptを1ファイルに同梱する。Mermaid本体はCDNから取得するため、図の描画にはネットワーク接続が必要。ローカル`file://`での閲覧を対象とし、HTTP配信のヘッダ防御は扱わない。

## 作成

1. 出力先とdocument titleを決める。既定の出力先は`./<slug>.html`、`$ARGUMENTS`にパスがあれば優先する
2. 必要な場合だけ`references/authoring-guide.md`の該当箇所を読み、`<div class="container">`の内側に入るHTML fragmentを一時source fileとして作る。HTMLとして扱う部分以外はエスケープする
3. 作業directoryを変えず、次を1回実行する

```text
node "<skill-directory>/scripts/render.js" --source "<source-path>" --output "<output-path>" --title "<title>"
```

4. ユーザーが既存outputの置換を明示している場合だけ`--overwrite`を付ける
5. exit code 0と出力ファイルの生成だけを確認する。render helperがtrusted shell、CSS、JavaScript、本文fragmentを単一HTMLへまとめ、plain-textのtitleをエスケープする
6. 表示不要と明示されていなければ、後処理として`$km-open-file`で開く。生成結果と表示結果は分けて報告し、表示失敗で生成成功を取り消さない。内容の再レビューや反復的な磨き込みはしない

## 参照と制約

- 概念・データ関係・処理・シーケンス・状態遷移は、理解を助けるMermaid図で積極的に示す。図を作る前に`references/authoring-guide.md`の該当箇所を読む。本文にない事実や、理解に寄与しない装飾は足さない
- URL・コード・未信頼データ・画像の埋め込み、スタイル・安全対策の変更時も同ガイドの該当箇所だけを読む
- 通常の本文作成では`references/document-template.css`と`references/document-template.js`を読む必要はない
- sourceには`<!doctype html>`、`html`、`head`、`body`、CSP、Mermaid loader、render/build markerなどのshell要素を複製しない
- 既定スタイルやtrusted shellの変更が必要な場合は同ガイドの制約に従う
