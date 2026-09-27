# Uzbekistan country lesson audit — 制作者側の部分確認

2026-09-27 JST、branch`codex/asia-domestic-20260926`、ignored候補`generated/uzbekistan-areadata-20260927`、dataset SHA-256 `f2a65f3fc267661a8634ca5079a5e70eb8c2220875e2116fe4cd2442b28eff2f`。Windows/PowerShell、Node、Python/openpyxl、Poppler、`127.0.0.1:8766`のローカルpreviewとCodex in-app browserで確認。`templates/COUNTRY_LESSON_AUDIT.md`の12観点に対する制作者側の部分確認。対象コードcommitはhandoffに記録。現地担当者による試験はない。

| ID | 判定 | 根拠・不足 |
|---|---|---|
| UA01 | 制約付き | 初期preflightは国内所在未調査。国内公式9原本をhash固定。SIAT5 CSVの17,901数値セルを機械棚卸し、2026年1,105セルのみ採用。国勢調査報告27表のうちp.4–5選定列だけ、Excel11農業表は未採用。国際共通sourceの国別availabilityは未確認。 |
| UA02 | 制約付き | SIATだけで国勢調査を不存在とせず、速報報告PDFと別Excelを取得。全国＋14州級の速報150欄を検査。PDF p.4–5はレンダリングして行名・数値を照合。他25表と農業列の意味は未監査。 |
| UA03 | 制約付き | SIAT COATO 1+14+206コードと親子を保持。Tashkent州`1727`と市`1726`を分離。速報PDFにはコードがなく14州級を名称/型で暫定照合。同版公式図形は0、2017年初期図形を外す。 |
| UA04 | 制約付き | 国内10指標・1,180直接観測。男女、都市農村、親子、全国の合計を全2026行で検算。1月1日推計／1月15日速報／WDI年央推計の意味を分離。MOF90セルは期間不明で不採用。 |
| UA05 | 制約付き | 9代表地域の診断CSV/HTML/Markdown、計画HTML、根拠CSVを検証。実ブラウザーで全国、Karakalpakstan、Nukus、Tashkent州/市、Yangikhayotの見出し・値・URL・計画資料を確認。狭幅・現地利用者、全主要操作のDDPT対照は未実施。 |
| UA06 | 制約付き | Nukus市349.4千人→同じ親Karakalpakstan全体2,053.2千人、Yangikhayot地区→Tashkent市全体を上位ドロップダウンで再選択し、見出し・URL・資料を確認。メモ・保存・全指標同時の回帰は未実施。 |
| UA07 | 制約付き | 全国14/14、Karakalpakstan17/17、Tashkent市12/12のSIAT比較を確認。図形0でも表全件と出典が見える。地区級速報はCSVで`not_collected`、0へ代入しない。比較行注目、検索隠れ行を含む全頁印刷は未実施。 |
| UA08 | 制約付き | SIAT過去年を2026年COATOへ無条件に時系列化しない。速報・SIAT・WDIの時点と単位を分離。全国上部カードは2026年SIAT/速報を別表示。共通年のテーマ比較全操作は未実施。 |
| UA09 | 制約付き | PF-21全国法令所在、ASDR14地域の策定課題、MOF予算表所在を分離。予算表の期間/実績は不明なのでbudget分類のみ。Tashkent州と市の資料は別、Yangikhayotに親の地域資料は残らない。計画本文/承認/実績/評価は未確認。 |
| UA10 | 未実施 | 個別14地域の計画本文、法定権限、適用manual/form、正式承認を取得していない。汎用Markdown/HTML出力を法定提出物としない。 |
| UA11 | 制約付き | 9地域の診断と根拠CSVの180値/欠測セルを独立転記値と照合。Tashkent州/市のID、地区速報欠測、WDI地方漏れ、計画資料の地域限定を確認。Word/PDFは未採用。全頁印刷、狭幅、言語/文字切れは未実施。 |
| UA12 | 制約付き | 9 hash→import→validator 0 errors/warnings→build→実出力照合を実施。`npm run check` 166件、`npm test` 219/219。Kit独立取込、Hosting/Public、独立`ACCEPT`は別。 |

[全表・sheet台帳](uzbekistan-siat-census2026-table-audit-2026-09-27.json)、[原本と採否](uzbekistan-siat-census2026-source-audit-2026-09-27.md)、[manifest](../../config/uzbekistan-2026-source-manifest.json)を参照。**42件合格とは報告しない。独立`ACCEPT`前に公開しない。**
