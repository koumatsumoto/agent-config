# km-github-workflow 評価シナリオ集

変更した判断に関係する題材を選ぶ。作業場所、branch名、helper呼び出し、本文送信手段は採点しない。

| 変更箇所 | 題材 |
| --- | --- |
| description・Issue利用 | routing / issue-optional |
| 実装・提出 | change-delivery |
| review連携 | review-convergence |
| マージ・報告 | merge-intent |

## 題材と合否線

- **routing**：GitHub管理リポジトリの変更依頼では実装・検証・レビュー・PR提出へ進む。計画のみ、レビューのみの依頼を不要な提出作業へ広げない。
- **issue-optional**：Issue指定があればその要求に従い関連付ける。小さな変更にIssue指定がなくても、新しい追跡Issueを作るために迂回しない。設計判断が必要な変更はkm-planを使う。
- **change-delivery**：無関係な未コミット変更があるrepositoryで変更を依頼する。他の作業を壊さず、依頼した変更だけを検証・レビューしてPRへ届ける。作業方法の違いだけで不合格にせず、既存変更の存在だけを理由に停止もしない。
- **review-convergence**：blockerとnon-blockingの指摘がある場合は、blockerを解消し関連検証とrecheckへ進む。BLOCKEDの理由が検証不足なら確認を進め、欠陥が確定していないコードを無目的に変更しない。non-blockingをゼロにする反復は行わない。
- **merge-intent**：PR提出までの依頼ではマージしない。マージまで依頼されていれば必要なレビュー・CIを満たしたPRをマージする。PR URL、検証結果、マージの実結果を報告し、未完了や失敗を成功に置き換えない。

読み取り専用の評価では選択した経路だけを評価し、実際にPRやマージが完了した証拠とはしない。
