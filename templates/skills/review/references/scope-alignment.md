# Phase 2 と Phase 3 architect の住み分け

`code-review.md` (Phase 2) と `experts/architect.md` (Phase 3 architect) は重複しないように設計されている。同じコードを 2 回深く読むのではなく、**異なる視点 (時間軸・関心事・粒度)** からレビューする。

## 基本原則

| Phase | 視点 | 主たる関心 |
|---|---|---|
| Phase 2 (code-review) | コードレベルの正しさ | 現在の diff が壊しうる関数・モジュール・システム境界の bug / 設計不整合 |
| Phase 3 architect | 長期・横断・非機能 | 時間軸とシステム全体の整合。将来の進化や横断的影響 |

Phase 2 は「今この diff は正しいか」、Phase 3 architect は「この diff が repo の長期的な健全性や互換性連鎖に与える影響は何か」を見る。

## 判定ルール

判定に迷ったら以下の問いに答える:

1. **指摘の根拠が「現在の diff の中だけ」で完結するか?**
   - YES → Phase 2
   - NO (他の consumer / 他のモジュール / 将来の変更との関係で問題になる) → Phase 3 architect

2. **指摘が修正されないと「今すぐ動かない」か、それとも「将来困る」か?**
   - 今すぐ動かない (bug、レイヤー違反、リソースリーク) → Phase 2
   - 将来困る (技術負債、互換性連鎖、保守コスト増) → Phase 3 architect

3. **その指摘は「規約への準拠」か「アーキ判断との整合」か?**
   - 規約準拠 (lint で拾えるレベル、命名、コメント、関数長) → Phase 2
   - アーキ判断との整合 (パターン選択、責務分割、進化方向) → Phase 3 architect

## 具体例

### Phase 2 (code-level: 現在の diff が壊すか)

- `api/v2/users.ts:42` の入力検証が抜けている (current diff の bug)
- モジュール `db/orm` が `ui/components` を import (レイヤー違反)
- HTTP handler が DB トランザクションを finally でクローズしていない (リソースリーク)

### Phase 3 architect (長期・横断・非機能: 将来や全体への影響)

- 公開 API の型契約変更で 3 consumer に互換性問題が連鎖 (横断・互換性)
- 現在の循環参照は実害ないが、今後 N 回のスケール展開で保守性悪化 (長期・保守性)
- チーム全体のアーキ判断 (例: Repository pattern) からの逸脱 (横断整合)
- 認証経路の責務が 3 モジュールに散らばり、後続のセキュリティ要件追加で修正点増加 (長期保守性、変更波及)

## 重複指摘が出た場合

Phase 2 と Phase 3 architect で同観点の重複が発生した場合の表示・カウントルールは **`experts/report-format.md` の「Phase 2 との重複時 (SOT ルール)」** に集約してある。本ファイルでは住み分けの判定ルールのみを管轄し、重複処理は SOT 側に従う。
