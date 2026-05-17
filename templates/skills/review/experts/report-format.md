# 第三者専門家レビュー 共通出力フォーマット

km:review Phase 3 の 3 専門家 (architect / qa / security) が返すレポートの形式。orchestrator は各専門家の出力を Phase 5 で合算する。

## 出力構造

```
### <専門家名> (architect / QA / security)
CRITICAL: 0 / HIGH: 1 / MEDIUM: 2 / LOW: 0

## HIGH: [問題タイトル] [confirmed | likely | possible]
**場所**: src/api/users.ts:42
**観点**: <担当 ISO 副特性>
**問題**: 何が問題か (2-4 文で具体的に)
**修正**: どう直すべきか (具体的な対応)
**根拠**: diff / 担当 ISO reference のどの観点に該当するか

## MEDIUM: [問題タイトル]
**場所**: ...
**観点**: ...
**問題**: ...
**修正**: ...
**根拠**: ...
```

確信度ラベル:
- `[confirmed]`: diff から直接裏づけ可能、誤検出の可能性ほぼゼロ
- `[likely]`: diff + repo context から推測、コンテキスト次第で偽陽性の可能性あり
- `[possible]`: 一般的な観点として該当しうるが、本変更で実害が出るかは別途確認要

確信度が `possible` の指摘は重大度を 1 段下げる (例: HIGH → MEDIUM) ことを検討する。

## 専門家名の表記

- architect → `### システムアーキテクト`
- qa → `### QA 専門家`
- security → `### セキュリティ専門家`

## 指摘ゼロのとき

```
### <専門家名>
CRITICAL: 0 / HIGH: 0 / MEDIUM: 0 / LOW: 0
（指摘なし）
```

## 重大度の判定

- `CRITICAL`: 即時悪用可能 / 重大インシデント直結
- `HIGH`: 明確なバグ、仕様回帰、危険な未検証入力、長期保守を直撃する設計欠陥
- `MEDIUM`: 設計不整合、品質特性の低下、テスト不足、技術負債蓄積の兆候
- `LOW`: 小さな改善、意図的に残してもよい指摘

`CRITICAL` または `HIGH` があれば orchestrator は Phase 4 の起動を阻む (Sequential gating)。

## 偽陽性フィルタリング

各専門家は以下を除外する:

- 今回の diff で導入されていない既存問題
- 担当 ISO 副特性に該当しない指摘 (他の専門家の担当)
- 合意済みの設計判断
- 未変更行だけに対する指摘
- diff から裏づけられない一般論だけの推測
- Phase 2 で既に確定済みの MEDIUM/LOW 指摘 (orchestrator から共有される) と同じ観点

## 担当 ISO 副特性との対応

各指摘の `**観点**` フィールドには、担当 ISO 副特性名を記載する。例:

- architect の場合: `**観点**: 7-保守性 / 修正性 (Modifiability)`
- qa の場合: `**観点**: 5-信頼性 / 障害許容性 (Fault Tolerance)`
- security の場合: `**観点**: 6-セキュリティ / 完全性 (Integrity)`

これにより、Phase 5 統合時に 9 特性のどこに集中しているかが俯瞰しやすくなる。

## 専門家固有の追加情報

各専門家固有のフィールドは **HIGH 以上で必須**。任意で MEDIUM/LOW にも添付可。これが欠落すると Phase 5 統合時に指摘の説得力が落ち、ユーザがマージ判断に使いづらくなる。

### architect

`**長期影響**` フィールド (HIGH 以上必須):

```
## MEDIUM: 公開 API 契約の波及
**場所**: src/api/v2/users.ts:42
**観点**: 3-互換性 / 相互運用性 (Interoperability)
**問題**: ...
**修正**: ...
**長期影響**: 3 つの consumer (web, mobile, partner-api) に互換性問題が連鎖。SemVer の major bump が必要
**根拠**: ...
```

### security

`**攻撃シナリオ**` フィールド (HIGH 以上必須) と CWE/OWASP 引用 (HIGH 以上必須):

```
## HIGH: 入力検証バイパス
**場所**: src/auth/middleware.ts:18
**観点**: 6-セキュリティ / 完全性 (Integrity)
**問題**: ...
**修正**: ...
**攻撃シナリオ**: 悪意のユーザが special character を含む header を送信すると...
**根拠**: ...
```

### qa

`**再現条件**` フィールド (HIGH 以上必須):

```
## HIGH: 競合状態
**場所**: src/jobs/processor.ts:55
**観点**: 5-信頼性 / 障害許容性 (Fault Tolerance)
**問題**: ...
**修正**: ...
**再現条件**: 2 並列実行 + DB writes が 100ms 以内
**根拠**: ...
```

## 判定保留 (context 不足)

該当観点があるが diff だけでは判定しきれない場合、独立セクションに記録する:

```
## 判定保留 (context 不足)
- **観点**: 6-セキュリティ / 真正性
- **何が必要か**: middleware 層での認証適用状況
- **暫定見解**: 認証 middleware が他で適用済なら問題なし、なければ HIGH 相当
```

## Phase 2 との重複時

Phase 2 で既に同観点が確定済みの場合、新規セクションを作らず以下を末尾に記載:

```
## 重複注記 (Phase 2 の指摘を補強)
- Phase 2 指摘: `<Phase 2 の問題タイトル>`
- Phase 3 視点の追加情報: 攻撃シナリオ / 長期影響 / 再現条件のうち該当する補強情報のみ
```
