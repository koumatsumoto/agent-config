# agent-config

Claude CodeとCodex CLIの共通設定テンプレートを管理する。

## 注意

- テンプレートの編集は `templates/` 配下で行う。Codex向けガイドラインの唯一の正本は `templates/AGENTS.md` とし、`~/.codex/AGENTS.md`へ配布する。このファイルはリポジトリ作業用の指示であり、配布対象ではない
- AI 共通ガイドラインはツール非依存に保つ。モデル、推論強度、サンドボックス、承認ポリシーなどの実行時設定は、各ツール固有の設定ファイルに置く
- `install.sh` 実行でテンプレートがホームディレクトリに反映される
- 作業中だけ必要なメモは、OSまたは実行環境が提供する一時領域に置く

## レビュー方針

`templates/`配下の挙動資産も、通常は完了条件との照合と読み取り専用のレビューで検証を終える。変更したという理由だけで実挙動評価を必須にしない。

変更後は`python3 -m unittest discover -s scripts/tests -t scripts -v`と、隔離した一時HOMEでシェルラッパーのinstall / verify / cleanを確認する。実ユーザーの設定へ検証目的でinstallしない。
