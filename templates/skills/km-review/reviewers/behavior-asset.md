# 挙動資産

skill、rule、共通ガイドライン、command、output-styleなど、AIに読み込まれて挙動を規定する資産へ選択した観点を適用する。

- `architect` — 正本、責務、優先順位、ロード境界、重複、不要な分岐とcontext増大、下流skillとの契約
- `product` — 起動条件、対象範囲、委譲境界、期待するAIの成果
- `reliability` — gate、既定値、収束条件、marker、reference、出力契約、既存シナリオへの回帰
- `security` — tool実行、外部書き込み、秘密情報、権限、公開・永続化、untrusted inputとprompt injection

最小コストで字面どおりに従う読者を想定し、安全確認や収束が抜けないかを見る。新設・分岐した副経路が本経路のgateを継承しているかを確認する。

人間向けのREADME、runbook、設計説明、CHANGELOGは、それ自体がAIの挙動を規定しない限り挙動資産ではない。
