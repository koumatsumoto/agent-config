---
name: km-html-document
description: 用意済みの内容を単一HTML文書にする。「HTMLレポートにして」などの依頼で使い、内容自体は決めない。
argument-hint: "[topic | output-path.html]"
---

# HTML Document

本文の内容・構成は呼び出し側が決め、このスキルはHTMLのレイアウト・図・安全対策を担う。
CSSと操作用JavaScriptを1ファイルに同梱する。Mermaid本体はCDNから取得するため、図の描画にはネットワーク接続が必要。ローカル`file://`での閲覧を対象とし、HTTP配信のヘッダ防御は扱わない。

## 作成

1. 出力先を決める。既定は`./<slug>.html`、`$ARGUMENTS`にパスがあれば優先する。既存ファイルは上書き前に確認する
2. 読み込んだ`SKILL.md`の実在directoryを基準に`references/document-template.html`を複製し、用意済みの本文を過不足なく最小限のHTMLで配置する。HTMLとして扱う部分以外はエスケープする
3. 作業directoryを変えず、次を実行する

```text
node "<skill-directory>/references/build.js" "<出力パス>"
```

4. ビルドの成功と出力ファイルの生成だけを確認する。`build.js`がCSS・JavaScriptを挿入する
5. 表示不要と明示されていなければ、後処理として`$km-open-file`で開く。生成結果と表示結果は分けて報告し、表示失敗で生成成功を取り消さない。内容の再レビューや反復的な磨き込みはしない

## 参照と制約

- 概念・データ関係・処理・シーケンス・状態遷移は、理解を助けるMermaid図で積極的に示す。図を作る前に`references/authoring-guide.md`の該当箇所を読む。本文にない事実や、理解に寄与しない装飾は足さない
- URL・コード・未信頼データ・画像の埋め込み、スタイル・安全対策の変更時も同ガイドの該当箇所だけを読む
- 通常の本文作成では`references/document-template.css`と`references/document-template.js`を読む必要はない
- テンプレートのレイアウト・図操作・`BUILD:INLINE`マーカーを保つ。既定スタイルを変えず、CSP・SRIを削除・緩和しない。変更が必要な場合は同ガイドの制約に従う
