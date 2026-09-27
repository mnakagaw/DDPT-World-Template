# Timor-Leste INETL 2022・計画資料 原本／採否監査

2026-09-27 JST。対象は独立・ignored候補 `generated/timor-leste-areadata-20260927`、未公開。公式PDF8件のbyte長とSHA-256は [manifest](../../config/timor-leste-phc2022-source-manifest.json) に固定し、全33番号表の処置と選定表のセル監査を候補 `evidence/TLS_PHC2022_AUDIT.json` に保存した。取得・所在・地理照合・指標採用は別の状態である。

## 原本・制度の所在と処置

| 原本 | 版・地理・採否 |
|---|---|
| [INETL Population and Housing Census 2022 Main Report](https://inetl-ip.gov.tl/wp-content/uploads/2023/05/Final-Main-Report_TLPHC-Census_18052023-1.pdf) | 204 PDF頁を取得。2022-09-05/06時点の通常居住者。全国＋第一階層14地域についてTable 4.3の総人口・面積・公表人口密度、4.11の5歳以上の私的世帯居住者、4.12の3～29歳の私的世帯居住者を部分採用。 |
| [Law 19/2023, territorial administration](https://www.mj.gov.tl/jornal/public/docs/2023/serie_1/SERIE_I_NO_45_D.pdf) | 第一階層のAtaúro、12 Municípios、Oe-Cusse Ambeno特別行政区を確認。2022統計の名称とは照合したが、2022年当時の型・現行の公式コード・図形を同一化しない。 |
| [Ministerial Diploma 19/2023, suco recognition](https://www.mj.gov.tl/jornal/public/docs/2023/serie_1/SERIE_I_NO_16_A.pdf) | 2023年版は461 sucoを認定。国勢調査本文の2022年452 sucoとは異なる。全104頁の個別名称・変更を照合しておらず、2022下位統計へ自動結合しない。 |
| [Municipal planning procedure 72/2024](https://www.mj.gov.tl/jornal/public/docs/2024/serie_1/SERIE_I_NO_49.pdf) | 市町村のdevelopment-plan手続があり、承認にはCouncil of Ministersのresolutionを要する。掲載後の改正・地域ごとの適用結果は未確認。 |
| [Ataúro procedure 33/2025](https://www.mj.gov.tl/jornal/public/docs/2025/serie_1/SERIE_I_NO_38.pdf) | Ataúroに別の計画手続があり、閣議決議による承認を要する。市町村手続をAtaúroに機械的に適用しない。 |
| [Díli PEDM 2026–2030](https://dili.gov.tl/wp-content/uploads/2026/02/Planu-Estratejiku-dezenvolvimentu-Munisipal-PEDM-DILI-2026-2030.pdf) | 自治体サイトの347頁本文を取得。要約はapprovedと述べるが、閣議承認決議を独立確認できず `official_status=unverified`。全章・目標・財源の意味監査は未完了。 |
| [Díli 2026 Annual Action Plan](https://dili.gov.tl/wp-content/uploads/2026/02/PAA-2026-AM-Dili.pdf) | 8頁目の `Total Orsamentu` は **US$19,502,642**。これは2026年**予算見込・計画値**であり、実支出・進捗・評価ではない。Díliにのみ接続。 |
| [Ataúro development plan 2026–2030 draft](https://atauro.gov.tl/wp-content/uploads/2026/02/Ezbosu_Planu-Dezenvolvimentu-Atauro-2026-2030_Final-Version-21-JANEIRU-26.pdf) | 自治体サイトの172頁本文を取得。ファイル名は`Ezbosu`（草案）。閣議承認決議未確認につき採択済みと書かず、Ataúroだけに表示。 |

## 国勢調査の全番号表台帳と採用列

目次の番号表は**Table 3.1～3.9の9件と4.1～4.24の24件、計33件**。候補監査JSONに全ID・採否を列挙した。採用3表以外の30表は `priority_unassessed`、`numeric_columns=null`。`null`は数値列が存在しない意味ではなく、列数・意味を未確認という意味。4.1/4.2の行政post/suco表は画像としてPDFに埋め込まれ、文字抽出でセルを読めない。一つのPDFのこの制限を国勢調査全体の不存在としない。

| 表 | 確認した数値列／行 | 採否・注意 |
|---|---|---|
| 4.3 | 全国＋14地域15行 ×6数値列=90セル。総人口、男子、女子、性比、面積、密度。 | 総人口・面積・密度の3列だけ直接採用。全国人口1,341,737、Díli324,738。性比の全国セルは`1,446`と印刷され異常。男女は画像Table 4.1の全国とBaucauで25人ずつ逆方向に競合するため不採用。 |
| 4.11 | 全国＋14地域の集計行15×9=135数値セル。年齢別255行×9=2,295欄中2,286数値・9秘匿。 | 私的世帯の5歳以上の総数・識字・非識字の3列を直接採用。識字割合は同一行の識字÷総数で算出。INETL本文p.21の4件未満秘匿を守り、差から9秘匿値を復元しない。残る男女・年齢細分は監査済み算術以外、意味採用待ち。 |
| 4.12 | 全国＋14地域の集計行15×9=135数値セル。年齢別255行×9=2,295数値欄。 | 私的世帯の3～29歳の総数・就学中・非就学の3列を直接採用。同じ行から就学中割合を算出。学校入学率や全人口割合ではない。残る男女・年齢細分は意味採用待ち。 |

採用3表の全集計行で足し算、全国と14地域の公表合計、秘匿のない年齢列で年齢計を検査し、選定列の監査 `issues=[]`。**11指標、15地域、165観測＝135直接＋30算出**。人口、私的世帯5歳以上、私的世帯3～29歳は互いに異なる母集団。初期WDI全国年央推計は別系列として保持し、地方値へ写さない。Table 4.3の総人口は2026年人口ではない。

## 地理・画面・未完了

2022報告は第一階層14行。初期取得の2017 geoBoundaries図形は13件で、Ataúroを独立地域とする報告行に対応しないため候補から除いた。公式ID・2022年対応図形・現行版・下位post/sucoコードは未取得。法定の計画主体と内部診断に必要な下位統計を分け、post/sucoの画像表は採否を保留する。Díliの計画本文やAtaúro草案を他12地域に複製しない。実支出、実施進捗、公式評価は未確認。

Dataset SHA-256 `9b5a0fb1f401e9cbfd53f77d0ff2e29efef170cf87efe6f75f7dc151714a36f9`。`validate-country`は0 errors/warnings、build成功。独立したsource/output照合コードで全国とDíli・Ataúro・Baucau・Oecusseの5地域×11指標、診断CSV/HTML/Markdown・計画HTML・根拠CSV、全国14地域×11指標の154比較行、DíliのPDF予算欄と地域別資料を確認。ローカルブラウザでは全国→Díli→Ataúro→全国の主値・URL・資料切替と境界未確認表示を確認した。これは制作者確認であり、**42シナリオ全件・独立 `ACCEPT`・Hosting/Public検証ではない**。

残件は、(1)未採用30表の全数値列と定義、画像のpost/suco表、性別競合の独立解決、(2)2022→現行の行政コード・図形・下位階層対照、(3)全計画主体の計画・予算・支出・実施・評価、閣議決議、(4)各PDFの利用条件と現地利用者、(5)42シナリオと独立`ACCEPT`。共通sourceのTLS×年×テーマ×粒度のavailabilityも未確認で、今回の接続数に含めない。
