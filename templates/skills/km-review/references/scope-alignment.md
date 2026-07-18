# Phase 2 と Phase 3 architect の住み分け

`code-review.md` (Phase 2) と `experts/architect.md` (Phase 3 architect) は同じコードを **異なる視点 (時間軸・関心)** から見る。重複指摘は出てよく、集約は Phase 4 が一括で行う (本ファイルは dedup の判断材料であり、レビュアの報告抑制の根拠にしない)。

| Phase | 視点 | 主たる関心 |
|---|---|---|
| Phase 2 (code-review) | コードレベルの正しさ | 現在の diff が壊しうる関数・モジュール・システム境界の bug / 設計不整合 |
| Phase 3 architect | 長期・横断・非機能 | 時間軸とシステム全体への影響。将来の進化・横断的波及 |

## 判定 (迷ったら)

1. 指摘の根拠が **現在の diff の中だけ**で完結する → Phase 2 / 他 consumer・他モジュール・将来変更との関係で問題 → architect
2. **今すぐ動かない** (bug・レイヤー違反・リソースリーク) → Phase 2 / **将来困る** (技術負債・互換性連鎖・保守コスト増) → architect
3. **規約準拠** (命名・コメント・関数長) → Phase 2 / **アーキ判断との整合** (パターン選択・責務分割・進化方向) → architect

例: 1 ファイル内で完結する循環 import の初期化順序 → Phase 2 (current diff 内の構造) / 同じ循環 import が repo 全体 5 箇所に拡散 → architect (横断・長期保守性)。

なお Phase 2 も code-review.md Step 2 の範囲 (前提の能動破壊・diff 外照合による不変条件の継承) を行うが (主担当は Phase 3 adversary、重複は Phase 4 dedup が吸収)、これは code-level 正しさ検査であり上表の architect との住み分けは変えない。
