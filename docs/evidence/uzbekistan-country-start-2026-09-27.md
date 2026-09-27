# Uzbekistan 国別候補・開始シート（AI記入、2026-09-27）

`templates/COUNTRY_START.md`対応。アジア50件の段階4・中央アジア、`UZB`。保存先は独立・ignored候補`generated/uzbekistan-areadata-20260927`。参照実装0.4／dataset schema 0.2。UX v1.0の最終採用や公開ではない。[原本監査](uzbekistan-siat-census2026-source-audit-2026-09-27.md)と[Task Contract](uzbekistan-task-contract-2026-09-27.md)を参照。

| 項目 | 今回の範囲 | 不足・次の行動 |
|---|---|---|
| 納品と公開 | AreaDataの`codex/asia-domestic-20260926`へ再実行コード・hash台帳・監査を保存。原本と生成サイトは候補内。 | UZB専用Hosting/Public先、更新責任者、独立`ACCEPT`は未設定。公開しない。 |
| 地方統計 | SIAT 2026年1月1日推計、全国＋14州級＋206地区／市、5指標1,105直接値。別系列の2026年1月15日国勢調査速報、全国＋14州級、5指標75直接値。 | SIAT過去年・速報他25表・農業11 sheet、将来の確報は未採用。全国WDI年央推計を地方値へ転用しない。 |
| 地理 | SIAT COATOコードと全親子を保持。Tashkent州と市を別ID。 | 2026年の同版公式図形、国勢調査行の公式コード、現行行政変更の対照は未取得。2017年参照図形を除外。 |
| 計画・予算 | 全国PF-21、ASDRの14地域戦略準備課題、MOF地方予算表の所在を表示。 | 個別計画本文・承認、地区の法的権限・様式、予算表の期間/実績の意味、支出・評価は未確認。 |
| 国際共通source | 初期WDI全国系列を別定義で保持。 | HAPI/UNHCR/DTM/IPC/MICS/DHS/WorldPop/GHSL/SALB/WaPOR等のUZB×テーマ×年×粒度のavailabilityは未確認。 |
| 利用条件 | SIAT catalogueのCC BY 4.0表示を記録し原本をhash固定。大きいPDF/XLSX/HTML原本はGitに入れない。 | 他の原本、地理資料、計画の二次利用・公開条件を資料別に確認する。 |

代表地域は全国、Karakalpakstan共和国・Nukus市・Bozatau地区、Andijan州・市、Tashkent州・Tashkent市・Yangikhayot地区。9地域の実出力と画面選択を確認。全表印刷、狭幅、多言語の完成、現地担当者による検証、42シナリオ全件、独立監査は未実施。
