# Malaysia country lesson audit — producer-side partial check

2026-09-27 JST、branch `codex/asia-domestic-20260926`、ignored候補 `generated/malaysia-areadata-20260927`、dataset SHA-256 `fabb14d24a4cbdd8265005c166bf2b78f2d3b4e153ba8e4390e0c6e18a8039d0`。Windows/PowerShell、Node v24、Python 3（openpyxl/pypdf）、ローカルpreview `127.0.0.1:4274` と Codex in-app browser。`templates/COUNTRY_LESSON_AUDIT.md`の12観点に照らす**制作者側の部分確認**であり、42シナリオ全件や独立監査ではない。対象commitは本記録を保存するAreaData commitとし、後続handoffにSHAを記す。

| ID | 判定 | 根拠と残件 |
|---|---|---|
| UA01 | 制約付き | 13原本をhash固定。DOSM CSV6本の全列・674,676数値セル/空欄を機械的棚卸し。人口選定sex/year、州HIES/amenitiesだけ14指標に採用。MyCensus PDFの19表、その他年齢/民族/過去年、DBKL計画576頁/年報467頁は `priority_unassessed`。 |
| UA02 | 制約付き | 2020/24全国・州・地区の原表unitと独立丸め差を確認。2020は国勢調査調整、2024は中間推計。地区PDFを取得したが全表の意味監査は未了。 |
| UA03 | 制約付き | 全国+16州/FT+156地区、単一州/FT地区重複4行を除外。2020改名4行、HIES 2024地区162行中の149 exact matchを保留。UPI土地コードとDOSM境界/2017図形の時点付き照合なし。 |
| UA04 | 制約付き | 1,282採用slots=1,258観測+24欠測。人口の千人→人は算出来歴。親は直接DOSM観測、率は単純平均しない。HIES世帯調査とWDI全国値を別意味。原CSV全数値の採否を各field/条件で記録したがPDFの全数値は未処置。 |
| UA05 | 制約付き | 5例の実CSV/HTML/Markdown・計画HTML・根拠CSVを原本locator照合。ブラウザーで全国、Selangor/Petaling、KLと資料、16州テーマ比較を確認。狭幅、低帯域、現地語/利用者、全指標の実操作は未実施。 |
| UA06 | 制約付き | Selangor→Petaling→同じSelangor全体をドロップダウンで再選択し、見出し・URL・上位選択/下位解除を確認。親の直接値に戻る。地域別メモ保持などは未検証。 |
| UA07 | 制約付き | 16/16州の2024人口比較全行、Selangor分析中にJohor行を注目しても対象/URLはSelangorのまま。Cameron Highlandの2020改名行は欠測。その他欠測指標と検索/印刷の全件は未検証。 |
| UA08 | 制約付き | 2020調整人口/2024推計/WDI2025を別表示し、図形未照合の検索/表代替を確認。未観測の親を子の一部で埋めない。歴史系列全件やCSV以外の印刷は未検証。 |
| UA09 | 制約付き | KL官報の採用・効力、DBKL予算**見込額**、年報本文取得だけを分離。KL→Selangor変更でKL資料が0件になり残留なし。Act172適用外の地域、実支出/評価、他PBT計画は未調査。 |
| UA10 | 未実施 | KL Volume 2の正式章/全数値、他地域の現行法令・手引き・策定主体・様式、参加/承認、正式なWord/PDF出力適合を照合していない。 |
| UA11 | 制約付き | 5例の診断CSV/HTML/Markdown、計画HTML、根拠CSVの地域/年/値/原本locatorを検査。Word/PDF、実印刷の全ページ、狭幅、長い全地区表の視覚検証は未実施。 |
| UA12 | 制約付き | hash固定→audit/import→validator/build→実出力verifierで再現。Validator 0 error/warning、`npm run check` 162 modules/templates、`npm test` 219/219。Kit独立取込、42件全件、Hosting/Publicは別記録。 |

公式原本の取得と監査は[原本監査](malaysia-dosm-source-audit-2026-09-27.md)で追跡する。**42件合格とは報告しない。** `ACCEPT`まで国別版完成・公開と数えない。
