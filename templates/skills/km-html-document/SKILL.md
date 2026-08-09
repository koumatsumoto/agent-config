---
name: km-html-document
description: 用意済みの内容を、安全対策済みの単一HTML文書にする。「HTMLレポートにして」などの依頼で使い、内容自体は決めない。
argument-hint: "[topic | output-path.html]"
---

# HTML Document

用意済みの本文をHTMLへ組み、レイアウト、図、安全対策だけを担う。本文の内容と構成は呼び出し側が決める。骨組みHTMLへ本文を流し込み、最後に`build.js`でCSSとJavaScriptを挿入して単一ファイルにする。

## Context

- 出力先: !`pwd`
- 日付: !`date +%Y-%m-%d`

## Files（`references/`）

| ファイル | 役割 | 本文作成時 |
| --- | --- | --- |
| `document-template.html` | 骨組み（CSP・レイアウト・`BUILD:INLINE` マーカー） | 読む・編集する |
| `document-template.css` | スタイル | 読まない（ビルドが挿入） |
| `document-template.js` | mermaid 初期化・図操作（拡縮・WebP 化） | 読まない（ビルドが挿入） |
| `build.js` | マーカーを CSS/JS で置換し単一 HTML を生成 | 実行する |
| `authoring-guide.md` | 図種・エスケープ・セキュリティ・スタイルの詳細 | 必要時に参照 |

## Workflow

1. 出力先を決める（既定 `./<slug>.html`、`$ARGUMENTS` にパスがあれば優先）。既存ファイルは上書き前に確認する
2. `references/document-template.html`（骨組み）を読む。`<style>` / `<script>` の `BUILD:INLINE` マーカーは消さず残す
3. 本文を骨組みの `<body>` に流し込む。エスケープ・図の置き方・セキュリティ規律は `references/authoring-guide.md` に従う
4. 図が要る箇所へ Mermaid を `<figure class="diagram">` で置く（図種は authoring-guide.md のカタログから選ぶ）
5. マーカー入りの HTML を出力パスへ書き出す
6. `node references/build.js <出力パス>` を実行し、CSS/JS を挿入して単一 HTML にビルドする
7. ブラウザで開いて検証し、出力パスを報告する

## Success Criteria

- 骨組み HTML に CSS/図操作 script をビルド挿入した単一 HTML を出力する
- コンテンツ幅 1400px・中央寄せで表示される
- 受動的な外部送信（fetch/XHR/beacon・外部 img/script）が起きない（`connect-src 'none'` 等、スクリプトと画像に外部ホストを持たない）
- 図が自動描画され、Ctrl+ホイール / ＋−ボタンで拡縮・ドラッグ移動でき、WebP で別タブに開ける
- ブラウザで開き、CSP違反、SRI不一致、実行時エラーがないことを確認する

## Safety Rules

- ローカル `file://` 閲覧を前提とする（HTTP 配信のヘッダ防御は対象外）
- 既存ファイルは上書き前に確認する
- 本文の内容そのものを作るのは責務外。内容生成は呼び出し側に委ねる
- CSPによる外部送信の防止策（`default-src` / `connect-src 'none'`など）と`BUILD:INLINE`マーカーを壊さない（詳細は`references/authoring-guide.md`）
