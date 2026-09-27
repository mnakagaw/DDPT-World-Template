# Brunei country lesson audit — 制作者側の部分確認

2026-09-27 JST、branch `codex/asia-domestic-20260926`、ignored候補 `generated/brunei-areadata-20260927`、dataset SHA-256 `868a15b5a57e7ca9248c76f6d618a6caace21167b1567a6b4cc11018b0ac5cfc`。Windows/PowerShell、Node、Python、Poppler `pdftotext`、ローカルpreview `127.0.0.1:8765`とCodex in-app browser。`templates/COUNTRY_LESSON_AUDIT.md`の12観点に対する**制作者側の部分確認**。対象コードcommitは後続BRN handoffに記録する。現地担当者による試験はない。

| ID | 判定 | 根拠・不足 |
|---|---|---|
| UA01 | 制約付き | 公式PDF6件hash固定。28付表を見出し台帳化、A1/A2/B1/B2/C1の選定範囲1,311数値セルを監査。残り23付表とMain Report全表の数値列・定義は`priority_unassessed`。国別preflightは未調査から開始。国際共通sourceの国別availabilityは未確認。 |
| UA02 | 制約付き | 一括B1/B2だけで完結させずA1/A2/C1原本を照合。全国人口440,715、4 District和、39 Mukimの親子和、資格/男女/年齢和を確認。Kampung詳細のB3–B6/C2–C10は未審査で不存在としない。 |
| UA03 | 制約付き | 全国・4 District・39 Mukimの報告名と親子関係を原表から登録。公式コードと2021対応図形は0件。2011参照図形を除外し、暫定IDのコード欄はnull。Mukimを独立した計画主体としない。 |
| UA04 | 制約付き | 11指標・367地方観測のうち352直接、15年齢帯加算。メソッドと`calculated`ラベルを画面/CSVへ反映。4 District値は直接観測。Melilasの資格0は欠測ではない。WDI全国年央推計を2021地方国勢調査と混ぜない。 |
| UA05 | 制約付き | 全国、Brunei Muara、Belait、Temburong、Kianggeh、Melilasの出力を検査。画面では全国→Brunei Muara→Kianggeh→親、およびBelait→Melilas→親を操作。見出し、主値、URL、計画目録を確認。狭幅・低帯域・現地利用者、全主要操作のDDPT対照は未実施。 |
| UA06 | 制約付き | Kianggehから同じBrunei Muara全体、Melilasから同じBelait全体を上位selectorで選び直し、見出しと人口8,102→318,530、29→65,531を確認。すべての指標・メモ・保存経路を通した確認は未実施。 |
| UA07 | 制約付き | 全国のDistrict比較4/4、Brunei MuaraのMukim比較18/18を確認。形状0件でも全構成表を表示。Kianggehの年齢群は欠測。比較行への注目、検索/スクロールで隠れた全行印刷は未実施。 |
| UA08 | 制約付き | B1/B2の2011欄を2021境界と時系列化せず、2011図形を外した。2021国勢調査と2000–2025年WDI全国系列は別指標。年齢群15件は原表の5歳帯和であり公表セルではない。 |
| UA09 | 制約付き | Cap.248本文、RKN12本文、JPBD目録を制度/事業予定/資料所在として区別。District/Mukimの計画カードは該当親Districtのみ。JPBDは`link_verified`、公式承認`unverified`、予算/実施/評価なし。4計画本文は未取得。 |
| UA10 | 未実施 | Planning AuthorityとMinisterの制度条項は確認したが、現行の各District計画の本文/様式/告示/承認、適用図面、必要な法定出力欄は未監査。汎用計画出力を法定提出物とは扱わない。 |
| UA11 | 制約付き | 6地域の診断CSV/HTML/Markdown、計画HTML、根拠CSVから直接値・算出値・欠測を計132セル照合。計画資料の他Districtへの漏れなし。Word/PDFは未採用。全頁印刷、狭幅・長ラベル表示、全42シナリオは未実施。 |
| UA12 | 制約付き | 原本6 hash→import→validator 0 errors/warnings→build→原PDF転記値対出力verifierを再現。`npm run check`/`npm test`はhandoffの対象commitで記録。Kit独立取込、Hosting/Publicと独立`ACCEPT`は別。 |

全付表台帳は[tracked JSON](brunei-bpp2021-table-audit-2026-09-27.json)、原本・採否の説明は[監査書](brunei-bpp2021-source-audit-2026-09-27.md)、PDF hashは[manifest](../../config/brunei-bpp2021-source-manifest.json)。**42件合格とは報告しない。独立完成監査`ACCEPT`前に公開しない。**
