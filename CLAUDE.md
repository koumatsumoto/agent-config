# agent-config

Claude Code / Codex CLI（および opt-in で Qwen Code）の共通設定テンプレートを管理するリポジトリ。

## 構成

- `templates/` - デプロイ対象テンプレート（install.sh で ~/.claude/ 等に反映）
- `templates/CLAUDE.md` - Claude Code / Codex CLI / Qwen Code 共通 agent guideline の唯一の正本。`~/.claude/CLAUDE.md`・`~/.codex/AGENTS.md`・`~/.qwen/QWEN.md`（`--qwen` 時のみ）へ同じ内容を配布する
- `.claude/` - このプロジェクト固有の設定
- `docs/` - ドキュメント

## 注意

- テンプレートの編集は `templates/` 配下で行う
- 共通 guideline はツール非依存に保つ。モデル・reasoning effort・sandbox・承認ポリシー等の実行時設定は各ツール固有の設定ファイル側に置く
- Qwen Code 向けの配布は opt-in。`--qwen` は通常の配布対象へ Qwen component を追加する additive flag で、`install` / `verify` / `clean` で同じ意味を持つ
- `install.sh` 実行でテンプレートがホームディレクトリに反映される
- 作業用の計画メモは repo 直下の `.plan/` に置き、git には含めない

## レビュー方針（運用テスト）

このリポジトリの成果物はプロンプト・ルール・スキルそのものであり、diff の静的レビューだけでは「意図した挙動改善が実際に起きるか・既存挙動を退行させないか」を確認できない。`templates/` 配下の挙動資産（skill / rules / CLAUDE.md 等）の変更は、採用前に `km-skill-improve` の検証プロトコル（計測器の選択・変更タイプに応じた A/B 運用テスト）で実挙動を確かめる。skill 以外の単体ファイルでは、版の渡し方と bank の置き場を読み替えて同プロトコルを適用する。時間・コストがかかってもよい。試したシナリオ・期待挙動・実挙動・判定は PR またはレビュー報告に残す。
