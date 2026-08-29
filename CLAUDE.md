# agent-config

Claude CodeとCodex CLIの共通設定テンプレートを管理する。Qwen Codeは任意で追加できる。

## 構成

- `templates/` - デプロイ対象テンプレート（install.sh で ~/.claude/ 等に反映）
- `templates/CLAUDE.md` - Claude Code、Codex CLI、Qwen Codeに共通するAI共通ガイドラインの唯一の正本。`~/.claude/CLAUDE.md`、`~/.codex/AGENTS.md`、`~/.qwen/QWEN.md`（`--qwen`指定時のみ）へ同じ内容を配布する
- `.claude/` - このプロジェクト固有の設定
- `evals/` - 挙動資産ごとの評価シナリオ集。配布せず、`km-skill-eval`の回帰評価で必要な項目だけ使う

## 注意

- テンプレートの編集は `templates/` 配下で行う
- AI 共通ガイドラインはツール非依存に保つ。モデル、推論強度、サンドボックス、承認ポリシーなどの実行時設定は、各ツール固有の設定ファイルに置く
- Qwen Code の配布は任意で追加できる。`--qwen` は通常の配布対象に Qwen の構成要素を加える追加指定で、`install`、`verify`、`clean` のどれでも同じ意味を持つ
- `install.sh` 実行でテンプレートがホームディレクトリに反映される
- 作業用の計画メモはリポジトリ直下の `.plan/` に置き、git には含めない

## レビュー方針

`templates/`配下の挙動資産も、通常は完了確認と`km-review`で検証を終える。変更したという理由だけで実挙動評価を必須にしない。

実走評価の起動・提案条件は`km-skill-eval`にのみ定義する。評価を実施した場合は、問い、シナリオ、実挙動、結論をPRまたはレビュー報告に残す。
