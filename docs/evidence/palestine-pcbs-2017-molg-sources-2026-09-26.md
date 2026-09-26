# パレスチナ：PCBS 2017国勢調査とMoLG計画資料の部分採用

確認日 2026-09-26。対象は `generated/palestine-areadata-20260926-v2` のローカル候補。**部分成果・未公開・独立監査未合格**。`PSE` は世界銀行の国別APIで *West Bank and Gaza* と表示される経済コードであり、PCBS原表の *Palestine* の地理・人口定義との完全一致を認証したものではない。UN M49の地域所属や国・地域の政治的地位をこのアダプターから推論しない。

## 取得原本と採用範囲

| 原本 | 取得・確認 | 採否 |
|---|---|---|
| [PCBS PHC 2017 Final Results Summary](https://www.pcbs.gov.ps/Downloads/book2383.pdf) | 186頁、SHA-256 `25b8c899e4d9be4e480236f08b764fd957949608767c7adb7f0a302a90cb4f5f`。PDF/印刷71頁のTable 2をテキストと画像で照合。 | Table 2の19報告行と4件数列（総人口・女性・男性・世帯）だけ採用。10数値列の残り6列（率、平均世帯人員、構成比）は未採用。その他の表・頁は未棚卸し。 |
| [PCBS PHC 2017 detailed population volume](https://www.pcbs.gov.ps/Downloads/book2425.pdf) | 270頁、SHA-256 `0ab9b57187f3924a128069a685a83295a23d80ab7d706dc8e690b8df2e9d0520`。 | 取得のみ。全物理表、数値列、定義と行政・集落コードは未棚卸し。 |
| [PCBS governorate area table](https://www.pcbs.gov.ps/Portals/_Rainbow/Documents/Land-use-table%201E-2019.html) | SHA-256 `33eebd91cecdeffecc42076406e22fe5b232f852037ce1ff5f8ab0a04c2fc233`。2019年公開群に置かれた2017年面積表。 | 面積値・境界図形・公式コードを未採用。頁注記は2017年の行政区域調整と国勢調査集落を結び付けるため、名称だけで後年図形を結ばない。 |
| [MoLG local development planning guide](https://molg.pna.ps/uploads/files/SDIP_d2ff2339671b4f1fbbd1c083e0ccd038.pdf) | 149頁、SHA-256 `27fbc38788da1bd1d0554fffbdf68ee831cbf415c1a407d5112d9e7f360bb210`。PDF1–2頁の表紙・第3版2018年の説明を画像とテキストで確認。 | 全国の**市・町向け策定手引き**として資料1件。県別・市別の策定済み計画、法的義務、現在の承認状態とはしない。 |
| [MoLG local government sector strategy 2025–2027](https://www.molg.pna.ps/ar/categories/13/%D8%B3%D9%8A%D8%A7%D8%B3%D8%A7%D8%AA-%D9%88%D8%A7%D8%B3%D8%AA%D8%B1%D8%A7%D8%AA%D9%8A%D8%AC%D9%8A%D8%A7%D8%AA/1) | 公式掲載先から4,039,370バイトのPDFを取得。SHA-256 `ec7d2dbf55526fc5d523b62e804e28570c1aed88240f308a796fa60956b7be54`、171頁。PDF1、2、5、51、55頁を画像で確認。 | 全国の**地方自治省セクター戦略**として資料1件。目次の予算・モニタリング項目を、各県の予算執行・計画達成・公式評価へ転記しない。個別の承認状態は `unknown`。 |

元資料はそれぞれ候補の `raw/` 以下に取得receiptとSHA-256で保持し、PDF・詳細HTMLのGit再配布は行わない。PCBSのPython標準CA束では証明書連鎖を検証できなかったため、Windowsの証明書ストアで検証する `curl.exe` を使用した。`--insecure` / `-k` は使用していない。

## Table 2 の数値・意味の照合

PDF71頁の見出しは *Population in Palestine by Governorate and Sex, 2017*。全国行は総人口 **4,781,248**、女性 **2,348,052**、男性 **2,433,196**、世帯 **929,221**。West Bank **2,881,957** と Gaza Strip **1,899,291** の人口は全国値に一致する。西岸11県、ガザ5県の各4件数列は各地域の印刷親値と一致し、男女の和もすべての行で総人口に一致する。したがって全国1＋広域2＋県16の19行 ×4列＝**76件の直接出典値**を採用した。地理合算で欠けた親値を補ったのではない。

同頁脚注は人口に実際の計上分と事後調査による未計上人口推計を含むと記す。したがって「2017年最終国勢調査の人口」と明示し、2026年人口、単純な実査人数、世界銀行の年央推計へ読み替えない。Gaza Strip と同名の Gaza Governorate は異なるIDで保持した。JerusalemのJ1/J2、集落、法定区域の対応は未検証。

Summary Table 29（PDF116頁から）の**585個の集落コード**を所在台帳として数えたが、そのうち56行は名前・数値が物理行に分割される。単一行で取れた529行だけの単純合計は全国値より大きく欠けるため、集落数値は**0件採用**とした。詳細270頁を含め、国勢調査全体に地方値がないとは言わない。[PCBS報告書台帳](https://www.pcbs.gov.ps/en/reference/report-history/)と[MoLG県別計画手引き](https://www.molg.pna.ps/uploads/userfiles/file/pdfs/DSDPmanualArabic.pdf)は確認した所在候補だが、全本文や現在の適用関係は未監査。

## 地理・計画・画面上の制約

- PCBS 2017原表の階層名のみを用いる。Table 2に県公式コードや2017年法定図形はない。初期生成で入った2021年のWest Bank/Gaza参照図形2件は数値地図から外した。位置・内部比較の全件表、検索、地域選択、CSV/HTMLは図形がなくても動作する。
- 国全体には世界銀行WDI全国系列を別系列で残した。地方値への転記、PCBS 2017との同義化、率の平均、欠けた親値の合算は行わない。
- MoLGの2018年ガイドは市・町のSDIP方法、2025～2027年戦略は省全体の文書であり、**全国参考資料2件**としてのみ表示する。選択したGaza県の計画画面は「その地域の資料0件」と表示し、全国参考を別枠に置く。県・自治体の計画本体、承認、実予算、支出、評価、現在の法定計画主体は未確認。
- 公式国勢調査やMoLG資料の取得成功は、資料の全表・全数値列を意味しない。国際共通source10候補はPSE/テーマ/年/粒度のavailabilityを未判定のまま保持する。

## 生成と検証

`inspect-palestine-pcbs-2017.py` が原本hash、Table 2の10数値列の採否、親子和、Table 29の物理行を検査する。`import-palestine-pcbs-2017-partial.py` と `import-palestine-molg-planning.py` が国内値と全国資料を接続し、`register-palestine-official-source-leads.py` が未採用の公式所在を記録する。候補は**19地域、16指標、388観測（うちPCBS国内76）、資料2、図形0**。dataset SHA-256 `0f66351ca0b4701e3aa637b45d5ee1926bbd50e9d57cddc79c66bd97b6da5908`。採用tuple SHA-256 `c8338c5caa3b50d53f00edd1b63c1f6d9584cab53687f07d59e05d2bdd688440`。

独立したPSE再初期化候補へ5原本とreceiptをコピーし、同じ検査・取込を実行した。19地域、76採用値、全国資料2件、公式source候補7件と採用tupleが一致した。`validate-country` は0 errors/0 warnings。`npm run check`、`npm test`（218/218）、build、7地域の診断CSV/HTML・計画HTML・根拠CSVで期間、出典URL、親子件数、初行・末行・hashを照合した。ブラウザーでは Palestine→West Bank→Jenin→West Bank全体、および Gaza Strip→Gaza Governorate の切替、計画・テーマ診断のURL、見出し、数値、資料スコープを確認した。Jeninの画面で全国WDI値は地方値として残らず、Gaza県ではガザ広域1,899,291を県人口652,597へ誤流用しなかった。

これは制作側の標本検証である。42シナリオの全実施、保存・メモ・Word/PDF/印刷全頁、法定境界と個別計画の監査、独立 `ACCEPT`、公開検証は**未実施**。Asia入口の `INCOMPLETE AUDIT` は維持し、Hosting/Publicへの配備は行わない。
