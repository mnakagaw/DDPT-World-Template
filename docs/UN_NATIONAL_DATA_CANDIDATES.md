# 国連システムの国別統計：AreaData導入候補

確認日：2026-09-23。これは**取得先と指標の候補台帳**であり、全指標・全国家の実データ取得やAreaDataへの採用完了を示さない。各候補は、対象国・年・定義・利用条件・欠測を調べてから採用する。専門機関の国際推計と各国の公式国勢調査は別系列で保持する。

| 優先 | 分野・国レベルで取得する候補 | 原ソース | 主な値の型と広域集計 |
| --- | --- | --- | --- |
| A | 総人口、男女・年齢別人口、出生、死亡、純移動、平均寿命、出生率 | [UN DESA World Population Prospects](https://population.un.org/wpp/) | 人数は同一年・同じ推計版・重複のない地域を確認して合計。率・平均寿命は単純合計・平均しない。推計と将来推計を区別。 |
| A | 難民、庇護申請者、国内避難民、無国籍者、帰還者、出身国・庇護国別人口 | [UNHCR Refugee Data Finder API](https://www.unhcr.org/refugee-statistics/insights/explainers/forcibly-displaced-api.html) | 人数でも集団・基準日・出身地／受入地を指定し、重複を避ける。国勢調査人口とは別系列。 |
| A | 国際貧困線・国内貧困線以下の人口比率、社会保障の対象範囲 | [UNSD SDG Global Database/API](https://unstats.un.org/SDGAPI/swagger/) | 主に率。貧困線・PPP版・調査年・元のcustodianを保存。率に人口を掛けて人数を推定する場合は別の計算値と明記。 |
| A | 労働参加率、就業率、失業率、若年NEET率、非公式雇用、賃金 | [ILO ILOSTAT](https://ilostat.ilo.org/data/) | 率・金額は単純合計不可。男女・年齢別とモデル推計／国報告値を区別。 |
| A | 平均寿命、母子死亡率、死因別死亡、感染症、予防接種、保健サービス | [WHO Global Health Observatory API](https://www.who.int/data/gho/info/gho-odata-api) | 人数と率を区別。年・性別・年齢・推計手法の違いを保持。 |
| A | 就学、修了、就学していない児童、識字、教員、生徒、教育支出 | [UNESCO UIS Data Browser/API](https://databrowser.uis.unesco.org/resources) | 人数と率を区別。ISCED水準、学年・年度・性別を保持。 |
| A | 安全に管理された飲料水・衛生設備、基本的な水・衛生・手洗いサービス | [WHO/UNICEF JMP](https://washdata.org/data) | 普及率は単純平均不可。人口分母を確認した推定人数と原公表人数を分ける。都市／農村と一部の国内地域も存在。 |
| A | 5歳未満・新生児死亡、発育阻害、消耗症、過体重、予防接種、出生登録 | [UNICEF Data Warehouse](https://data.unicef.org/open-data/) | 子どもの人数・死亡数と率を区別。調査値・国際モデル推計を分ける。更新年は指標で異なる。 |
| A | 栄養不足、食料不安、作物・家畜の生産量、農地面積、農産物貿易 | [FAOSTAT / FAO Country Profiles](https://www.fao.org/statistics/country-profile-tool) | 生産量等は品目・単位・年が一致すれば合計候補。割合、収量、栄養不足率は不可。 |
| B | GDP、産業別付加価値、政府・家計消費、投資、1人当たりGDP | [UNSD National Accounts Main Aggregates](https://unstats.un.org/unsd/snaama/downloads) / [API](https://unstats.un.org/unsd/amaapi/) | 同一価格基準・通貨・年の総額のみ合計候補。1人当たり額、成長率、異なる通貨の額は合計しない。 |
| B | 輸出入、貿易収支、サービス貿易、海外直接投資、送金 | [UNCTADstat](https://unctadstat.unctad.org/datacentre/) | フロー・ストック、名目通貨、相手国別行の二重計上に注意。国別公表と分析値を分ける。 |
| B | インターネット利用者、携帯・ブロードバンド加入、通信網カバー率、料金 | [ITU DataHub](https://datahub.itu.int/about/) | 個人利用率・加入契約数・人口カバー率は異なる概念。DataHubの再利用条件を確認。 |
| B | 故意殺人、犯罪被害、人身取引の検知被害者、被収容者 | [UNODC Data Portal](https://data.unodc.org/) | 発生件数、検知件数、率を分ける。法制度・報告範囲の国差に注意。 |
| B | 災害による死亡・行方不明、被災者、直接経済損失、国家防災戦略 | [UNDRR Sendai Framework Monitor](https://www.undrr.org/implementing-sendai-framework/monitoring-sendai-framework/sfm-data-and-analytics) | 報告国・報告年・災害範囲に欠測がある。金額の価格基準と期間を確認。 |
| B | HDI、MPI、不平等調整HDI、ジェンダー不平等指数 | [UNDP Human Development Data](https://hdr.undp.org/data-center/documentation-and-downloads) | 複合指数は合計・単純平均不可。MPIは国・調査年の対象範囲が限定される。 |
| C | 温室効果ガス排出・吸収量と部門別排出 | [UNFCCC GHG Data Interface](https://unfccc.int/process-and-meetings/transparency-and-reporting/reporting-and-review/transparency-data-and-tools/greenhouse-gas-data/data-interface-help) | 提出制度・報告基準・カバー年が国群で異なる。異制度の値を無確認で合計しない。 |
| C | 女性への暴力に関する調査値、法律・政策・予算措置 | [UN Women Data Hub](https://data.unwomen.org/global-database-on-violence-against-women/about) | 調査値と国際比較用モデル推計、政策の有無を分ける。毎年の全国家時系列とは扱わない。 |

## 共通取得口と優先順位

[UNSD SDG Global Database](https://unstats.un.org/sdgs/indicators/en/)には複数機関の国別系列が集まる。横断検索の入口として便利だが、元のcustodian、系列コード、改訂版、脚注を残し、同じ指標を原機関データと二重登録しない。国際貧困指標などには国連以外の機関がcustodian・データ提供者となる系列もあるため、「UNSDで配信」を「国連が原数値を作成」と言い換えない。SDGデータは[API](https://unstats.un.org/SDGAPI/swagger/)と[SDMXサービス](https://unstats.un.org/sdgs/iaeg-sdgs/sdmx-working-group/)から取得可能。

最初の実装は、国別表示と広域地図の土台になる **WPP人口 → JMP水衛生 → ILO雇用 → UIS教育 → WHO/UNICEF保健・栄養 → UNHCR避難 → UNSD貧困・国民経済計算** の順がよい。これはAreaData向けの実装優先案であり、特定の国の数値の採用・網羅率を確認済みという意味ではない。国連機関でも指標ごとに対象国と年が違うので、採用前に利用可能な国数・年数と欠測分布を機械的に算出する。

## AreaDataに保存する属性

`source_id`、原機関、配信機関、系列コード、国コード体系、指標定義、単位、分母、年／基準日、推計・予測・報告値の区別、改訂版、取得日時、原URL、原ファイルhash、利用条件、欠測状態、集計許可方式を観測値に結び付ける。国・地域の上位値は出典の同一範囲公表値を優先し、独自計算は完全・非重複・同期間の被覆が確認できる場合だけ別ラベルで出す。率・平均・指数を単純平均せず、国内の県・市に国の値を転記しない。
