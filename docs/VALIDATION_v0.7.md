# 実行テンプレート0.7 検証記録

## 対象

- データ実装commit: `c3f938a6c45d6d3f77325ac73769d0c04677e6b0`（中米7か国の公式国勢調査人口アダプター）
- 公開実装commit: `6920735a4d740c27536625a73a3f7e59e071d417`（Apache/LiteSpeed向けmodule MIME設定を含む）
- 検証日: 2026-09-15 JST
- 環境: Windows、Node.js 24.11.1、Python 3.12.14、Codex in-app browser
- データschema: 0.2。国勢調査正規化中間データ: 1.0
- 実取得原本: `.work/census-acquisition-2026-09-15-central-america-7-v5/`
- 再利用可能な正規化データ: `data/census/central-america-population-v0.7.json`
- 生成案件: `.work/areadata-ca-v0.7-census-final-4/`

この版は、ラテンアメリカ展開前のスケーラビリティ確認として、中米7か国の異なる国勢調査年と異なる行政階層を一つのAreaData実行版へ接続したものである。人口以外の国内国勢調査テーマ、国内境界polygon、計画法・計画資料は完成扱いにしない。

## 原本取得と固定

manifestに登録した公式HTTPS URLだけを取得し、既存原本を上書きせず、形式署名・容量・redirect先host・SHA-256を記録した。主原本は12件要求、12件取得、失敗0件、合計19,661,402 bytes。Hondurasの市別PDFは公式WordPress APIから2013年の投稿を探索し、299投稿候補を298固有PDFへ重複排除して、298件取得、失敗0件、合計250,090,271 bytesだった。

| source ID | 国勢調査年 | bytes | SHA-256 |
|---|---:|---:|---|
| `BLZ_C2022_POP_SETTLEMENT_SEX` | 2022 | 31,021 | `c7be751b1ef0aaf09da65df90413bd4e12272676622a82bffb29fc686543b4ea` |
| `BLZ_C2022_GENERAL_CHARACTERISTICS` | 2022 | 69,401 | `8d649118178f8cc01f9188c049489a9e02817439cdaf78dfe704cd254bf3cdfc` |
| `BLZ_C2022_HOUSING` | 2022 | 79,758 | `caa94f3f50ec43906dba2f59ec4f4a9eb99e8281379a4e927bef6c0bfc65eaa0` |
| `GTM_C2018_POP_SEX_AGE_AREA` | 2018 | 4,072,815 | `b4dfbc6a0373373e8f35827ef5a8d5ed07db5d035225a271061b1869769e96d9` |
| `GTM_C2018_POPULATED_PLACE_CENTROIDS` | 2018 | 1,105,747 | `b8ea8fea33e6d606e102e8d96ed692deacec660c028ffcf673f84459bcafe14e` |
| `SLV_C2024_POP_GEO_AGE_SEX` | 2024 | 1,367,910 | `24a1c701f6fcadbf89a7ed3fadc4cb3735f28a4c194dbea82f5556c6102e85f1` |
| `HND_C2013_GENERAL_POPULATION_TOME1` | 2013 | 3,050,064 | `b549cac85468dfc731c1b158c06f3028f7b2565ba09a524bbc17b17199f65c9a` |
| `NIC_C2005_OFFICIAL_FIGURES_TABLES` | 2005 | 1,216,879 | `48342b8ba3d5aad199554df86060c6ad96d228e519f0135f42f82d6703bf35ae` |
| `CRI_C2022_POP_HOUSING_ESTIMATED_RESULTS` | 2022 | 8,466,179 | `9735bc4170da604e287b6a830adad075da93aa618f76192545586bd2c9a61022` |
| `CRI_C2022_CANTON_POPULATION_ARCGIS` | 2022 | 10,090 | `5d42ab0c7bbbf7ebc7df5291ca17a559ae9c3a4733da73a64f057d98f8c88175` |
| `CRI_C2022_PROVINCE_POPULATION_ARCGIS` | 2022 | 1,143 | `7653d44b6391c5061572500d1ed0c7fb9ef1d08cfb3477ef92fb01769fe2d43a` |
| `PAN_C2023_VOLUME5_TABLE1` | 2023 | 190,395 | `90a124d77307f20f615f63a642e5c4a92ef7f491bb0145c78064ba07c959b23e` |

