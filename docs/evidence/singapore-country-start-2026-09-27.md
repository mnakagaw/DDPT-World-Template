# Singapore 国別候補・開始シート（AI記入、2026-09-27）

`templates/COUNTRY_START.md`に対応。アジア50件の段階3・東南アジア、`SGP`。独立ignored候補 `generated/singapore-areadata-20260927`。**公式地方統計と全国MP2025の部分成果・未公開**。[原本監査](singapore-population2026-source-audit-2026-09-27.md)と[Task Contract](singapore-task-contract-2026-09-27.md)を参照。

| 項目 | 確認した範囲 | 不足・次の行動 |
|---|---|---|
| 作業・納品 | AreaData `codex/asia-domestic-20260926`に取得・監査・importコード、公開可能なsource所在を保存。原本とbuildはignored候補。参照実装0.4、dataset schema 0.2。 | 独立`ACCEPT`、SGP専用Hosting/Public先、現地運用者・更新担当・利用条件は未設定。 |
| 目的・地域 | 全国→55 Planning Area→332 Subzoneで地域診断、同年比較、出典付きCSV/HTML/Markdown、計画資料を使う。5 Regionは原本保持だけ。 | Subzoneは法定計画主体ではなく、MP2025コード/図形未取得。計画策定主体・適用様式はURA等の制度で確認。 |
| 国内統計 | SingStat 2026 ZIPの全3冊7sheet、456,288行・244,240数値と212,048 `-` を棚卸し。6指標1,489観測＋839欠測を採用。 | 他の年齢・住宅・床面積、2020国勢調査詳細表は意味監査未了。 `-`は0ではない。 |
| 地理 | SingStat 2026とURA MP2025の55区域名が一致。55区域のURAコードと参考図形を接続。 | SubzoneのMP2025公式コード/図形、MP2019→2025対照、5 Regionの直接2026値は未取得。 |
| 計画制度 | Planning Act 1998 Part 2所在、URA MP2025 Written Statement本文26頁、2025-12-01官報化通知。国全体の法定土地利用計画。 | 全区域の実施・予算・実支出・評価本文と計画全章の意味監査は未了。国のMaster Planを区域別独立計画としない。 |
| 国際source | 初期WDI全国系列は別母集団・年の参考系列として保持。 | HDX等の共通候補のSGP availabilityは未確認。 |
| 利用条件 | data.gov.sgのGeoJSON/CSVにOpen Data Licence表示。7原本hash固定、原本はGitに含めない。 | SingStat ZIP/PDF・法令/計画PDFの再配布条件と各素材の用途を別途確認。 |

代表確認は全国、Tampines/Tampines East（親子再選択）、Ang Mo Kio（異なる居住地）、Changi Bay（`-`欠測）。実出力5地域と画面の一部を原本照合。Word/PDF、実印刷全頁、狭幅/低帯域、現地担当者、42件全適用は未実施。指標・時点・地域と資料・出力先を同期し、全国直接値を地方へ配分しない。
