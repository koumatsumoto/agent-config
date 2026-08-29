---
name: km-html-document
description: 用意済みの内容を、安全対策済みの単一HTML文書にする。「HTMLレポートにして」などの依頼で使い、内容自体は決めない。
argument-hint: "[topic | output-path.html]"
---

# HTML Document

用意済みの本文をHTMLへ組み、レイアウトと安全対策だけを担う。本文の内容と構成は呼び出し側が決める。既存テンプレートをそのまま使い、必要な本文だけを流し込んで単一ファイルにする。

## Files（`references/`）

| ファイル | 役割 | 本文作成時 |
| --- | --- | --- |
| `document-template.html` | 骨組み（CSP・レイアウト・`BUILD:INLINE` マーカー） | 本文を配置する |
| `document-template.css` | 既定スタイル | 通常は読まない・変えない |
| `document-template.js` | Mermaid 初期化・図操作 | 通常は読まない・変えない |
| `build.js` | CSS/JS を挿入して単一 HTML を生成 | 実行する |
| `authoring-guide.md` | 図、特殊な埋め込み、スタイル・安全対策変更の詳細 | 該当箇所だけ参照 |

## Workflow

1. 出力先を決める（既定 `./<slug>.html`、`$ARGUMENTS` にパスがあれば優先）。既存ファイルは上書き前に確認する
2. `references/document-template.html` の複製へ、用意済みの本文を必要最小限のHTMLとして配置する。`BUILD:INLINE` マーカーと既存のCSPは変えない
3. `node references/build.js <出力パス>` を実行する
4. コマンドが成功し、出力ファイルが生成されたことだけを確認して、出力パスを報告する。既定ではブラウザ確認や内容の再レビュー、反復的な磨き込みは行わない

図は、ユーザーが求めた場合か、文章より関係を明確にできる場合だけ追加する。既定のスタイルは変更しない。Mermaid、URL、コードブロック、未信頼データ、画像、スタイル・安全対策の変更が必要な場合だけ `authoring-guide.md` の該当箇所を読む。

## Success Criteria

- 用意済みの内容を過不足なく配置した単一 HTML を出力する
- `build.js` が正常終了し、CSS/JavaScriptが挿入されている
- 既存テンプレートのレイアウト、CSP、SRI、図操作を壊さない
- ユーザーが求めていない図、装飾、内容変更を加えない

## Safety Rules

- ローカル `file://` 閲覧を前提とする（HTTP 配信のヘッダ防御は対象外）
- 既存ファイルは上書き前に確認する
- 本文の内容そのものを作るのは責務外。内容生成は呼び出し側に委ねる
- 本文テキストはHTMLとして解釈させる部分を除いてエスケープする
- CSPによる外部送信の防止策（`default-src` / `connect-src 'none'`など）と`BUILD:INLINE`マーカーを壊さない