公式掲載先は各source recordに保持した。代表的な掲載先は、[Honduras INE 2013 census](https://ine.gob.hn/censo-de-poblacion-y-vivienda-2013/)、[Nicaragua INIDE 2005 census](https://www.inide.gob.ni/docu/censos2005/censo2005.htm)、[Costa Rica INEC tools](https://admin.inec.cr/herramientas)、[Panama INEC 2023 census volume](https://www.inec.gob.pa/publicaciones/Default3.aspx?ID_CATEGORIA=19&ID_PUBLICACION=1231)である。

## 国別採用結果

| 国 | 年 | 採用した最下位層 | 追加地域 | 観測 | internal comparison | terminal ID | 判定 |
|---|---:|---|---:|---:|---:|---:|---|
| Belize | 2022 | district | 6 | 7 | 1 | 0 | 全国値と6 districtを採用。localityは監査のみ。子比較がないためdistrictで停止 |
| Guatemala | 2018 | municipality | 362 | 363 | 23 | 340 | 全国、22 department、340 municipalityを採用 |
| El Salvador | 2024 | district | 320 | 321 | 59 | 262 | 全国、14 department、44 municipality、262 districtを採用 |
| Honduras | 2013 | municipality | 316 | 316 | 19 | 298 | 全国、18 department、298 municipality台帳。Espartaの値1件を保留 |
| Nicaragua | 2005 | municipality | 170 | 171 | 18 | 153 | 全国、17第一層、153 municipalityを採用 |
| Costa Rica | 2022 | canton | 89 | 90 | 8 | 82 | 全国、7 province、82 cantonを採用 |
| Panama | 2023 | corregimiento | 794 | 795 | 96 | 699 | 全国、13第一層、82 district、699 corregimientoを採用 |
| **合計** | — | — | **2,057** | **2,063** | **224** | **1,834** | 国別正規化レイヤーの合計 |

生成dataset全体は2,065地域、2,227観測、21 source、225 internal comparison、1,834 terminal IDを持つ。

採用時に次の例外を隠していない。

- El Salvadorの全国人口は6,029,976。`No Especificado` 107,055人を全国値には含めるが、行政地域として生成しない。14 department、44 municipality、262 districtの既知地域合計との差を監査に残す。
- Hondurasの全国人口は8,303,771、18 department合計は8,303,770で、公式表の1人差を保持する。市別PDFのEsparta `01-03`は表紙名がEspartaである一方、14,559がSan Francisco `01-06`と一致し、Atlántidaの親値とも整合しないため、地域は保持して観測を保留した。残差18,449を推定値として埋めない。ほかの9 departmentの1～2人差も親公式値を置換しない。
- NicaraguaとPanamaの採用表には公式code列がないため、source順の内部IDを付け、公式codeとは表示しない。
- Costa Rica 2022は部分的な実査を補正した公式推計結果であり、完全列挙と表示しない。別系列の2026人口推計表は国勢調査人口へ混ぜない。
- Belizeの全国・districtは重み付き原値を保持する。地域合計やUIは人数として整数表示し、JSONと出力では原精度を残す。locality表のdistrict配分不一致は未解決のため採用しない。

## 広域集計と異なる年度

広域値は各国の正確な全国観測だけを使い、下位地域の行を足して再構成しない。7か国がすべて揃い、人口概念・非重複・出典を確認したため、次の混合基準年合計を表示する。

| 国 | 採用年 | 全国人口原値 |
|---|---:|---:|
| Belize | 2022 | 397,483.45623886667 |
| Guatemala | 2018 | 14,901,286 |
| El Salvador | 2024 | 6,029,976 |
| Honduras | 2013 | 8,303,771 |
| Nicaragua | 2005 | 5,142,098 |
| Costa Rica | 2022 | 5,044,197 |
| Panama | 2023 | 4,064,780 |

原値合計は43,883,591.45623886667、画面表示は43,883,591人である。全画面、比較表、出力に各構成国の実年を渡し、同一年の人口とは表示しない。7か国のうち一つでも全国値が欠けるデータ版では、この広域値を生成しない契約を自動試験で確認した。

## 自動検証

| 検証 | 結果 |
|---|---|
| `npm run check` | 51 JavaScript module・JSONを構文確認、合格 |
| `npm test` | 140件中140件合格 |
| Python `py_compile` | 2 script合格 |
| `node scripts/create-central-america.mjs ... --census-data data/census/central-america-population-v0.7.json` | 248 country/area、3,544国際参照値の保存原本から再生成成功 |
| `node scripts/validate-country.mjs --project .work/areadata-ca-v0.7-census-final-4` | error 0、warning 10 |
| `git diff --check` | 合格 |

validator警告は、source terms要確認9件と、確認済み国別planning documentなし1件である。公開配布条件の確定前に原資料の再配布条件を確認する。取得・hash・データ採用の合格と、再配布許諾の確認を同一視しない。

## 実画面確認

`http://127.0.0.1:4178/`の最終生成版と、`https://areadata.net/`の公開版をデスクトップのin-app browserで確認した。

- 地域診断の中米入口は7か国を全件表示し、広域人口43,883,591人、7/7の構成国、BLZ 2022、GTM 2018、SLV 2024、HND 2013、NIC 2005、CRI 2022、PAN 2023を表示した。
- テーマ診断は`7 observed / 7 comparable areas`、範囲397,483～14,901,286、各順位行に実年を表示した。検索の有無にかかわらず比較集合は7か国である。
- El SalvadorでAhuachapán department 348,880、Ahuachapán Centro municipality 180,913、同市内4 districtを確認した。district選択後に同じmunicipalityを選び直すとdistrictが解除され、さらに同じAhuachapán departmentをnative dropdownから選び直すとmunicipalityとdistrictが解除された。見出し、URL、値、内部比較が親全体へ更新し、指標`CENSUS_POP_TOTAL`と`latest-available`を保持した。
- HondurasのEsparta `01-03`は地域名・所属・codeを保持し、人口は`No data / incomplete coverage`と表示した。14,559や残差18,449を自動補完していない。
- source/gap欄の広域人口は43,883,591人と読みやすく表示し、原精度をdata exportに保持する説明を付けた。

## FTP公開と公開確認

2026-09-15 JSTに、生成案件の`site/`配下16ファイル、2,524,236 bytesをFTPSで`v2006.coreserver.jp:/domains/areadata.net/public_html`へ公開した。公開直前の既存ファイルを`.work/ftp-backups/areadata.net-before-v0.7-2026-09-15/`へ退避し、MIME修正版の再公開前も`.work/ftp-backups/areadata.net-before-mime-fix-v0.7-2026-09-15/`へ退避した。既存の`cgi-bin/.htaccess`は変更していない。

初回公開後、サーバーが`.mjs`を`application/octet-stream`で返し、ブラウザがmoduleを実行できないことを確認した。生成テンプレートへ`.htaccess`を追加して`.mjs`を`text/javascript`で配信する修正を行い、再生成・再検証・再公開した。修正版のGitHub Actions [Validate template](https://github.com/mnakagaw/DDPT-World-Template/actions/runs/34906397912)は成功した。

- FTPS転送後に16ファイルすべてを再取得し、ローカル生成物とSHA-256が一致した。
- HTTPで取得可能な15ファイルは、`https://areadata.net/`から再取得してbytesとSHA-256がすべて一致した。`.htaccess`はHTTP 403のため、FTPS再取得結果で一致を確認した。
- 公開トップは中米7か国、2,065地域、人口43,883,591人、構成国ごとの実際の国勢調査年を表示した。
- 公開地域診断でAhuachapán Centro municipality 180,913人、下位district Ahuachapán 127,301人、上位Ahuachapán department 348,880人を照合した。
- district選択後に同じmunicipalityを選び直すとdistrictが解除され、続けて同じdepartmentを選び直すとmunicipalityも解除された。見出し、URL、値、内部比較が上位地域へ更新され、指標と期間は保持された。
- 公開テーマ診断は7 observed / 7 comparable areas、公開Databaseは2,065地域・2,182 source-reported values・5 indicatorsを表示した。
- 公開Planningは選択地域を引き継ぎ、確認済みの計画主体・資料が未収録であることを明示した。

## 42シナリオの適用結果

`templates/ACCEPTANCE.md`をこの人口試作の採用範囲へ適用した。`合格`は今回の自動試験または実画面で証拠を得た範囲だけを示す。

| ID | 結果 | 今回の証拠・理由 |
|---|---|---|
| A01 | 合格 | El Salvadorのdepartment→municipality→district→同じ親をローカル・公開実画面で確認。地図がない階層は代替表示 |
| A02 | 未実施 | planning資料が未収録 |
| A03 | 未実施 | 再読込は自動試験済みだが、実ブラウザの戻る・進む一式は未実施 |
| A04 | 未実施 | 全地域検索は実装済み。数千地域の実操作記録は未作成 |
| A05 | 合格 | 中米→7か国のKPI・地図・全件表をローカル・公開実画面で照合 |
| A06 | 未実施 | 3機能間の全件数・日付照合は未完了 |
| A07 | 合格 | zero、missing、取得失敗、意味差を自動試験。Esparta欠測を実画面確認 |
| A08 | 合格 | 境界なしの地方値、全国値のみ、欠測、historical boundaryを自動試験。実画面も代替表示 |
| A09 | 対象外 | 今回の生成版に認証付き文書取得を採用していない |
| A10 | 未実施 | HTML・Markdown・CSVの自動内容試験は合格。最終生成版からの手動全取得・印刷は未実施 |
| A11 | 合格 | 静的datasetで非同期の逆順応答は発生しない。高速選択と旧地域残留を自動試験 |
| A12 | 対象外 | 保存・地域別メモを今回の生成版に採用していない |
| A13 | 合格 | 章リンクと全指標下の比較を実画面確認 |
| A14 | 合格 | デスクトップ幅で上部選択、主要分析、次操作をローカル・公開実画面で確認 |
| A15 | 未実施 | 768/375/320px、200%拡大の一式は未実施 |
| A16 | 未実施 | 現地語UIと長い名称の多言語確認は未実施 |
| A17 | 対象外 | 文章生成を今回の生成版に採用していない |
| A18 | 未実施 | 更新失敗時last-goodは自動試験済み。低速回線・背景地図障害の実画面確認は未実施 |
| A19 | 合格 | 7全国値を優先し、Honduras親子差とEspartaを補完しないことを抽出・画面で確認 |
| A20 | 未実施 | 自治体職員による実利用試験は未実施 |
| A21 | 合格 | district→同じmunicipalityをnative dropdownで再選択し、下位解除と指標・年保持をローカル・公開実画面で確認 |
| A22 | 合格 | municipality→同じdepartmentをnative dropdownで再選択し、下位解除と親値への更新をローカル・公開実画面で確認 |
| A23 | 未実施 | 状態復元の自動試験は合格。実ブラウザの履歴一式は未実施 |
| A24 | 未実施 | mapから検索で隠れた行を出す自動試験は合格。最終生成版での手動確認は未実施 |
| A25 | 対象外 | 人口ピラミッド・原図を今回の生成版に採用していない |
| A26 | 対象外 | 水域背景を今回の生成版に採用していない |
| A27 | 合格 | planning拡張なしschema 0.2 datasetの後方互換自動試験が合格 |
| A28 | 対象外 | 国別planning区分をまだ採用していない |
| A29 | 合格 | 同名別行政型、code・境界版・対象IDの誤結合拒否を自動試験 |
| A30 | 未実施 | source段階の契約試験は合格。実planning本文が未収録 |
| A31 | 合格 | 統計年と資料独自期間の分離、不正日付の拒否を自動試験 |
| A32 | 対象外 | 国内公式状態地図をまだ採用していない |
| A33 | 対象外 | 実予算・実績・評価資料をまだ採用していない |
| A34 | 合格 | 再取得・検証・生成失敗でlast-goodを保持する自動試験が合格。HANDOFFから再生成成功 |
| A35 | 合格 | 上部の地域選択と指標ごとの下部比較を実画面確認 |
| A36 | 合格 | 7か国比較とEl Salvador各階層の同年・同定義・同単位集合を実画面確認 |
| A37 | 合格 | project独自7か国範囲とUN M49 013との差を表示。国際参照系列と国勢調査を分離 |
| A38 | 合格 | terminal ID優先と、明示されたEl Salvador district比較の例外を自動・実画面確認 |
| A39 | 合格 | 内部比較の注目操作が上部対象を変えない自動試験が合格 |
| A40 | 合格 | 親公式値優先、欠測、意味差、比較除外、階級境界を自動試験。Espartaを実画面確認 |
| A41 | 未実施 | 全行を含む出力の自動試験は合格。最終生成版の実ダウンロード・全表印刷は未実施 |
| A42 | 合格 | 旧dataset・URL・出力互換と同じ親への再選択を自動試験 |

結果は、合格21、未実施13、対象外8である。42件のシナリオが存在することを42件合格とは報告しない。

## 未実施・次工程

- 各国原本の人口以外の全表・変数を棚卸しし、性別・年齢・住宅・教育・就業等を分母・定義・地域粒度とともに採用する。
- 7か国の国内地域を、確認済み公式codeと同一版のpolygonへ結合する。名称だけで結合しない。
- source terms要確認9件を確認し、公開できる原本・派生データ・メタデータを分ける。
- 7か国の計画法、計画主体、既存計画、予算・実績・評価資料を国別アダプターで収集する。
- モバイル、200%文字拡大、戻る・進む、実ダウンロード、全行印刷、自治体職員による実利用試験を行う。
- MariaDBへimportし、数万自治体・複数年・複数指標でquery、index、更新単位、API応答時間を測る。
- 今後の公開更新では、生成物のFTPS hash照合に加え、`.mjs`のContent-Typeと主要4画面の読込を継続して確認する。

中米7か国の公式国勢調査人口レイヤーは、ローカル生成、GitHub保存、FTPS公開、公開画面確認の対象として合格した。AreaData全体、国内国勢調査の全テーマ、AreaPlanを完成扱いにはしていない。
