# agent-config

Claude Code / Codex CLI（および opt-in で Qwen Code）の共通設定テンプレートを管理するリポジトリ。

## 構成

- `templates/` - デプロイ対象テンプレート（install.sh で ~/.claude/ 等に反映）
- `templates/CLAUDE.md` - Claude Code / Codex CLI / Qwen Code 共通 agent guideline の唯一の正本。`~/.claude/CLAUDE.md`・`~/.codex/AGENTS.md`・`~/.qwen/QWEN.md`（`--qwen` 時のみ）へ同じ内容を配布する
- `.claude/` - このプロジェクト固有の設定
- `evals/` - 挙動資産ごとの scenario bank（再走トリガ・題材と合否線・落とし穴）。配布しない検証材料
- `docs/` - ドキュメント

## 注意

- テンプレートの編集は `templates/` 配下で行う
- 共通 guideline はツール非依存に保つ。モデル・reasoning effort・sandbox・承認ポリシー等の実行時設定は各ツール固有の設定ファイル側に置く
- Qwen Code 向けの配布は opt-in。`--qwen` は通常の配布対象へ Qwen component を追加する additive flag で、`install` / `verify` / `clean` で同じ意味を持つ
- `install.sh` 実行でテンプレートがホームディレクトリに反映される
- 作業用の計画メモは repo 直下の `.plan/` に置き、git には含めない

## レビュー方針

このリポジトリの成果物はプロンプト・ルール・スキルそのものだが、`templates/` 配下の挙動資産（skill / rules / `CLAUDE.md` 等）の変更も、通常は完了確認と `km-review` で閉じる。変更したという事実だけで実挙動の評価を課さない。

変更効果に重要な不確実性が残り、それが実走でしか解消できず、結果が採否を変えうるときだけ、`km-skill-eval` の最小の評価案を提案してよい。ユーザーの明示指示か、提案への同意を得る前には起動しない。評価を実施した場合は、問い・シナリオ・実挙動・結論を PR またはレビュー報告に残す。
