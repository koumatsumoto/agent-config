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
