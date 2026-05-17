# ISO/IEC 25010:2023 References

ソフトウェア品質特性の参照リソース。9 特性 × 39 副特性 を網羅 (ISO/IEC 25010:2023 公式 + 業界実務で重要な拡張観点を一部含む)。`km:review` Phase 3 の 3 専門家が担当分を Read するほか、人間が一般知識として学習する用途にも使う。

## File Index

| # | 特性 | ファイル | 副特性数 |
|---|---|---|---|
| 1 | 機能適合性 (Functional Suitability) | [1-functional-suitability.md](1-functional-suitability.md) | 3 |
| 2 | 性能効率性 (Performance Efficiency) | [2-performance-efficiency.md](2-performance-efficiency.md) | 3 |
| 3 | 互換性 (Compatibility) | [3-compatibility.md](3-compatibility.md) | 2 |
| 4 | インタラクション能力 (Interaction Capability) | [4-interaction-capability.md](4-interaction-capability.md) | 7 |
| 5 | 信頼性 (Reliability) | [5-reliability.md](5-reliability.md) | 4 |
| 6 | セキュリティ (Security) | [6-security.md](6-security.md) | 6 |
| 7 | 保守性 (Maintainability) | [7-maintainability.md](7-maintainability.md) | 5 |
| 8 | 柔軟性 (Flexibility) | [8-flexibility.md](8-flexibility.md) | 4 |
| 9 | 安全性 (Safety) | [9-safety.md](9-safety.md) | 5 |

合計 39 副特性 (`3+3+2+7+4+6+5+4+5`)。

## Expert Mapping (km:review Phase 3)

| 専門家 | 担当特性 | 視点 |
|---|---|---|
| architect | 2, 3, 7, 8 | 長期・横断・非機能 |
| qa | 1, 4, 5 | 異常系・境界・運用品質 |
| security | 6, 9 | 脅威モデル・攻撃面 |

## Format Conventions

各ファイルの構造:

- **見出しレベル**: 特性 = H1、副特性 = H2、checklist = `- [ ]`
- **特性ヘッダ直下**: 1 文の特性スコープ
- **副特性ヘッダ直下** (任意): 他副特性との住み分けを 1 行で明示 (例: 「正常時の資源使用観点 (異常時の解放漏れは 5-信頼性 / 回復性側)」)
- **観点 (checklist)**: 1 行・検証可能・疑問形「〜か」で統一 (二値判断しやすい)
- **副特性名**: ISO 公式 2023 版の正式名 (日本語 + 英語併記)
- **末尾の参照**: ISO/IEC 25010:2023 + 関連標準 (OWASP / CWE / SRE / CNCF / NIST / RFC / WCAG など)

## diff レビューでの取り扱い

checklist には diff から直接判定できない観点 (例: ADR の存在、IaC / 計装の semantic convention 準拠) も含まれる。expert は diff から裏づけられない観点を `[possible]` 確信度で扱い、必要に応じて「判定保留 (audit-only)」として記録する。検出が diff コンテキストに収まらないなら指摘化せず、`possible` のまま重大度を 1 段下げる。

## 関連標準 (2026 年 5 月時点最新)

- ISO/IEC 25010:2023
- OWASP Top 10 (現行版を確認: 2025 リリース済), OWASP API Security Top 10 (2023), OWASP LLM Top 10
- CWE Top 25
- SLSA, Sigstore (アーティファクト来歴)
- Anthropic AI safety policy
- RFC 9457 (Problem Details for HTTP APIs), RFC 9110 (HTTP Semantics)
- WCAG 2.2
- Google SRE Workbook (SLO / observability)
- CNCF cloud-native deployment patterns
- The Twelve-Factor App
