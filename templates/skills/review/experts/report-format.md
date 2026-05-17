# 第三者専門家レビュー 共通出力フォーマット

km:review Phase 3 の 3 専門家 (architect / qa / security) が共通で従う出力規約。orchestrator は各専門家の出力を Phase 5 で合算する。

専門家固有の役割定義 / 担当 ISO 副特性 / 主観点は `architect.md` / `qa.md` / `security.md` を参照。本ファイルでは **出力構造・重大度判定・確信度・偽陽性フィルタ** を一本化する。

## 出力構造

```
### <システムアーキテクト | QA 専門家 | セキュリティ専門家>
CRITICAL: 0 / HIGH: 1 / MEDIUM: 2 / LOW: 0

## HIGH: [問題タイトル] [confirmed | likely | possible]
**場所**: src/api/users.ts:42
**観点**: <担当 ISO 副特性 (例: 7-保守性 / 修正性 (Modifiability))>
**問題**: 何が問題か (2-4 文で具体的に)
**修正**: どう直すべきか (具体的な対応)
**根拠**: diff / 担当 ISO reference のどの観点に該当するか
<役割固有フィールド (HIGH 以上必須、下記参照)>

## MEDIUM: [問題タイトル]
**場所**: ...
**観点**: ...
**問題**: ...
**修正**: ...
**根拠**: ...
```

専門家名: `architect` → `### システムアーキテクト` / `qa` → `### QA 専門家` / `security` → `### セキュリティ専門家`。

指摘ゼロのとき:

```
### <専門家名>
CRITICAL: 0 / HIGH: 0 / MEDIUM: 0 / LOW: 0
（指摘なし）
```

## 重大度の判定

- `CRITICAL`: 即時悪用可能 / 重大インシデント直結 / 即時データ損失
- `HIGH`: 明確なバグ、仕様回帰、危険な未検証入力、長期保守を直撃する設計欠陥、明確な脆弱性
- `MEDIUM`: 設計不整合、品質特性の低下、テスト不足、技術負債蓄積の兆候
- `LOW`: 小さな改善、意図的に残してもよい指摘

`CRITICAL` または `HIGH` があれば orchestrator は Phase 4 の起動を阻み、Phase 5 で BLOCKED 報告して終了する。

## 確信度ラベル

- `[confirmed]`: diff から直接裏づけ可能、誤検出の可能性ほぼゼロ
- `[likely]`: diff + repo context から推測、コンテキスト次第で偽陽性の可能性あり
- `[possible]`: 一般的な観点として該当しうるが、本変更で実害が出るかは別途確認要

`possible` の指摘は重大度を 1 段下げる (例: HIGH → MEDIUM) ことを検討する。

## 偽陽性フィルタリング

以下は除外する:

- 今回の diff で導入されていない既存問題 (security は新規 attack surface に既存問題が露呈する場合のみ報告)
- 担当外 ISO 副特性に該当する指摘 (他の専門家の担当)
- Phase 2 で既に確定済みの MEDIUM/LOW と同じ観点で **補強情報も重大度再評価もない** もの (詳細は本ファイル末尾「Phase 2 との重複時 (SOT ルール)」)
- 合意済みの設計判断 (intent context があれば確認)
- 未変更行だけに対する指摘
- diff から裏づけられない一般論だけの推測 (security では「攻撃シナリオが現実的でない」を含む)

## 役割固有フィールド (HIGH 以上必須)

### architect: `**長期影響**`

```
**長期影響**: 3 つの consumer (web, mobile, partner-api) に互換性問題が連鎖。SemVer の major bump が必要
```

### qa: `**再現条件**`

```
**再現条件**: 2 並列実行 + DB writes が 100ms 以内
```

### security: `**攻撃シナリオ**` + CWE/OWASP 引用 (引用は `**根拠**` 内に記載)

```
**攻撃シナリオ**: 悪意のユーザが special character を含む header を送信すると...
**根拠**: diff L78 の handler に所有者検証なし。OWASP API Top 10 (2023) API1: BOLA
```

## 判定保留 (context 不足)

該当観点があるが diff だけでは判定しきれない場合、独立セクションに記録する:

```
## 判定保留 (context 不足)
- **観点**: 6-セキュリティ / 真正性
- **何が必要か**: middleware 層での認証適用状況
- **暫定見解**: 認証 middleware が他で適用済なら問題なし、なければ HIGH 相当
```

## Phase 2 との重複時 (SOT ルール)

Phase 2 と同観点 (`(file_path, 影響行範囲 ±5 行, 問題タイトルの正規化結果)` の組が一致) で Phase 3 expert が出力する場合の **単一情報源**。SKILL.md (orchestrator) と scope-alignment.md はここを参照する。「問題タイトルの正規化結果」は Phase 2 / Phase 3 共通の `## <重大度>: <問題タイトル>` 行から重大度ラベルを除き、空白・記号を正規化した文字列を指す。

| パターン | expert 側 | カウント / 表示 |
|---|---|---|
| **A: 追加情報なし** | 出力しない | Phase 2 側のみ |
| **B: 補強情報あり** (攻撃シナリオ / 再現条件 / 長期影響、重大度は据え置き) | 重複注記のみ末尾追記 | Phase 2 側カウント、注記は Phase 2 直下に併記 |
| **C: 重大度の再評価** (例: Phase 2 MEDIUM → security HIGH) | 新規セクションで出力 | Phase 3 側採用、Phase 2 側の同観点は drop (Phase 2 セクション末尾に注記) |

補強可能条件: `qa` は「複数経路の連鎖」または「運用での再現条件」が加わる場合のみ。`architect` は新規 attack surface 露呈 / 長期影響のみ。`security` は重大度再評価可。

### 補強注記フォーマット (パターン B)

```
## 重複注記 (Phase 2 の指摘を補強)
- Phase 2 指摘: `<Phase 2 の問題タイトル>`
- Phase 3 視点の追加情報: 攻撃シナリオ / 長期影響 / 再現条件のうち該当するものだけ
```
