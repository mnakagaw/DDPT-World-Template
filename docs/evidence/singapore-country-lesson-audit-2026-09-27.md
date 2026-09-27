# Singapore country lesson audit — 制作者側の部分確認

2026-09-27 JST、branch `codex/asia-domestic-20260926`、ignored候補 `generated/singapore-areadata-20260927`、dataset SHA-256 `286785d5f0b0368093beefebbdb35f4e148fbd3df1c7ed29efb1587e403aee26`。Windows/PowerShell、Node v24、Python 3（openpyxl/pypdf）、ローカルpreview `127.0.0.1:4275` とCodex in-app browser。`templates/COUNTRY_LESSON_AUDIT.md`の12観点に照らす**制作者側の部分確認**。対象コードcommitは後続SGP handoffに記録し、42シナリオや独立`ACCEPT`と区別する。

| ID | 判定 | 根拠・不足 |
|---|---|---|
| UA01 | 制約付き | 公式原本7件をhash固定。2026 ZIP3冊7sheet・456,288値欄、2020 CSV60値列、末尾注記を棚卸し。選定6指標だけ採用。その他は`priority_unassessed`、2020詳細報告2冊の旧PDF URLは404。 |
| UA02 | 制約付き | 2026 PDF printed p.15の55区域・MP2025注記、全国4,231,520・Tampines296,060、ZIPの388地理キーと2表の総数一致を照合。2020国勢調査はMP2019・4,044,210、別版。 |
| UA03 | 制約付き | URA MP2025の55区域名・`PLN_AREA_C`・図形を結合。332 Subzoneは親名付き原表キー、公式コード/2025図形なし。2019図形332は2026に流用しない。5 Regionは非分析対象。 |
| UA04 | 制約付き | 2,328 slots=1,489観測＋839`-`欠測。48/55区域・281/332 Subzoneに人口観測。親は直接値。区域数値和は全国より30人多く、男女和も10人多いので再集計しない。WDI全人口は別母集団。 |
| UA05 | 制約付き | 全国、Tampines/Tampines East、Ang Mo Kio、Changi Bayの5地域、各6セル、診断CSV/HTML/Markdown・計画HTML・根拠CSVを原本照合。ブラウザーで地図/階層/資料を確認。狭幅、低帯域、現地語担当者確認は未実施。 |
| UA06 | 制約付き | ブラウザーでTampines→Tampines East→同じTampines全体を選び、見出し/URL/上部人口296,060へ復帰。子124,770が親主値に残らない。メモ/保存全経路は未確認。 |
| UA07 | 制約付き | Changi Bayの直接`-`は「データなし」のまま。全国テーマ診断は48/55観測・7欠測。Tampines行への注目で全国の分析対象とURLは変わらない。全指標の検索/印刷は未確認。 |
| UA08 | 制約付き | MP2019の2020国勢調査は歴史原本で留保、MP2025の2026值へ自動移管しない。区域表示図形は参考、Subzoneの図形なし。2020–2026変化は計算しない。 |
| UA09 | 制約付き | 全国MP2025 Written Statementを国の計画として表示。区域ページで「資料未取得」を表示し、全国文書を区域固有文書にしない。予算/実支出/評価は別の未取得状態。 |
| UA10 | 未実施 | Planning Actの全適用条文、URA計画様式・区域別詳細計画、実施/財政/評価、現地の制度利用者確認を終えていない。正式な区域別計画出力は採用しない。 |
| UA11 | 制約付き | 5地域の実CSV/HTML/Markdownと計画・根拠出力を原表locatorに照合、全国比較55行を確認。Word/PDF・全行印刷・スマートフォン視覚確認は未実施。 |
| UA12 | 制約付き | 原本hash→再生成→validator 0 error/warning→build→実出力verifierを再現。`npm run check` 163 modules/templates、`npm test` 219/219。Kit独立取込、42件全件、Hosting/Publicは別記録。 |

全sheet台帳は候補 `evidence/SGP_POPULATION2026_AUDIT.json`、出力照合は `evidence/SGP_OUTPUT_VERIFICATION.json`。[原本監査](singapore-population2026-source-audit-2026-09-27.md)が採否と未取得を説明する。Word/PDFは採用しておらず、隔離renderer試験は対象外。**42件合格とは報告しない。独立完成監査 `ACCEPT` 前に公開しない。**
