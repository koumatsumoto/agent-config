# agent-config

Claude Code / Codex CLI の共通設定テンプレートを管理するリポジトリ。

## 構成

- `templates/` - デプロイ対象テンプレート（install.sh で ~/.claude/ 等に反映）
- `templates/AGENTS.md` - Codex CLI 向け共通方針
- `templates/CLAUDE.md` - Claude Code 向け共通方針
- `.claude/` - このプロジェクト固有の設定
- `docs/` - ドキュメント

## 注意

- テンプレートの編集は `templates/` 配下で行う
- `install.sh` 実行でテンプレートがホームディレクトリに反映される
- 作業用の計画メモは repo 直下の `.plan/` に置き、git には含めない

## レビュー方針（運用テスト）

このリポジトリの成果物はプロンプト・ルール・スキルそのものであり、diff の静的レビューだけでは「意図した挙動改善が実際に起きるか・既存挙動を退行させないか」を確認できない。`templates/skills` 配下の変更は、採用前に `km-skill-improve` の検証プロトコル（レベル選択・変更タイプに応じた A/B 運用テスト）で実挙動を確かめる。skill 以外の `templates/` 配下（rules / CLAUDE.md 等）の変更も、同プロトコルに準じた A/B 運用テストで確かめる。時間・コストがかかってもよい。試したシナリオ・期待挙動・実挙動・判定は PR またはレビュー報告に残す。
