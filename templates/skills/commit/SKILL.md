---
name: km:commit
description: Creates a Conventional Commits git commit for the current staged/unstaged changes. Use whenever the user says "commit" / "コミットして" or otherwise asks to commit the current work.
argument-hint: "[message]"
---

# Commit

変更内容を確認し、必要なファイルだけを安全にコミットする。コミットメッセージは「後から git log / blame だけで変更の意図・背景をたどれる」ことを最優先に書く（読者は将来の AI セッションと人間の両方）。

## Context

- Git status: !`git status`
- Changes (stat): !`git diff HEAD --stat`
- Branch: !`git branch --show-current`
- Recent commits: !`git log --oneline -10`

## Success Criteria

- ステージ対象を最小限に絞る
- メッセージ単体で「なぜこの変更か」を再構成できる（issue / PR を開かなくても意図が読める）
- 複数の独立した作業がまとまっている場合、明確に分割できるならコミットを分ける

## Workflow

1. Context を読み、`$ARGUMENTS` があればタイトルのヒントとして使う
2. 対象ファイルの差分を確認する（小さければ `git diff HEAD` 一括、大きければ `git diff HEAD -- <file>` で個別に。stat だけでメッセージを書かない）
3. 対象ファイルだけを個別に `git add <file>` でステージする
4. `git diff --cached --stat` で誤ステージがないか確認する
5. メッセージを組み立て、`git commit -F - <<'EOF'` で渡す（`-m` の引用符・backtick 事故を避ける）
6. `git log -1 --stat` で結果を確認する

変更が複数の独立した作業を含み、明確に分割できる場合のみ作業単位ごとに 2–6 を繰り返す。迷ったら分けない。

## Commit Message

why は diff からは読めない。この session にしかない情報（依頼の目的・計画 issue の判断・作業中に覆した方針・却下した代替案）から抽出して残す。session が消えた後は、コミットメッセージが why の唯一の記録になる。

### Subject

- `type: 日本語の要約` または `type(scope): 日本語の要約`（type / scope は英語、description は日本語）
- scope は repo に実在する構造名（directory / package / skill 名）をそのまま使えるときだけ付ける。概念的な分類（コードに実在しない語）は発明しない。複数 scope にまたがる場合はまずコミット分割を疑い、分割しないなら省略する。迷ったら省略
- 変更の効果・意図が分かる要約にする。50 文字目安
- 経緯ベースの subject は書かない（「レビュー指摘を反映」「〜修正の修正」は禁止。何をどう変えるかを内容で書く）

### Body（可変構造・why 先頭）

固定見出しは使わず、規模に応じて段落と bullets で構成する:

1. **why 段落**（設計判断を含む変更では必須）: 何が問題 / 目的で、どの判断をなぜ採ったか。旧→新の挙動対比はここに書く（コード側は現在形で書く方針のため、変遷はコミットにしか残らない）。検討して却下した代替案があれば理由とともに残す
2. **変更点 bullets**（diff から自明でない場合のみ）: `file: 変更の要点`。diff の言い直しはしない（`git show` で分かることを繰り返さない）
3. **検証**（実施した場合のみ）: 何をどう確認したか 1–2 行。実施していない検証は書かない
4. **Refs trailer**: 関連 issue があれば末尾に独立行で `Refs #N`（`Closes` は PR 本文の責務）

書かないもの: 逐次の作業ログ・レビュー往復の経緯・「依頼された」等の session 進行への言及。最終差分を理解するための背景・判断だけを書く。

typo / style 等の自明な変更は subject + 必要なら 1–2 行で足りる。無理に本文を膨らませない。

サンプル:

```text
fix: リフレッシュ時に旧 token を失効させ盗難 token の残存を防ぐ

アクセストークン更新時に旧 refresh token を失効させておらず、盗まれた
token が期限まで使える状態だった。rotation 方式（更新ごとに旧 token 失効
+ 再利用検知で全 session 無効化）を採用。JWT の自己完結検証では即時失効
ができないため、refresh token のみ DB 管理とし access token は短命の
まま維持する（全 token DB 管理案は毎リクエスト DB 参照になるため却下）。

- lib/auth/refresh.ts: rotation と再利用検知を実装
- middleware.ts: 401 時の透過的リトライを追加

検証: 旧 token 並行使用の競合を統合テストで確認。

Refs #123
```

## Safety Rules

- `git add -A` / `git add .` は使わない
- `git commit --no-verify` は使わない
- push はこのスキルのスコープ外
