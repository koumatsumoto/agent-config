---
name: km:html-document
description: Renders already-prepared content as a single security-hardened HTML document (1400px layout, Mermaid diagrams); 内容そのものは決めない。Use when the user says "HTML にして" / "HTML のレポート" / "HTML 文書にして"。
argument-hint: "[topic | output-path.html]"
---

# HTML Document

用意済みの内容を、単一の自己完結 HTML 文書として組む。扱うのは HTML のレイアウト・見た目・図・セキュリティ基盤だけで、**内容（何を書くか・どう構成するか）は決めない**（内容は呼び出し側が決める）。

骨組み HTML に本文を流し込み、最後に `build.js` で CSS/JS を挿入して単一ファイルにする。CSS/JS 本体は読まずビルドに任せるので、本文作成のコンテキストを軽く保てる。

## Context

- Output dir: !`pwd`
- Today: !`date +%Y-%m-%d`

## Files（`references/`）

| ファイル | 役割 | 本文作成時 |
| --- | --- | --- |
| `document-template.html` | 骨組み（CSP・レイアウト・`BUILD:INLINE` マーカー） | 読む / 編集する |
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
- 外部へのデータ送信が起きない（`connect-src 'none'`、script/img に外部ホストを持たない）
- 図が自動描画され、ホイール拡縮・ドラッグ移動でき、WebP で別タブに開ける
- ブラウザで開いて CSP 違反・SRI mismatch・実行時エラーが出ない

## Safety Rules

- ローカル `file://` 閲覧を前提とする（HTTP 配信のヘッダ防御は対象外）
- 既存ファイルは上書き前に確認する
- 本文の内容そのものを作るのは責務外。内容生成は呼び出し側に委ねる
- CSP の egress 歯止め（`default-src` / `connect-src 'none'` 等）と `BUILD:INLINE` マーカーを壊さない（詳細は `references/authoring-guide.md`）
