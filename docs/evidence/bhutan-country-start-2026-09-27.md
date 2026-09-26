# ブータン国別版・開始シート（AI記入、2026-09-27）

`templates/COUNTRY_START.md`に対応。アジア50件の段階2南アジア、`BTN`。新規ignored候補は`generated/bhutan-areadata-20260927`。**部分成果・未公開**。[原本監査](bhutan-phcb2017-source-audit-2026-09-27.md)を参照。

| 項目 | 採用・確認 | 不足・次の行動 |
|---|---|---|
| 納品と場所 | AreaData branch `codex/asia-domestic-20260926`にコード・台帳・公開可能な公式source所在を保存。原本とsiteは別のignored国別ディレクトリ。 | 独立`ACCEPT`、国別Hosting/Public先、現地担当者と更新頻度。DDPT公開先は転用しない。 |
| 仕様 | 共通実装0.4候補、dataset schema 0.2。地域診断・テーマ診断・DB・計画資料と既存出力を維持。 | UX v1.0最終採用、現地語と運用者による受入。 |
| 国内統計 | NSB PHCB 2017全国＋20 Dzongkhag報告のA2.1を選定。国・20県・64町/Thromde行・205農村Gewog部分行、４指標・871直接観測。詳細分析人口727,145人、ホテル滞在者を含む全国の全発見人口735,553人は別指標。WDI推計も別系列。 | 他641番号表の数値列/意味、全国付表と新しい地方統計、利用条件。 |
| 地理・コード | 元表の親子・男女の全行照合。2020年版BSSGC原本を取得したが、2017年コードとして採用しない。provider図形を除外。 | 2017対応の公式コード・境界、町とGewog法定範囲、Thromde/Councilとの照合。 |
| 計画主体・資料 | 2012年Local Government Rules本文を取得。Dzongkhag TshogduとGewog Tshogdeに関する当時の条文を所在確認。 | 現行効力、適用様式、13th FYP PDFの真正な再取得、対象自治体の採択計画・予算・支出・評価。統計行を計画主体へ同一化しない。 |
| 国際共通source | WDI全国系列は初期生成で取得。 | 他国際sourceの国・テーマ・年・粒度別availabilityと国内地理対応は未確認。所在・取得・照合・採用を別管理。 |
| 利用条件と公開 | NSB/DLGDMの公式PDF23原本をURL・bytes・hashで固定。候補は未公開。 | 原本再配布条件、全42シナリオ、独立監査、Hosting/Public先。 |

代表確認は全国、Haa、Bji農村行、Thimphu、Thimphu Thromde。実画面でHaa→Bji→同じHaaの再選択と、計画資料の未収集表示を確認。六つの実出力例を照合した。Word/PDF描画、狭画面、全地域型、現地利用は未実施。
