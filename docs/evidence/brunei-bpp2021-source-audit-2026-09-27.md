# Brunei DEPS BPP 2021・計画資料 原本／採否監査

2026-09-27 JST。対象は独立・ignored候補 `generated/brunei-areadata-20260927`、未公開。公式PDF6件のbyte長とSHA-256は[manifest](../../config/brunei-bpp2021-source-manifest.json)に固定した。[28付表台帳](brunei-bpp2021-table-audit-2026-09-27.json)は表の見出し、選定列の確認範囲、未審査を区別する。Main Reportの全表・数値列は未審査であり、全国勢調査項目を審査済みとはしない。初期preflight `generated/brunei-areadata-20260927/evidence/SOURCE_PREFLIGHT.md`は`source_locations_not_pre_researched`だったため国内公式sourceから所在調査を開始した。

## 原本と制度

| source | 取得・処置 |
|---|---|
| [DEPS BPP 2021 final report](https://www.deps.gov.bn/wp-content/uploads/2025/10/RPT-1.pdf) | 公式[刊行目録](https://www.deps.gov.bn/statistical-publications/)から本文40,014,514 bytesを取得。Main Reportの全表・数値列は`priority_unassessed`。Preliminaryではなくfinal版を参照。 |
| [Annex A](https://www.deps.gov.bn/wp-content/uploads/2025/10/ANNEX-A.pdf) | 1,329,106 bytes。A1の居住資格×District×男女とA2の18年齢帯×District×男女を数値列ごと監査。A3–A12は見出し所在のみ。 |
| [Annex B](https://www.deps.gov.bn/wp-content/uploads/2025/10/ANNEX-B.pdf) | 1,337,185 bytes。B1の全国・4 District、B2の39 Mukim。2011/2021各5列、計10数値列を確認。2021の総人口・男女・世帯・居住住宅を採用。2011欄は境界版不一致の恐れがあり時系列にしない。B3–B6は未審査。 |
| [Annex C](https://www.deps.gov.bn/wp-content/uploads/2025/10/ANNEX-C.pdf) | 2,284,478 bytes。C1の4 District+39 Mukim、総計・資格別×男女12列を監査。資格別Persons3列のみ採用。C2–C10のKampung・年齢等は未審査。 |
| [AGC Town and Country Planning Act, Cap.248, revised 2022](https://www.agc.gov.bn/wp-content/uploads/2026/07/CAP-248-TOWN-AND-COUNTRY-PLANNING-ACT.pdf) | 254,472 bytes。§8は計画区域指定、§13–15はPlanning Authorityによるdraft District PlanとMinisterの書面承認／拒否、§17–19はLocal Plan。旧Cap.143を現行法として使わない。本文版の後続改正と個別計画への適用は引き続き確認。 |
| [MOF RKN12 English 2024–2029](https://www.mof.gov.bn/wp-content/uploads/2025/10/RKN12-English.pdf) | 13,558,978 bytes。PDF p.114にNational Land Use Masterplanと4つのDistrict Plan 2026–2045が**事業予定**として記載。地域別の計画完成、承認、配分、実支出の証拠ではない。全国投資計画の金額をDistrictへ転記しない。 |
| [JPBD plan catalogue](https://www.jpbd.gov.bn/buku-garispanduan-dan-master-plan/) | 全国master planとBrunei Muara、Belait、Tutong、Temburong District Planの所在を確認。目録の表紙画像のみで、4計画の本文、図面、版、対象期間、承認告示、取得・利用条件は未確認。`link_verified`とし、本文取得とは区別。 |
| [Survey Department Geoportal](https://geoportal.survey.gov.bn/start) | 公式地理sourceの所在を確認。2021国勢調査に対応したDistrict/Mukim公式コード・図形は取得・照合できていない。 |

`www.deps.gov.bn`上の公式PDF直リンクを取得した。目録が参照するCDN経路は403だったため、同名資料を取得済みとする根拠に使っていない。取得条件、hash、URLはmanifestに保存。原本は候補`raw/`に置きGitには含めない。再配布権は未確認。

## 28付表の全IDと選定数値列

付表A1–A12、B1–B6、C1–C10の**28件**を台帳化。次の5表の選定範囲だけ意味・数値を確認し、残る23表の各数値列と分母は`priority_unassessed`。A3–A12（10件）、B3–B6（4件）、C2–C10（9件）。未審査は値が存在しないことを意味しない。

| 表・印刷頁 | 確認した全数値欄／採用列 | 地域・注意 |
|---|---|---|
| A1 p.80 | 3居住資格行×15地域/男女欄＝45セル。Persons5地域×3資格を採用、男女は検算。 | 全国＋4 District。C1の資格別集計と一致。 |
| A2 p.81 | 18年齢帯×15地域/男女欄＝270セル。5歳帯Personsを0–14、15–64、65+へ加算した15値のみ採用。 | 全国＋4 District。独立公表セルではないため`calculated`、帯と計算をlocator/footnoteに保存。 |
| B1 p.109 | 5行×10列＝50セル。2021年5列だけを採用。 | 全国＋4 District。4 Districtの各列和は全国と一致。2011年5列は保留。 |
| B2 pp.110–113 | 4親+39 Mukimの43行×10列＝430セル。2021 Mukim5列を採用。 | 親Districtの10列と全Mukimの和を検算。2011年5列は保留。 |
| C1 pp.153–156 | 43行×12列＝516セル。District+Mukimの資格別Persons3列を採用、残る男女・合計9列を検算。 | B2総人口と各資格の和が一致。MelilasのTemporary Residents 0は公表されたゼロ。 |

選定表の**1,311数値セル**を機械的に読取り、全国/親子合計、男女合計、資格計、年齢帯合計とB1/B2/A1/C1の重複を確認した。A2は全国と4 Districtの5歳帯から15件を算出。2021国勢調査の**全国＋4 District＋39 Mukim＝44地域、11指標、367観測（352出典公表セル＋15算出）**。全国B1人口440,715、Brunei Muara318,530、Belait65,531、Tutong47,210、Temburong9,444。WDIの2021全国推計451,721や2025推計466,330は別系列。全国WDI値を地方へ配分せず、観測年の違う値を比較地図へ混ぜない。

## 地理、計画、画面・残件

DEPSの行名は公式行政コードではない。初期取得の2011年geoBoundaries District図形4件を2021統計へ結合せず除外。対応図形0件の代替として、上部の階層selectorと下部の全構成表を使う。全国→4 District、各District→39 Mukimの区分を原表で確認した。District計画のための内部診断にMukimを使うが、Mukimに独立した法定District Planを付与しない。JPBD目録は各DistrictとそのMukimには「親の計画所在」としてのみ表示し、承認状態は`unverified`。計画本文・地域別予算/支出/評価は欠測。

Dataset SHA-256 `868a15b5a57e7ca9248c76f6d618a6caace21167b1567a6b4cc11018b0ac5cfc`。`validate-country` 0 errors/warnings、build成功、6代表地域の診断/計画/根拠出力132セルとPDF6 hashを検証。実ブラウザーでBrunei Muara→Kianggeh→同District、Belait→Melilas→同Districtの再選択、年齢算出ラベル、Melilasの0、計画目録の地域限定を確認。これは制作者確認で、42シナリオ全件、独立`ACCEPT`、Hosting/Publicではない。

残件は(1)23付表とMain Report全表の数値列・定義/母集団/詳細地理、(2)2021→現行District/Mukim/Kampungの公式コード・同版図形、(3)4計画の本文・版・告示・承認・予算見込・実支出・実施・公式評価、(4)利用条件・現地実務、(5)42シナリオと独立監査。初期preflightの国際共通候補はBRN×年×テーマ×粒度のavailability未確認で、地方指標数に含めない。
