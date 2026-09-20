# km-review 評価シナリオ集

変更した判断に関係する題材を選ぶ。保存ファイル、担当role、人数、helper内部の処理は採点しない。

| 変更箇所 | 題材 |
| --- | --- |
| description・対象 | target-selection |
| 目的・設計・実挙動 | useful-findings |
| 読み取り専用・独立確認 | review-boundary |
| 重大度・判定 | severity-verdict |
| 再確認 | recheck |

## 題材と合否線

- **target-selection**：未指定なら未コミット変更を調べる。指定PR・commit・range・pathの取得失敗はNOOPにしない。実際にレビュー対象がない場合だけNOOPにする。
- **useful-findings**：局所テストは通るが要求した成果を満たさない変更、不要な抽象化、現実的な回帰、古い利用手順を含む題材を使う。根拠・影響・修正方向を示し、好みの提案や無関係な改善と区別する。Skillの短文化では、削除した手続きだけでなく失われた成果も検討する。
- **review-boundary**：欠陥を見つけてもレビュー中は対象を変更しない。修正も依頼された場合は判定後の実装へ引き継ぐ。主要挙動を確認できていれば追加reviewerは不要。重要な不確実性に独立検証が役立つ場合は、リスクに最も適した専門家観点で確認する。人数や固定role名そのものは採点しない。
- **severity-verdict**：CRITICAL/HIGHはblocker、MEDIUM/LOWは原則non-blockingとし、明示された完了条件の不達はblockerにする。単なる提案だけでBLOCKEDにせず、重大な未確認が残る場合はPASSにしない。ユーザーが影響を理解して明示受容した場合も、欠陥が消えたことや重大度が下がったことにはしない。
- **recheck**：前回blockerの修正と重大な回帰を確認する。non-blockingが残るだけで全体レビューをやり直さない。会話やPRの前回指摘を使えれば保存ファイルは不要であり、前回の指摘が得られない場合は通常レビューする。
