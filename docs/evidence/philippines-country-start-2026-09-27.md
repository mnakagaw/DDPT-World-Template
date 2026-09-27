# フィリピン国別版・開始シート（AI記入、2026-09-27）

`templates/COUNTRY_START.md`に対応。アジア50件の段階3・東南アジア、国ID `PHL`。独立したignored候補は `generated/philippines-areadata-20260927`。**部分成果・未公開**。[原本監査](philippines-popcen-source-audit-2026-09-27.md)を参照。

| 項目 | 採用・確認 | 不足・次の行動 |
|---|---|---|
| 納品と場所 | AreaData branch `codex/asia-domestic-20260926` にコード、台帳、公開可能なsource所在を保存。原本とsiteは国別ignored候補。 | 独立`ACCEPT`、Philippines固有のHosting/Public先、運用者・更新周期。DDPTの公開先を転用しない。 |
| 仕様 | 共通の地域診断・テーマ比較・DB・計画資料とschema 0.2を保持。国名だけの依頼から開始票・差分契約をAI記入。 | UX v1.0最終採用、現地語・現地利用者の受入。 |
| 国内統計 | PSA 2024 POPCEN Table A/Bの2024直接人口を、全国＋1,743報告行へ接続。全国112,729,484人。 | Table C 42,004バランガイの数値照合、他テーマ、過去年・PGRの意味監査。 |
| 地理・コード | 2024年6月30日Q2 PSGCの18 Region、82 Province、149 City、1,493 Municipalityと対照。SGAはコードなしの別集計。101親子2024合計は全一致。 | 10件の歴史値・名称差の精査、公式2024対応図形、法定LGU境界。古いprovider図形は除外。 |
| 計画主体・資料 | RA7160 §106/109/114とDILG CDP手引き、Quezon CityのCDP/LDIP/AIP/予算の実PDFと市議会記録を確認。 | 全文・現行改正・適用様式、他LGU資料、支出・実施・評価。AIP金額と予算額は区別。 |
| 国際共通source | 初期生成のWDI全国年次系列はPOPCEN 2024と別指標。 | 他共通sourceの国・テーマ・年・粒度別availabilityと採否。 |
| 利用条件と公開 | PSA30原本と計画6 PDFをURL/bytes/hashで固定し、26 XLSX・161 sheetsの数値列を棚卸し。候補は未公開。 | 原本再配布条件、42シナリオ、独立監査、Hosting/Public先。 |

代表確認は全国、NCR、Quezon City、Makati、Taguig、NIR、BARMM、Maguindanao del Norte、Sulu、SGA。10例の実出力、ブラウザーで全国→NCR→Quezon City→同じNCR全体への再選択と資料消去を確認。Word/PDF、狭画面、全市町村の実画面、現地担当者確認は未実施。
