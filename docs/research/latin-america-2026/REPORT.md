# ラテンアメリカの国勢調査・地方計画制度とDDPT業務の自動化

調査基準日：2026-09-13。対象：ラテンアメリカ20主権国家。研究版1.0。

## 結論

世界版の入口は、**各国の計画制度に沿った「国勢調査を基礎とする自治体診断・計画作成支援」**とする。法定計画主体の地域単位を先に決め、人口・住宅・水衛生・教育などを国勢調査からそろえる。その上で、計画に必要な不足項目を省庁別資料から補い、地域診断、要求、事業、計画草案、実施・見直しを根拠付きでつなぐ。

ドミ共で行ったDDPTの地域診断・Temático、計画策定の基礎資料、住民要求・事業情報の整理を、この自動化の業務モデルとする。国勢調査の表を一つの地域コード体系で取り込めれば、人口・住宅・サービス等を一括で扱える。一方、学校や病院の供給能力、経済活動の実績、道路、防災、予算・公共投資、承認済み計画は引き続き別資料が必要になる。

自動化する中心は、資料の探索・取得・変換・照合・比較・根拠付き下書き・様式転記・更新差分である。地域が何を課題とするか、何を優先し、誰がどの資金で実施するかは、記録された現地の判断に接続する。草案と正式な計画、AIの提案と住民の合意を区別する。

## 調査の範囲と読み方

対象はCEPALのLatin America区分の20主権国家。英語圏カリブ、ベリーズ、ガイアナ、スリナムは今回の20か国に含めない。Puerto Ricoも主権国家ではないため対象外。Latin America and the Caribbean全33か国の調査とは区別する。[CEPALの区分](https://statistics.cepal.org/yearbook/2025/docs/2500481_AE2025_notas_estadisticas_sociales.pdf)

このレポートは公式統計サイト、調査票・辞書・集計目録、法令原文・政府の制度資料を照合したデスク調査である。国別の全数値取得、全自治体の境界結合、全法令・州法・条例の現行改正審査を済ませたものではない。法律そのもの、政令、行政規範、運用ガイドを含む「主要制度の一覧」であり、各国のすべての計画関連法を網羅する法令集ではない。

「公表目録確認」は全表の数値点検完了ではない。「調査票／変数辞書確認」は、その地域粒度で利用できる数値が公表されたことを保証しない。「未確認」は、未収録・未公開・不存在の断定ではない。細かい粒度の地図が存在しても、すべてのテーマの統計が同じ細かさで提供されるとは限らない。

制定年は最初の制定・発出年を基本とし、参照している改正法や統合本文の年は別に説明した。アルゼンチン憲法の1994は自治体自治に関する参照改正年。機関名は2026時点の政府資料を優先したが、個別の提出部署・権限移管で確認が残る箇所を明記した。

## 20か国の調査年と計画単位

「詳細利用候補年」は、すべての項目・自治体について統合検証した年ではない。ペルー2025のように最新結果が段階公表の場合、項目ごとに旧年データが必要になる。

| 国 | 調査年／段階 | 詳細利用候補年 | 計画主体と計画 | 確認した統計粒度・注意 |
| --- | --- | --- | --- | --- |
| [アルゼンチン](https://redatam.indec.gob.ar/) | 2022：2022確報・REDATAM公開 | 2022 | municipio／comuna等の地方政府（州法別）；州法・地方条例に基づく地域／都市計画 | departamento／partido／comuna（表別）。departamentoと自治体は全国で同一ではない。機微項目の粒度制限あり。 |
| [ボリビア](https://cpv2024.ine.gob.bo/index.php/tabulados-sobre-la-tematica-pobreza/) | 2024：2024 municipio/TIOC別表公開 | 2024 | municipio・departamento／TIOC；PTDI／先住民自治はPGTC等 | municipio／TIOC。TIOCと通常のmunicipioの制度・地域対応を分ける。NBIは所得貧困と別。 |
| [ブラジル](https://www.ibge.gov.br/estatisticas/sociais/trabalho/22827-censo-demografico-2022.html?edicao=41852&t=resultados) | 2022：2022全数・標本結果を別公開 | 2022 | município（計画別に適用要件）；Plano Diretor／財政計画は別制度 | município。標本と全数の公開粒度を区別。ネットは標本項目。全数のセクター細分性をネット等の標本値に転用しない。 |
| [チリ](https://censo2024.ine.gob.cl/resultados/) | 2024：2024結果・小地域データ公開 | 2024 | comuna（municipalidad）；PLADECO | comuna。固定・モバイル・衛星ネットの複数回答を単純合計しない。 |
| [コロンビア](https://www.dane.gov.co/index.php/estadisticas-por-tema/demografia-y-poblacion/censo-nacional-de-poblacion-y-vivenda-2018/herramientas) | 2018：CNPV2018・地域集計と変数辞書公開 | 2018 | municipio／distrito・departamento；Plan de Desarrollo Territorial（PDT）／POTは別 | municipio。ネットは住宅の固定／モバイル接続。就業状態から産業別生産を推測しない。 |
| [コスタリカ](https://admin.inec.cr/sites/default/files/2024-11/meSocialMetodologiaEstimacionesSocialesVivienda2022.pdf) | 2022：不完全収集を補正した2022公式推計 | 2022 | cantón（municipalidad）；Plan de Desarrollo Municipal／PAO等 | provincia／cantón／distritoの推計指標。44社会住宅指標は補正推計。実査の全数値として扱わず、地区別の品質を確認。 |
| [キューバ](https://celade.cepal.org/censosinfo/Boletas/CU_BDef_2012.pdf) | 2012：確認できた詳細調査は2012。UNSDは2026を予定表記 | 2012 | municipio（provinciaとの接続）；Estrategia de Desarrollo Municipal | municipioの公表データ取得は未確認。2012調査票の設問を確認。現行ONEIの地方別データ取得・2026結果は未確認。 |
| [エクアドル](https://www.censoecuador.gob.ec/resultados-censo/) | 2022：2022結果表・テーマ別データ公開 | 2022 | provincia・cantón・parroquia ruralのGAD；PDOT | cantón／parroquia（項目別）。農村parroquiaは自治政府。都市parroquiaを同じ法定計画主体と扱わない。 |
| [エルサルバドル](https://censo2024.bcr.gob.sv/wp-content/uploads/tablas-geoportal/2025/Informe%20_VII_Censo_de_Poblacion_y_VI_de_Vivienda_marzo_2025.pdf) | 2024：2024結果報告・地理ポータル公開 | 2024 | 44 municipios（262 distritosは下位区分）；自治体開発計画／土地利用計画を類型別確認 | municipio・distrito（項目別）。住宅表はdepartamento例。2023再編法による2024からの44自治体と旧262自治体を混同しない。 |
| [グアテマラ](https://censo2018.ine.gob.gt/explorador) | 2018：2018地域集計・地域内小地区資料公開 | 2018 | municipio；PDM-OT | municipio。個人ネット利用7歳以上と世帯のネット設備を分ける。 |
| [ハイチ](https://ihsi.gouv.ht/recensement/autres_resultat_rgph_2003) | 2003：RGPH2003が公式サイトで確認できる詳細結果 | 2003 | commune；Plan de Développement Communal（PDC） | communeは人口・就業の一部。住宅設備は全国表を確認。古い基準年。近年の人口推計・人道データを2003調査値へ混ぜない。 |
| [ホンジュラス](https://ine.gob.hn/2015/06/15/tomo-5-genero-2013/) | 2013：2013詳細結果。2026は準備・実施関連情報で結果未確認 | 2013 | municipio；PDM-OT | municipio（298自治体別報告の目録）。2026という事業名や準備記事を公表済み国勢調査結果と扱わない。 |
| [メキシコ](https://inegi.org.mx/rnm/index.php/catalog/632) | 2020：2020全数基本票・標本拡大票。2025中間調査は別 | 2020 | municipio／CDMX alcaldía（州・特別制度別）；州法に基づくPDM／都市開発計画等 | 基本票・標本ともmunicipio、ただし提供項目差。基本38問と拡大103問を区別。拡大票は小街区までの推計を保証しない。 |
| [ニカラグア](https://www.inide.gob.ni/docu/censos2005/censo2005.htm) | 2024：2024実施情報あり。詳細結果は未確認、2005公開表を採用候補 | 2005 | municipio；Plan de Desarrollo Municipal | 2005 municipio別巻。調査年2024と実際に使える詳細2005を分ける。古い値を最新と表示しない。 |
| [パナマ](https://www.inec.gob.pa/publicaciones/Default3.aspx?ID_CATEGORIA=19&ID_PUBLICACION=1231) | 2023：2023 Vol.V lugares poblados等公開 | 2023 | distrito（municipio）。comarca等の特別制度は別確認；Plan Estratégico Distrital（PED） | distrito／corregimiento／lugar pobladoの選定指標。小地域表は選定項目。comarca・corregimientoを一律に自治体へ置換しない。 |
| [パラグアイ](https://censo2022.ine.gov.py/) | 2022：2022確報・住宅巻・地区地理指標公開 | 2022 | municipio／distrito；PDS／POUT | distrito。住宅設備表と個人票・NBI・先住民調査を別に照合する。 |
| [ペルー](https://www1.inei.gob.pe/estadisticas/censos/) | 2025：2025結果公表開始・地区人口確認。2017詳細システムも利用可能 | 2025 | municipalidad provincial／distrital（地域政府はPDRC）；PDLC | 2025 distrito人口。テーマ結果はdepartamentoの公表例確認。2025の人口地区表を、全テーマ地区公開済みという意味にしない。必要時は2017を別系列で採用。 |
| [ドミニカ共和国](https://www.one.gob.do/datos-y-estadisticas/temas/censos/poblacion-y-vivienda/2022/) | 2022：2022結果表・2026刊行の水衛生特集等 | 2022 | municipio（distrito municipalは権限・適用を別確認）；PMD／上位の地域・県計画を区別 | municipio／distrito municipal（項目別）。個人ネット5歳以上・過去3か月と世帯の接続を混同しない。2026刊行でも統計年は2022。 |
| [ウルグアイ](https://www.gub.uy/instituto-nacional-estadistica/politicas-y-gestion/microdatos-censo-2023-ponderados) | 2023：2023加重版（2026年5月更新）。旧2024版は置換済み | 2023 | municipio（管理・開発）＋departamento（土地利用）；PQM／POA、部門政府の土地利用計画 | 2026版でmunicipio／localidad等を拡張。旧版との混在不可。個票行数を人口総数にせず、公式ウェイトと母集団に従う。 |
| [ベネズエラ](https://celade.cepal.org/censosinfo/Boletas/VE_BDef_2011.pdf) | 2011：詳細票2011確認。UNSDの2021実施日記録は結果と未照合 | 2011 | municipio（州・コミューン計画と区別）；Plan Municipal de Desarrollo | municipio／parroquiaは票で識別。公開表未取得。2021記録の意味・結果公表を確定できていない。2011を現在人口・設備率として扱わない。 |

## テーマから見た共通化

次の18分野は本調査で作成した探索候補であり、OWIDの公式18分類でも全国家での必須メニューでもない。OWIDを広いテーマの探索に使い、定義は国連の国勢調査勧告・SDGメタデータと国内統計の定義で照合する。国際データの多くが国レベルであるため、地方自治体の実数値の代わりにはしない。[OWID](https://ourworldindata.org/)、[UN_REC](https://unstats.un.org/unsd/publication/SeriesM/Series_M67Rev4en.pdf)、[SDG](https://unstats.un.org/sdgs/metadata/)。

| 分野 | 国勢調査の候補項目 | 国勢調査の役割 | 補完する資料 | 計画での使い方・比較条件 |
| --- | --- | --- | --- | --- |
| 人口・世帯 | 人口、性・年齢、世帯構成 | 国勢調査を優先 | 統計局の人口推計・住民登録 | 計画の対象人口・将来需要。基準年と推計年を分ける |
| 住宅・居住 | 住宅材料、保有、過密、居住状態 | 国勢調査を優先 | 住宅省・地籍・集落台帳 | 住宅改善の対象。都市計画区域と行政区域を照合 |
| 水・衛生 | 水源、配管、便所、排水 | 国勢調査を優先 | 水道事業者・保健省・JMP | 水道接続と安全に管理された水は別。水質・時間・継続性は追加資料 |
| 家庭エネルギー | 電気、照明、調理燃料 | 国・調査年による | 電力事業者・エネルギー省 | 接続と停電・料金・供給能力を分ける |
| デジタル接続 | 世帯接続、個人利用、端末 | 国・票種による | 通信規制機関・ITU・通信事業者 | 固定／モバイル、個人／世帯、年齢、利用期間をそろえる |
| 教育・技能 | 識字、就学、学歴 | 国勢調査を優先 | 教育省EMIS・学校台帳 | 住民の学歴と学校の供給・学力・定員を分ける |
| 就業・生計 | 経済活動、職業・産業、通勤 | 票種・年齢・公表条件による | 労働力調査・社会保険・雇用機関 | 失業率・非公式雇用・所得は定義差が大きい |
| 包摂・ケア・社会保障 | 障害、民族、言語、保険 | 国・定義による | 福祉省・社会保護台帳・時間利用調査 | 機能上の困難、疾患、給付受給は別系列 |
| 健康・医療 | 医療保障・受診の一部 | 補助的 | 保健省・施設台帳・保健調査・WHO | 疾病・病床・人員・到達時間は国勢調査だけでは不足 |
| 貧困・所得・格差 | NBI・住環境の欠如、一部所得 | 国・方法による | 家計調査・公式貧困地図・行政台帳 | NBI・多次元貧困・所得貧困を混同しない |
| 食料安全保障・栄養 | 人口・住宅は背景情報 | 専門資料が中心 | 栄養調査・DHS/MICS・FAO・保健省 | 栄養不良や食料不安を住宅設備から推定しない |
| 農林水産業 | 就業者の産業分類の一部 | 専門資料が中心 | 農業センサス・農林水産省 | 生産量・農地・灌漑・漁獲を人口センサスから作らない |
| 地域経済・企業・観光 | 職業・産業の一部 | 専門資料が中心 | 経済センサス・事業所台帳・観光省 | 企業数、売上、観光客と就業者数を区別 |
| 交通・アクセス | 通勤先・手段、一部自動車保有 | 国・票種による | 道路・交通省・GTFS・施設位置 | 道路状態・公共交通・到達時間は別資料 |
| 環境・資源・廃棄物 | 世帯のごみ処理方法 | 一部は国勢調査 | 環境省・気象機関・自治体廃棄物台帳 | 収集方法と処分場容量・水質・大気を分ける |
| 気候・災害リスク | 人口・住宅の曝露側 | 専門資料が中心 | 防災機関・気象・ハザード図 | 危険度・脆弱性・被災記録を別々に根拠化 |
| 治安・暴力・紛争 | 人口分母等 | 専門資料が中心 | 警察・司法・被害調査・紛争データ | 通報件数と被害率を混同しない |
| 行政・財政・参加 | 人口分母等 | 専門資料が中心 | 計画機関・自治体・予算・監査・議会 | 計画の存在、承認、執行、達成、評価を別管理 |

国別の具体的な設問・項目、確認段階、粒度、出典は[テーマ別200行の付表](THEME_DETAILS.md)に掲載した。共通して調査されやすい分野であっても、ある国の欄が未確認なら、採用前に原票・辞書・公表表を追加点検する。

水とインターネットは有力な共通指標だが、そのまま横並びにはできない。例えば住宅の給水源は、水質・継続供給まで満たす「安全に管理された飲料水」とは異なる。ブラジルの世帯ネットは標本、ドミ共の確認表は個人5歳以上・過去3か月の利用である。比較する指標名だけでなく、母集団・設問・票種・地域粒度まで一致させる。[JMP](https://washdata.org/topics/drinking-water)、[BRA_S](https://www.ibge.gov.br/estatisticas/sociais/populacao/22827-censo-demografico-2022.html?edicao=42157&t=resultados)、[DOM_C](https://www.one.gob.do/datos-y-estadisticas/temas/censos/poblacion-y-vivienda/2022/)。

## 主要計画法・制定年・所管機関

国の制度所管と地方で実際に作成・承認する主体は別である。所管機関欄には関係機関を示し、各国の自治体計画の承認権限を中央へ移す解釈はしない。下表の法令・規範は38件。

| 国 | 法令・規範 | 制定／発出年 | 概要と適用上の注意 | 国家の所管・関係機関 |
| --- | --- | --- | --- | --- |
| アルゼンチン | [Constitución Nacional（art.123）](https://www.argentina.gob.ar/normativa/nacional/804/texto) | 1994 | 1994改正で自治体自治を規定。自治体計画の義務・種類は各州法・条例を追加確認する。 | [州・地方政府の計画部局。全国一律の自治体計画所管は設定しない](https://www.argentina.gob.ar/normativa/nacional/804/texto) |
| ボリビア | [Ley 777 del SPIE](https://sea.gob.bo/digesto/CompendioII/A/2_L_777.pdf) | 2016 | 統合計画体系。PTDIの地方対象とTIOCの計画類型を区別する（art.17等）。 | [Ministerio de Planificación del Desarrollo y Medio Ambiente（MPDyMA）](https://www.gob.bo/entidades/ministerio-de-planificacion-del-desarrollo-y-medio-ambiente) |
| ブラジル | [Lei 10.257 Estatuto da Cidade](https://www.planalto.gov.br/ccivil_03/leis/leis_2001/l10257.htm) | 2001 | art.40–41。Plano Diretorは自治体域全体を対象とし、人口2万人超その他の条件に該当する都市で義務。全自治体一律ではない。 | [Ministério das Cidades（都市計画）、Ministério do Planejamento e Orçamento（国家予算計画）](https://www.gov.br/cidades/pt-br) |
| ブラジル | [Constituição Federal（計画・都市政策）](https://www4.planalto.gov.br/legislacao/legis-federal/constituicao) | 1988 | 国・州・自治体の関係、PPA等の財政計画、自治体の都市政策の憲法上の枠組み。 | [Ministério das Cidades（都市計画）、Ministério do Planejamento e Orçamento（国家予算計画）](https://www.gov.br/cidades/pt-br) |
| チリ | [Ley 18.695 Orgánica Constitucional de Municipalidades](https://www.bcn.cl/leychile/navegar?idNorma=251693) | 1988 | PLADECOを自治体の基本的計画手段とする。現行参照はDFL 1（2006）統合条文art.6–7等。 | [SUBDERE／各municipalidad（PLADECO）。都市規制は別の所管・計画](https://www.subdere.gob.cl/organigrama-subdere/organigrama.html) |
| コロンビア | [Ley 152 Orgánica del Plan de Desarrollo](https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=327) | 1994 | art.32–40等が地方計画の策定・承認・評価を規定。開発計画と土地利用計画を別管理。 | [Departamento Nacional de Planeación（DNP）／地方計画部局](https://portalterritorial.dnp.gov.co/) |
| コスタリカ | [Ley 7794 Código Municipal](https://www.pgrweb.go.cr/DOCS/NORMAS/1/VIGENTE/L/1990-1999/1995-1999/1998/9D05/17C506.HTML) | 1998 | 自治体議会の開発計画承認等。art.13の現行号記は改正で変わるため統合条文で確認。 | [MIDEPLAN（国家計画）／自治体。地方支援機関・都市規制は業務別](https://www.mideplan.go.cr/documentos_leyes?field_ano_value=&order=title&page=0&sort=asc&title=) |
| コスタリカ | [Ley 5525 de Planificación Nacional](https://www.mideplan.go.cr/index.php/marco-legal-inversion-publica) | 1974 | 国家計画体系とMIDEPLAN。自治体の計画権限・都市規制とは区別する。 | [MIDEPLAN（国家計画）／自治体。地方支援機関・都市規制は業務別](https://www.mideplan.go.cr/documentos_leyes?field_ano_value=&order=title&page=0&sort=asc&title=) |
| キューバ | [Decreto 33 Para la Gestión Estratégica del Desarrollo Territorial](https://www.gacetaoficial.gob.cu/sites/default/files/goc-2021-o40.pdf) | 2021 | art.6–8。自治体行政評議会が戦略を作成・実施・評価・更新し、自治体人民権力議会へ承認のため提出。省の計画とも接続。 | [Ministerio de Economía y Planificación（制度上の関係機関）／地方政府。現行組織図の追認は残件](https://www.gacetaoficial.gob.cu/es/gaceta-oficial-no-40-ordinaria-de-2021) |
| エクアドル | [Código Orgánico de Planificación y Finanzas Públicas（COPFP）](https://www.planificacion.gob.ec/wp-content/uploads/2021/10/Codigo-Org%C3%A1nico-de-Planificaci%C3%B3n-y-Finanzas-P%C3%BAblicas.pdf) | 2010 | art.41以下のPDOT。GADの開発・土地利用計画と財政・国家計画の関係を規定。 | [Presidencia・Secretaría General de la Administración Pública y Gabinete（旧SNPを2025吸収。2026資料確認）](https://planificacion.presidencia.gob.ec/wp-content/uploads/2026/03/3-Acta-de-reunion-RDC-2025-SNP.pdf) |
| エクアドル | [PDOT作成・更新ガイド（Acuerdo SNP-SNP-2023-0049-A）](https://www.planificacion.gob.ec/wp-content/uploads/2023/06/PDOT-ACUERDO-Nro.-SNP-SNP-2023-0049-A.pdf) | 2023 | 法令ではなく運用手引き。州・郡・農村教区等の対象を確認。案件時に後続版を確認する。 | [Presidencia・Secretaría General de la Administración Pública y Gabinete（旧SNPを2025吸収。2026資料確認）](https://planificacion.presidencia.gob.ec/wp-content/uploads/2026/03/3-Acta-de-reunion-RDC-2025-SNP.pdf) |
| エクアドル | [COOTAD](https://www.planificacion.gob.ec/wp-content/uploads/downloads/2018/09/CODIGO-ORGANICO-DE-ORGANIZACION-TERRITORIAL-COOTAD.pdf) | 2010 | 地方政府の種類・権限とPDOTを規定。参照PDFは2018改正収録版のため後続改正確認が必要。 | [Presidencia・Secretaría General de la Administración Pública y Gabinete（旧SNPを2025吸収。2026資料確認）](https://planificacion.presidencia.gob.ec/wp-content/uploads/2026/03/3-Acta-de-reunion-RDC-2025-SNP.pdf) |
| エクアドル | [Decreto Ejecutivo 95（機関統合）](https://planificacion.presidencia.gob.ec/wp-content/uploads/2026/03/3-Acta-de-reunion-RDC-2025-SNP.pdf) | 2025 | 旧SNPを大統領府へ吸収。2026年3月の政府文書で承継を確認。 | [Presidencia・Secretaría General de la Administración Pública y Gabinete（旧SNPを2025吸収。2026資料確認）](https://planificacion.presidencia.gob.ec/wp-content/uploads/2026/03/3-Acta-de-reunion-RDC-2025-SNP.pdf) |
| エルサルバドル | [Código Municipal（Decreto 274）](https://www.asamblea.gob.sv/leyes-y-decretos/decretos-por-anios/1986/0) | 1986 | 自治体の開発計画等の権限を規定。新44自治体の対象区域・適用計画は改編法と併読。 | [Ministerio de Desarrollo Local（MINDEL）／自治体。国土計画・予算は別所管](https://www.transparencia.gob.sv/perfil/371) |
| エルサルバドル | [Ley Especial para la Reestructuración Municipal](https://www.asamblea.gob.sv/node/12819) | 2023 | 44自治体・262地区への再編。統計の地区と計画責任を負う自治体の対応表が必要。 | [Ministerio de Desarrollo Local（MINDEL）／自治体。国土計画・予算は別所管](https://www.transparencia.gob.sv/perfil/371) |
| グアテマラ | [Código Municipal（Decreto 12-2002）](https://portal.segeplan.gob.gt/segeplan/wp-content/uploads/2022/07/107_PDM_OT_San_Pedro_Ayampuc.pdf) | 2002 | art.142（2010改正）は自治体の土地利用・総合開発計画の策定・実施を規定。PDM-OT手引きへ接続。 | [SEGEPLAN／地方政府の計画部局](https://portal.segeplan.gob.gt/segeplan/?page_id=6433) |
| グアテマラ | [Ley de los Consejos de Desarrollo Urbano y Rural（11-2002）](https://www.congreso.gob.gt/detalle_pdf/decretos/231) | 2002 | 国・地方・共同体をつなぐ参加型開発計画の評議会制度。2026改正の現行適用は追加照合。 | [SEGEPLAN／地方政府の計画部局](https://portal.segeplan.gob.gt/segeplan/?page_id=6433) |
| ハイチ | [Décret du 1er février 2006 sur la collectivité municipale](https://www.mict.gouv.ht/wp-content/uploads/2016/04/Decret-Portant-Organisation-et-Fonctionnement-de-la-Collectivite-Municipale.pdf) | 2006 | communeの組織・権限と地域開発の枠組み。現行施行状況・個別計画手続きを案件別に確認。 | [Ministère de la Planification et de la Coopération Externe（MPCE）／MICT・自治体](https://mpce.gouv.ht/) |
| ホンジュラス | [Normativa para la Formulación de PDM con enfoque de OT（Acuerdo 00132）](https://www.tsc.gob.hn/web/leyes/Normativa_formulacion_planes_desarrollo_municipal_2013.pdf) | 2013 | 自治体開発計画の作成方法を定める規範。Ley de Municipalidades等の現行統合条文は案件時に併読。 | [SGJD（自治体開発支援）／SEFIN-DGP（2026暫定計画調整）。旧SPEは廃止](https://www.sefin.gob.hn/wp-content/uploads/2026/05/Presentacion-Lineamientos-para-la-Ejecucion-y-Evaluacion-Presupuestaria_2026.pdf) |
| ホンジュラス | [PCM-004-2026（機関再編）](https://portalunico.iaip.gob.hn/498/) | 2026 | SPE廃止を政府透明性ポータルが明記。計画・予算接続はSEFIN-DGPの暫定権限を確認。 | [SGJD（自治体開発支援）／SEFIN-DGP（2026暫定計画調整）。旧SPEは廃止](https://www.sefin.gob.hn/wp-content/uploads/2026/05/Presentacion-Lineamientos-para-la-Ejecucion-y-Evaluacion-Presupuestaria_2026.pdf) |
| ホンジュラス | [Ley de Municipalidades（Decreto 134-90）](https://www.tsc.gob.hn/web/leyes/Ley_de_Municipalidades.pdf) | 1990 | 自治体の自治・権限・地方開発の基本法。PDM-OT規範と併読。 | [SGJD（自治体開発支援）／SEFIN-DGP（2026暫定計画調整）。旧SPEは廃止](https://www.sefin.gob.hn/wp-content/uploads/2026/05/Presentacion-Lineamientos-para-la-Ejecucion-y-Evaluacion-Presupuestaria_2026.pdf) |
| ホンジュラス | [Ley de Visión de País y Plan de Nación（286-2009）](https://tsc.gob.hn/biblioteca/index.php/leyes/128-ley-para-establecimiento-de-una-vision-de-pais-y-la-adpcion-de-un-plan-de-nacion-para-honduras) | 2009 | 国家の長期・中期計画の枠組み。2010公布、182-2010等の改正があり、現行運用は再確認。 | [SGJD（自治体開発支援）／SEFIN-DGP（2026暫定計画調整）。旧SPEは廃止](https://www.sefin.gob.hn/wp-content/uploads/2026/05/Presentacion-Lineamientos-para-la-Ejecucion-y-Evaluacion-Presupuestaria_2026.pdf) |
| メキシコ | [Ley de Planeación](https://www.diputados.gob.mx/LeyesBiblio/pdf_mov/Ley_de_Planeacion.pdf) | 1983 | 連邦の計画制度。自治体PDMの義務・期限は州計画法・自治体法を追加照合する。 | [SHCP（国家計画）／SEDATU（土地・都市）／州の計画機関・自治体](https://situ.sedatu.gob.mx/) |
| メキシコ | [Ley de Planeación del Estado de México y Municipios（州の例）](https://legislacion.edomex.gob.mx/sites/legislacion.edomex.gob.mx/files/files/pdf/ley/vig/leyvig087.pdf) | 2001 | 一州の地方計画制度。全国の自治体へ一律転用しない。対象州の法令へ差し替える。 | [SHCP（国家計画）／SEDATU（土地・都市）／州の計画機関・自治体](https://situ.sedatu.gob.mx/) |
| ニカラグア | [Ley 40 de Municipios](https://legislacion.asamblea.gob.ni/SILEG/Iniciativas.nsf/c9a0faf9d8c5e28f062572c70052cde2/7ebe8ba4e242fa7b062579eb0064e3b6/%24FILE/Ley%20No.%20792%20reforma%20Ley%20de%20municipios.pdf) | 1988 | 自治体の開発計画等。1997・2012等の改正を併読。掲載リンクはLey 792による改正。 | [大統領府・MHCP（計画予算投資）／自治体。地方支援の現行分掌は追加確認](https://www.hacienda.gob.ni/politica-institucional/) |
| パナマ | [Ley 37 de Descentralización](https://www.descentralizacion.gob.pa/page/ley-37-2009-descentralizacion) | 2009 | 地方分権と地区計画。Ley 66（2015）等の改正を含めてPED・参加・予算へ接続。 | [MEF（地域計画）／Autoridad Nacional de Descentralización（AND）／自治体](https://www.mef.gob.pa/2025/10/panama-presenta-el-presupuesto-mas-alto-de-su-historia-para-2026/) |
| パラグアイ | [Ley 3966 Orgánica Municipal](https://www.bacn.gov.py/leyes-paraguayas/969/ley-n-3966-organica-municipall) | 2010 | art.224–226。持続可能な開発計画PDSと都市・土地利用計画POUTを区別して策定。 | [Ministerio de Economía y Finanzas（MEF）・Viceministerio de Economía y Planificación](https://www.mef.gov.py/es/institucional/organigrama-y-funciones) |
| パラグアイ | [Ley 7158（MEF設置）](https://www.bacn.gov.py/leyes-paraguayas/11893/ley-n-7158-crea-el-ministerio-de-economia-) | 2023 | 財務省・公務機関・旧STPをMEFへ統合。古いSTP宛の規定と現在の所管を区別する。 | [Ministerio de Economía y Finanzas（MEF）・Viceministerio de Economía y Planificación](https://www.mef.gov.py/es/institucional/organigrama-y-funciones) |
| ペルー | [Ley 27972 Orgánica de Municipalidades](https://www.gob.pe/96430-el-plan-de-desarrollo-municipal-concertado) | 2003 | art.97等。地区・県自治体の協議型開発計画を接続。地域政府のPDRCは別の計画主体。 | [CEPLAN（PCMに属する国家計画機関）／地方政府](https://www.gob.pe/ceplan) |
| ペルー | [Decreto Legislativo 1088（SINAPLAN・CEPLAN）](https://www.gob.pe/institucion/ceplan/campa%C3%B1as/6243-conoce-las-normas-del-sinaplan) | 2008 | 国家戦略計画体系とCEPLANを規定。自治体のPDLCは自治体法・最新手引きと併読。 | [CEPLAN（PCMに属する国家計画機関）／地方政府](https://www.gob.pe/ceplan) |
| ドミニカ共和国 | [Ley 176-07 del Distrito Nacional y los Municipios](https://ayuntamientocomendador.gob.do/transparencia/wp-content/uploads/2026/01/PDM-Comendador-2025-2029.pdf) | 2007 | art.122等の自治体開発計画・参加。PMDと県・地域の基礎資料を別の制度・主体として扱う。 | [Ministerio de Hacienda y Economía（MHE、2025統合）／地方政府](https://www.presidencia.gob.do/noticias/presidente-abinader-promulga-ley-que-dispone-fusion-del-ministerio-de-hacienda-y-el) |
| ドミニカ共和国 | [Ley 498-06 de Planificación e Inversión Pública](https://www.hacienda.gob.do/wp-content/uploads/2023/12/PNPSP-Plan-Nacional-Plurianual-del-Sector-Pu%CC%81blico_compressed.pdf) | 2006 | 国家計画・公共投資体系。地方計画と上位計画・事業投資の整合確認に使う。 | [Ministerio de Hacienda y Economía（MHE、2025統合）／地方政府](https://www.presidencia.gob.do/noticias/presidente-abinader-promulga-ley-que-dispone-fusion-del-ministerio-de-hacienda-y-el) |
| ドミニカ共和国 | [Ley 1-12 Estrategia Nacional de Desarrollo 2030](https://transparencia.hacienda.gob.do/wp-content/uploads/2023/04/1-Ley-No-1-12-Ley-de-la-Estrategia-Nacional-de-Desarrollo-2030_.pdf) | 2012 | 長期国家開発戦略。地方の課題・目標・事業との対応根拠に使う。 | [Ministerio de Hacienda y Economía（MHE、2025統合）／地方政府](https://www.presidencia.gob.do/noticias/presidente-abinader-promulga-ley-que-dispone-fusion-del-ministerio-de-hacienda-y-el) |
| ドミニカ共和国 | [Ley 45-25（省庁統合）](https://www.presidencia.gob.do/noticias/presidente-abinader-promulga-ley-que-dispone-fusion-del-ministerio-de-hacienda-y-el) | 2025 | HaciendaとMEPyDを統合しMHEを設置。旧組織名と現在の提出・技術支援先を区別する。 | [Ministerio de Hacienda y Economía（MHE、2025統合）／地方政府](https://www.presidencia.gob.do/noticias/presidente-abinader-promulga-ley-que-dispone-fusion-del-ministerio-de-hacienda-y-el) |
| ウルグアイ | [Ley 19.272 Descentralización y Participación Ciudadana](https://www.impo.com.uy/bases/leyes/19272-2014) | 2014 | 自治体の機能と計画・参加の枠組み。2026のOPP実務でPQM・POA・管理合意を確認。 | [Oficina de Planeamiento y Presupuesto（OPP）／土地利用は部門政府・MVOT](https://www.opp.gub.uy/es/noticias/ciclo-de-apoyo-la-planificacion-figm-2026) |
| ウルグアイ | [Ley 18.308 Ordenamiento Territorial y Desarrollo Sostenible](https://www.impo.com.uy/bases/leyes/18308-2008) | 2008 | 土地利用計画の重要な権限はdepartamento側。Plan Localという名称だけでmunicipio所管と決めない。 | [Oficina de Planeamiento y Presupuesto（OPP）／土地利用は部門政府・MVOT](https://www.opp.gub.uy/es/noticias/ciclo-de-apoyo-la-planificacion-figm-2026) |
| ベネズエラ | [Ley Orgánica de Planificación Pública y Popular](https://mppp.gob.ve/marco-legal/leyes-y-reglamentos/) | 2010 | 国・地方・コミュニティの計画体系。所管省は2014改正法を掲載しており、2010本文のみで実装しない。 | [Ministerio del Poder Popular de Planificación（MPPP）／地方政府](https://mppp.gob.ve/) |
| ベネズエラ | [Ley Orgánica de Planificación Pública y Popular（改正）](https://mppp.gob.ve/marco-legal/leyes-y-reglamentos/) | 2014 | MPPPがG.O.E.6.148（2014-11-18）を掲載。案件時に条文・追加改正を照合。 | [Ministerio del Poder Popular de Planificación（MPPP）／地方政府](https://mppp.gob.ve/) |

制度の違いが自動化の分岐条件になる。州法別のアルゼンチン・メキシコ、条件付きPlano Diretorのブラジル、複数の地方政府階層でPDOTを作るエクアドル、自治体と部門政府の計画を分けるウルグアイを、同じ「municipal plan」に押し込まない。

機関の承継もデータ条件として扱う。ドミ共は2025年のMHE統合、パラグアイは2023年のMEF設置、エクアドルは2025年のSNP吸収、ホンジュラスは2026年のSPE廃止とSEFIN-DGPの暫定的な計画調整を確認した。古い手引きの機関名を現在の提出先へ無条件にコピーしない。[DOM_L4](https://www.presidencia.gob.do/noticias/presidente-abinader-promulga-ley-que-dispone-fusion-del-ministerio-de-hacienda-y-el)、[PRY_L2](https://www.bacn.gov.py/leyes-paraguayas/11893/ley-n-7158-crea-el-ministerio-de-economia-)、[ECU_L4](https://planificacion.presidencia.gob.ec/wp-content/uploads/2026/03/3-Acta-de-reunion-RDC-2025-SNP.pdf)、[HND_L2](https://portalunico.iaip.gob.hn/498/)、[HND_A](https://www.sefin.gob.hn/wp-content/uploads/2026/05/Presentacion-Lineamientos-para-la-Ejecucion-y-Evaluacion-Presupuestaria_2026.pdf)。

## 国別レポート

次の20章をこの一つのレポートに収録した。法令と国・地方の関係、計画粒度、統計項目、自動化案、未確認事項を国ごとに続けて読める。

[1. アルゼンチン](#country-ARG) / [2. ボリビア](#country-BOL) / [3. ブラジル](#country-BRA) / [4. チリ](#country-CHL) / [5. コロンビア](#country-COL) / [6. コスタリカ](#country-CRI) / [7. キューバ](#country-CUB) / [8. エクアドル](#country-ECU) / [9. エルサルバドル](#country-SLV) / [10. グアテマラ](#country-GTM) / [11. ハイチ](#country-HTI) / [12. ホンジュラス](#country-HND) / [13. メキシコ](#country-MEX) / [14. ニカラグア](#country-NIC) / [15. パナマ](#country-PAN) / [16. パラグアイ](#country-PRY) / [17. ペルー](#country-PER) / [18. ドミニカ共和国](#country-DOM) / [19. ウルグアイ](#country-URY) / [20. ベネズエラ](#country-VEN)

<a id="country-ARG"></a>

### 1. アルゼンチン（ARG）

**計画法体系。** 連邦制。国家憲法が自治体自治を保障し、具体的な自治体制度・計画権限は州憲法・州法・地方条例を通して定める。全国共通のPMD義務を、この調査から確定していない。

国家憲法（自治体自治の1994改正）→対象州の憲法・自治体／土地利用法→自治体の条例・地域計画。

| 主要法令・規範 | 制定／改正・発出年 | 概要・適用と留意点 |
| --- | --- | --- |
| [Constitución Nacional（art.123）](https://www.argentina.gob.ar/normativa/nacional/804/texto) | 1994 | 1994改正で自治体自治を規定。自治体計画の義務・種類は各州法・条例を追加確認する。 |

| 国と地方の関係 | 確認した制度と運用 |
| --- | --- |
| 国の所管・関係機関 | [州・地方政府の計画部局。全国一律の自治体計画所管は設定しない](https://www.argentina.gob.ar/normativa/nacional/804/texto) |
| 国の役割 | 国の計画・投資資料は背景と財源・広域整合の確認に使う。地方計画の具体的な所管は対象州・自治体の現行組織から確定する。 |
| 地方自治体の役割 | municipio、comuna等の制度と権限は州によって異なる。統計のdepartamentoを自動的に地方自治体へ読み替えない。 |
| 作成・協議・承認 | 作成部署・議会等の承認権限・協議手続きは州法と自治体条例を取得して確定する。中央省の承認を一律に追加しない。 |
| 期間・見直し | 全国一律の周期を設定しない。対象州・自治体の採用計画と現行条例を確認する。 |

関係の根拠：[ARG_L](https://www.argentina.gob.ar/normativa/nacional/804/texto)。制度枠組みの一次確認であり、個別自治体の最新承認・全改正の審査は含まない。

| 計画・統計の粒度 | この国での扱い |
| --- | --- |
| 法定主体に合わせる基本単位 | municipio／comuna等の地方政府（州法別） |
| 計画の種類 | 州法・地方条例に基づく地域／都市計画 |
| 調査・結果の段階 | 2022確報・REDATAM公開 |
| 調査年／詳細利用候補年 | 2022／2022 |
| 確認した統計の公表粒度 | departamento／partido／comuna（表別） |
| 自治体内部の補助粒度 | fracción／radio censal。地方政府界との対応を別確認 |
| 取得形式 | REDATAM・PDF・表ダウンロード |
| 利用上の条件 | departamentoと自治体は全国で同一ではない。機微項目の粒度制限あり。 |

**国勢調査の分野別項目。** 次の確認段階は原表の全件抽出・統合検証とは異なる。

| テーマ | 具体的な項目 | 確認段階・粒度 | 根拠 |
| --- | --- | --- | --- |
| 人口・世帯 | 性・年齢、人口、世帯 | 公表目録確認。departamento／partido／comuna（表別） | [ARG_R](https://redatam.indec.gob.ar/redarg/CENSOS/CPV2022/Docs/Redatam_introduccion.pdf) |
| 住宅 | 床・屋根、所有・賃貸、居住条件 | 公表目録確認。departamento／partido／comuna（表別） | [ARG_H](https://www.indec.gob.ar/ftp/cuadros/poblacion/censo2022_condiciones_habitacionales.pdf) |
| 水 | 飲用・調理用水源、屋内配管 | 公表目録確認。departamento／partido／comuna（表別） | [ARG_H](https://www.indec.gob.ar/ftp/cuadros/poblacion/censo2022_condiciones_habitacionales.pdf) |
| 衛生 | 水洗便所、下水道 | 公表目録確認。departamento／partido／comuna（表別） | [ARG_H](https://www.indec.gob.ar/ftp/cuadros/poblacion/censo2022_condiciones_habitacionales.pdf) |
| 家庭エネルギー | 調理燃料（ガス・電気等）。独立した電力普及率は未確認 | 公表目録確認。departamento／partido／comuna（表別） | [ARG_H](https://www.indec.gob.ar/ftp/cuadros/poblacion/censo2022_condiciones_habitacionales.pdf) |
| デジタル接続 | 住宅のネット、ネット対応携帯、PC・タブレット | 公表目録確認。departamento／partido／comuna（表別） | [ARG_H](https://www.indec.gob.ar/ftp/cuadros/poblacion/censo2022_condiciones_habitacionales.pdf) |
| 教育 | 就学、教育到達度 | 公表目録確認。departamento／partido／comuna（表別） | [ARG_R](https://redatam.indec.gob.ar/redarg/CENSOS/CPV2022/Docs/Redatam_introduccion.pdf) |
| 就業・生計 | 経済活動（詳細変数は導入資料で探索対象を確認） | 公表目録確認。departamento／partido／comuna（表別） | [ARG_R](https://redatam.indec.gob.ar/redarg/CENSOS/CPV2022/Docs/Redatam_introduccion.pdf) |
| 包摂・健康の一部 | 医療保障、先住民・アフロ系、ジェンダー関連項目 | 公表目録確認。departamento／partido／comuna（表別） | [ARG_R](https://redatam.indec.gob.ar/redarg/CENSOS/CPV2022/Docs/Redatam_introduccion.pdf) |
| 移住 | 出生地・移住 | 公表目録確認。departamento／partido／comuna（表別） | [ARG_R](https://redatam.indec.gob.ar/redarg/CENSOS/CPV2022/Docs/Redatam_introduccion.pdf) |

**DDPT業務の自動化への適用案。** 州を選び、その州の法体系・自治体台帳とINDECの地域コードを対応付けてから、2022住宅・人口表を地域診断へ組み込む。地方政府区域とradioの関係は別工程で検証する。

**残る確認。** 全州の計画法・条例、地方政府界と統計界の対応、自治体計画の本文・承認資料は未取得。

<a id="country-BOL"></a>

### 2. ボリビア（BOL）

**計画法体系。** SPIEにより国と地方の計画を接続する。地方の自治を前提に、部門・自治体のPTDIと先住民自治の計画類型を分ける。

国家の長期・中期計画→SPIE／Ley 777→departamento・municipioのPTDI、TIOCのPGTC等→制度計画・年次実施／投資。

| 主要法令・規範 | 制定／改正・発出年 | 概要・適用と留意点 |
| --- | --- | --- |
| [Ley 777 del SPIE](https://sea.gob.bo/digesto/CompendioII/A/2_L_777.pdf) | 2016 | 統合計画体系。PTDIの地方対象とTIOCの計画類型を区別する（art.17等）。 |

| 国と地方の関係 | 確認した制度と運用 |
| --- | --- |
| 国の所管・関係機関 | [Ministerio de Planificación del Desarrollo y Medio Ambiente（MPDyMA）](https://www.gob.bo/entidades/ministerio-de-planificacion-del-desarrollo-y-medio-ambiente) |
| 国の役割 | MPDyMAがSPIEの制度所管を担い、国家計画と地方計画の整合を扱う。省名は2025年以降の再編を反映する。 |
| 地方自治体の役割 | 自治地方政府が対象区域の発展と土地・生活圏を扱う。TIOCは単なる統計地区ではなく、通常のmunicipioとは異なる計画主体になり得る。 |
| 作成・協議・承認 | 作成・法定承認・国家計画との整合確認を区別する。対象政府の現行手引きと承認行為を取得し、国のガイド掲載だけで地方計画を承認済みとしない。 |
| 期間・見直し | 国家の中期計画周期と地方PTDIの対象期間を文書ごとに記録する。前期2021–2025を新規案件へ固定しない。 |

関係の根拠：[BOL_L](https://sea.gob.bo/digesto/CompendioII/A/2_L_777.pdf)、[BOL_A](https://www.gob.bo/entidades/ministerio-de-planificacion-del-desarrollo-y-medio-ambiente)。制度枠組みの一次確認であり、個別自治体の最新承認・全改正の審査は含まない。

| 計画・統計の粒度 | この国での扱い |
| --- | --- |
| 法定主体に合わせる基本単位 | municipio・departamento／TIOC |
| 計画の種類 | PTDI／先住民自治はPGTC等 |
| 調査・結果の段階 | 2024 municipio/TIOC別表公開 |
| 調査年／詳細利用候補年 | 2024／2024 |
| 確認した統計の公表粒度 | municipio／TIOC |
| 自治体内部の補助粒度 | 小地域のテーマ別数値公開は追加確認 |
| 取得形式 | ZIP集計表・REDATAM・地理ポータル |
| 利用上の条件 | TIOCと通常のmunicipioの制度・地域対応を分ける。NBIは所得貧困と別。 |

**国勢調査の分野別項目。** 次の確認段階は原表の全件抽出・統合検証とは異なる。

| テーマ | 具体的な項目 | 確認段階・粒度 | 根拠 |
| --- | --- | --- | --- |
| 人口・世帯 | 性・年齢、世帯構成、人口動態 | 公表目録確認。municipio／TIOC | [BOL_C](https://cpv2024.ine.gob.bo/index.php/tabulados-sobre-la-tematica-pobreza/) |
| 住宅 | 材料、保有形態、室数 | 公表目録確認。municipio／TIOC | [BOL_C](https://cpv2024.ine.gob.bo/index.php/tabulados-sobre-la-tematica-pobreza/) |
| 水 | 水源 | 公表目録確認。municipio／TIOC | [BOL_C](https://cpv2024.ine.gob.bo/index.php/tabulados-sobre-la-tematica-pobreza/) |
| 衛生 | 便所、排水 | 公表目録確認。municipio／TIOC | [BOL_C](https://cpv2024.ine.gob.bo/index.php/tabulados-sobre-la-tematica-pobreza/) |
| 家庭エネルギー | 電源、調理燃料 | 公表目録確認。municipio／TIOC | [BOL_C](https://cpv2024.ine.gob.bo/index.php/tabulados-sobre-la-tematica-pobreza/) |
| デジタル接続 | 世帯ICT機器・接続関連項目（個別の接続定義要照合） | 公表目録確認。municipio／TIOC | [BOL_C](https://cpv2024.ine.gob.bo/index.php/tabulados-sobre-la-tematica-pobreza/) |
| 教育 | 識字、就学、学歴、平均教育年数 | 公表目録確認。municipio／TIOC | [BOL_C](https://cpv2024.ine.gob.bo/index.php/tabulados-sobre-la-tematica-pobreza/) |
| 就業・生計 | 活動、職業、産業、就業地への移動 | 公表目録確認。municipio／TIOC | [BOL_C](https://cpv2024.ine.gob.bo/index.php/tabulados-sobre-la-tematica-pobreza/) |
| 包摂・健康の一部 | 機能上の困難5歳以上、医療、言語、民族、NBI | 公表目録確認。municipio／TIOC | [BOL_C](https://cpv2024.ine.gob.bo/index.php/tabulados-sobre-la-tematica-pobreza/) |
| 移住 | 国内移住、国外移住 | 公表目録確認。municipio／TIOC | [BOL_C](https://cpv2024.ine.gob.bo/index.php/tabulados-sobre-la-tematica-pobreza/) |

**DDPT業務の自動化への適用案。** 2024のmunicipio/TIOC別表を基礎に、PTDIの診断要求へ指標を対応付ける。NBI、基礎サービス、就業・教育を優先し、地方投資・環境・計画本文を追加収集する。

**残る確認。** 最新期の地方手引き・承認済みPTDI、TIOCの個別適用、全対象の境界対応は国別導入時に確認。

<a id="country-BRA"></a>

### 3. ブラジル（BRA）

**計画法体系。** 連邦・州・連邦区・自治体の役割を分ける。都市政策の自治体計画Plano Diretorと、PPA・予算の計画を別の制度・成果物として扱う。

連邦憲法（1988）→都市政策のEstatuto da Cidade（2001）→自治体のPlano Diretor・土地利用規則。財政側はPPA・LDO・LOAの系統。

| 主要法令・規範 | 制定／改正・発出年 | 概要・適用と留意点 |
| --- | --- | --- |
| [Lei 10.257 Estatuto da Cidade](https://www.planalto.gov.br/ccivil_03/leis/leis_2001/l10257.htm) | 2001 | art.40–41。Plano Diretorは自治体域全体を対象とし、人口2万人超その他の条件に該当する都市で義務。全自治体一律ではない。 |
| [Constituição Federal（計画・都市政策）](https://www4.planalto.gov.br/legislacao/legis-federal/constituicao) | 1988 | 国・州・自治体の関係、PPA等の財政計画、自治体の都市政策の憲法上の枠組み。 |

| 国と地方の関係 | 確認した制度と運用 |
| --- | --- |
| 国の所管・関係機関 | [Ministério das Cidades（都市計画）、Ministério do Planejamento e Orçamento（国家予算計画）](https://www.gov.br/cidades/pt-br) |
| 国の役割 | 連邦は都市政策の一般的枠組み・支援施策等を担う。都市計画はMinistério das Cidades、国家予算計画はMPOという業務の違いを保持する。 |
| 地方自治体の役割 | 自治体が都市政策を担い、Plano Diretorは都市中心部だけでなく自治体域全体を対象にする。人口2万人超、都市圏等の法定条件で策定義務が分岐する。 |
| 作成・協議・承認 | Plano Diretorは自治体の法律として承認される。住民参加や公開の要求を、単なるデータ収集の完了で代替しない。 |
| 期間・見直し | Plano Diretorの改定規則とPPA・年次予算の周期は異なる。art.40の見直し規定と現行自治体法を案件で照合する。 |

関係の根拠：[BRA_L](https://www.planalto.gov.br/ccivil_03/leis/leis_2001/l10257.htm)、[BRA_L2](https://www4.planalto.gov.br/legislacao/legis-federal/constituicao)。制度枠組みの一次確認であり、個別自治体の最新承認・全改正の審査は含まない。

| 計画・統計の粒度 | この国での扱い |
| --- | --- |
| 法定主体に合わせる基本単位 | município（計画別に適用要件） |
| 計画の種類 | Plano Diretor／財政計画は別制度 |
| 調査・結果の段階 | 2022全数・標本結果を別公開 |
| 調査年／詳細利用候補年 | 2022／2022 |
| 確認した統計の公表粒度 | município。標本と全数の公開粒度を区別 |
| 自治体内部の補助粒度 | 全数の一部はsetor censitário・bairro等 |
| 取得形式 | SIDRA・CSV・XLS・地理データ |
| 利用上の条件 | ネットは標本項目。全数のセクター細分性をネット等の標本値に転用しない。 |

**国勢調査の分野別項目。** 次の確認段階は原表の全件抽出・統合検証とは異なる。

| テーマ | 具体的な項目 | 確認段階・粒度 | 根拠 |
| --- | --- | --- | --- |
| 人口・世帯 | 性・年齢、人種、世帯 | 公表目録確認。município。標本と全数の公開粒度を区別 | [BRA_C](https://www.ibge.gov.br/estatisticas/sociais/trabalho/22827-censo-demografico-2022.html?edicao=41852&t=resultados) |
| 住宅 | 所有・賃貸、室数、過密（標本を含む） | 公表目録確認。município（標本）。セクター提供は主張しない | [BRA_S](https://www.ibge.gov.br/estatisticas/sociais/populacao/22827-censo-demografico-2022.html?edicao=42157&t=resultados) |
| 水 | 水源、配管 | 公表目録確認。município。標本と全数の公開粒度を区別 | [BRA_H](https://sidra.ibge.gov.br/pesquisa/censo-demografico/demografico-2022/universo-caracteristicas-dos-domicilios) |
| 衛生 | 便所、下水・排水 | 公表目録確認。município。標本と全数の公開粒度を区別 | [BRA_H](https://sidra.ibge.gov.br/pesquisa/censo-demografico/demografico-2022/universo-caracteristicas-dos-domicilios) |
| 家庭エネルギー | 未確認：2022一般住宅の独立した電力・調理燃料表 | 未確認。当該項目の公表粒度未確認 | [BRA_C](https://www.ibge.gov.br/estatisticas/sociais/trabalho/22827-censo-demografico-2022.html?edicao=41852&t=resultados) |
| デジタル接続 | 世帯のインターネット接続（標本） | 公表目録確認。município（標本）。セクター提供は主張しない | [BRA_S](https://www.ibge.gov.br/estatisticas/sociais/populacao/22827-censo-demografico-2022.html?edicao=42157&t=resultados) |
| 教育 | 識字（全数）。学歴等は標本別に確認 | 公表目録確認。município。標本と全数の公開粒度を区別 | [BRA_C](https://www.ibge.gov.br/estatisticas/sociais/trabalho/22827-censo-demografico-2022.html?edicao=41852&t=resultados) |
| 就業・生計 | 就業・所得（標本） | 公表目録確認。município。標本と全数の公開粒度を区別 | [BRA_E](https://www.ibge.gov.br/estatisticas/Sociais/populacao/22827-censo-demografico-2022.html?edicao=44663) |
| 包摂・健康の一部 | 先住民・quilombola。障害関連は標本表の条件確認 | 公表目録確認。município。標本と全数の公開粒度を区別 | [BRA_C](https://www.ibge.gov.br/estatisticas/sociais/trabalho/22827-censo-demografico-2022.html?edicao=41852&t=resultados) |
| 移住 | 未確認：この台帳では移住の詳細表を未点検 | 未確認。当該項目の公表粒度未確認 | [BRA_C](https://www.ibge.gov.br/estatisticas/sociais/trabalho/22827-censo-demografico-2022.html?edicao=41852&t=resultados) |

**DDPT業務の自動化への適用案。** 法定適用条件を自治体台帳へ付け、IBGEの全数・標本を分けて取り込む。水衛生等の全数指標とネット・所得等の標本指標を、認められる地域粒度で比較する。

**残る確認。** 自治体ごとの義務該当条件・最新Plano Diretor・PPA・条例、標本指標の精度と細地域提供条件は未網羅。

<a id="country-CHL"></a>

### 4. チリ（CHL）

**計画法体系。** 自治体の総合的な開発計画PLADECOを軸とし、都市の用途・規制を扱うPlan Regulador Comunalや年度予算は別の計画・手続きとして接続する。

自治体基本法18.695（1988）と統合条文DFL 1（2006）→comunaのPLADECO→個別事業・年度予算。都市規制計画は別系統。

| 主要法令・規範 | 制定／改正・発出年 | 概要・適用と留意点 |
| --- | --- | --- |
| [Ley 18.695 Orgánica Constitucional de Municipalidades](https://www.bcn.cl/leychile/navegar?idNorma=251693) | 1988 | PLADECOを自治体の基本的計画手段とする。現行参照はDFL 1（2006）統合条文art.6–7等。 |

| 国と地方の関係 | 確認した制度と運用 |
| --- | --- |
| 国の所管・関係機関 | [SUBDERE／各municipalidad（PLADECO）。都市規制は別の所管・計画](https://www.subdere.gob.cl/organigrama-subdere/organigrama.html) |
| 国の役割 | SUBDEREが自治体計画の方法面を支援する。国や地域の施策との整合と、自治体の意思決定を区別する。 |
| 地方自治体の役割 | comunaを区域とするmunicipalidadが地域の総合的発展を扱う。統計上のmanzana・entidadは自治体内部の診断に利用する。 |
| 作成・協議・承認 | 市長とconcejoの法定権限を確認してPLADECOの承認・改定資料へ結合する。本文の公開だけで議会の承認を推定しない。 |
| 期間・見直し | PLADECOの最低期間・見直しと自治体の実際の採用年を現行条文・計画本文で確定する。単一の世界共通周期は設定しない。 |

関係の根拠：[CHL_L](https://www.bcn.cl/leychile/navegar?idNorma=251693)、[CHL_A](https://www.subdere.gob.cl/organigrama-subdere/organigrama.html)。制度枠組みの一次確認であり、個別自治体の最新承認・全改正の審査は含まない。

| 計画・統計の粒度 | この国での扱い |
| --- | --- |
| 法定主体に合わせる基本単位 | comuna（municipalidad） |
| 計画の種類 | PLADECO |
| 調査・結果の段階 | 2024結果・小地域データ公開 |
| 調査年／詳細利用候補年 | 2024／2024 |
| 確認した統計の公表粒度 | comuna |
| 自治体内部の補助粒度 | manzana／entidad。項目別の秘匿条件確認 |
| 取得形式 | 結果ビューア・REDATAM・microdata・地理データ |
| 利用上の条件 | 固定・モバイル・衛星ネットの複数回答を単純合計しない。 |

**国勢調査の分野別項目。** 次の確認段階は原表の全件抽出・統合検証とは異なる。

| テーマ | 具体的な項目 | 確認段階・粒度 | 根拠 |
| --- | --- | --- | --- |
| 人口・世帯 | 人口、性・年齢、世帯 | 公表目録確認。comuna | [CHL_C](https://censo2024.ine.gob.cl/resultados/) |
| 住宅 | 所有・賃貸、過密 | 公表目録確認。comuna | [CHL_H](https://censo2024.ine.gob.cl/censo-2024-el-611-de-los-hogares-residen-en-una-vivienda-propia-y-el-262-en-una-vivienda-arrendada/) |
| 水 | 水源・供給 | 公表目録確認。comuna | [CHL_H](https://censo2024.ine.gob.cl/censo-2024-el-611-de-los-hogares-residen-en-una-vivienda-propia-y-el-262-en-una-vivienda-arrendada/) |
| 衛生 | 下水、浄化槽等 | 公表目録確認。comuna | [CHL_H](https://censo2024.ine.gob.cl/censo-2024-el-611-de-los-hogares-residen-en-una-vivienda-propia-y-el-262-en-una-vivienda-arrendada/) |
| 家庭エネルギー | 電源、調理・暖房燃料 | 公表目録確認。comuna | [CHL_H](https://censo2024.ine.gob.cl/censo-2024-el-611-de-los-hogares-residen-en-una-vivienda-propia-y-el-262-en-una-vivienda-arrendada/) |
| デジタル接続 | 世帯ネット（固定・モバイル・衛星） | 公表目録確認。comuna | [CHL_H](https://censo2024.ine.gob.cl/censo-2024-el-611-de-los-hogares-residen-en-una-vivienda-propia-y-el-262-en-una-vivienda-arrendada/) |
| 教育 | 教育・就学 | 設問の公式説明確認。当該項目の公表粒度未点検 | [CHL_Q](https://censo2024.ine.gob.cl/ine-habilito-punto-censo-en-el-instituto-teleton-de-santiago/) |
| 就業・生計 | 就業・労働参加 | 設問の公式説明確認。当該項目の公表粒度未点検 | [CHL_Q](https://censo2024.ine.gob.cl/ine-habilito-punto-censo-en-el-instituto-teleton-de-santiago/) |
| 包摂・健康の一部 | 日常生活の機能上の困難 | 設問の公式説明確認。当該項目の公表粒度未点検 | [CHL_Q](https://censo2024.ine.gob.cl/ine-habilito-punto-censo-en-el-instituto-teleton-de-santiago/) |
| 移住 | 未確認：この台帳では移住の詳細表を未点検 | 未確認。当該項目の公表粒度未確認 | [CHL_C](https://censo2024.ine.gob.cl/resultados/) |

**DDPT業務の自動化への適用案。** 2024のcomuna人口・住居・サービス表で診断基礎を作り、現行PLADECOと予算、都市規制資料の対象・期間を区別して取り込む。ネットの複数回答を重複集計しない。

**残る確認。** 全comunaのPLADECO本文・最新承認日、教育・就業等の細目別公開粒度、現行条文の全改正確認は残件。

<a id="country-COL"></a>

### 5. コロンビア（COL）

**計画法体系。** 国家と地方の開発計画をLey 152で接続する。地方は権限・資源・責任の範囲で計画上の自治を持ち、国家計画の政策・戦略との整合も求められる。

Ley 152（1994）→国家PND／地方PDT→複数年投資・実施・評価。POT等の土地利用計画は別の法令系統。

| 主要法令・規範 | 制定／改正・発出年 | 概要・適用と留意点 |
| --- | --- | --- |
| [Ley 152 Orgánica del Plan de Desarrollo](https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=327) | 1994 | art.32–40等が地方計画の策定・承認・評価を規定。開発計画と土地利用計画を別管理。 |

| 国と地方の関係 | 確認した制度と運用 |
| --- | --- |
| 国の所管・関係機関 | [Departamento Nacional de Planeación（DNP）／地方計画部局](https://portalterritorial.dnp.gov.co/) |
| 国の役割 | DNPが国家計画と地方への技術支援・共通ツールを提供する。SisPT等の公開ツールは利用条件・内容を確認して資料探索に使う。 |
| 地方自治体の役割 | municipio・distrito・departamentoは異なる地方計画主体。人口センサスの細区分を計画主体として追加しない。 |
| 作成・協議・承認 | 地方の執行機関が策定し、議会等の法定手続きと地方計画評議会の参加を伴う。作成案、協議意見、採択行為を別資料として管理する。 |
| 期間・見直し | 地方の任期に対応したPDT期間と国家PND期間、投資・予算年度を分ける。期の違う計画を同じ統計年で隠さない。 |

関係の根拠：[COL_L](https://www.funcionpublica.gov.co/eva/gestornormativo/norma.php?i=327)、[COL_A](https://portalterritorial.dnp.gov.co/)。制度枠組みの一次確認であり、個別自治体の最新承認・全改正の審査は含まない。

| 計画・統計の粒度 | この国での扱い |
| --- | --- |
| 法定主体に合わせる基本単位 | municipio／distrito・departamento |
| 計画の種類 | Plan de Desarrollo Territorial（PDT）／POTは別 |
| 調査・結果の段階 | CNPV2018・地域集計と変数辞書公開 |
| 調査年／詳細利用候補年 | 2018／2018 |
| 確認した統計の公表粒度 | municipio |
| 自治体内部の補助粒度 | manzana・農村sección等は選定変数 |
| 取得形式 | DANE地域ビューア・地理サービス・ANDA・REDATAM |
| 利用上の条件 | ネットは住宅の固定／モバイル接続。就業状態から産業別生産を推測しない。 |

**国勢調査の分野別項目。** 次の確認段階は原表の全件抽出・統合検証とは異なる。

| テーマ | 具体的な項目 | 確認段階・粒度 | 根拠 |
| --- | --- | --- | --- |
| 人口・世帯 | 性、5歳階級、世帯内続柄 | 変数辞書確認。municipio（個別変数の公開・秘匿条件は抽出時に確認） | [COL_P](https://microdatos.dane.gov.co/index.php/catalog/643/data-dictionary/F11?file_name=PERSONAS) |
| 住宅 | 種類・壁・床、居住状態 | 変数辞書確認。municipio（個別変数の公開・秘匿条件は抽出時に確認） | [COL_H](https://microdatos.dane.gov.co/index.php/catalog/643/data-dictionary/F8?file_name=VIVENDAS) |
| 水 | acueductoサービス | 変数辞書確認。municipio（個別変数の公開・秘匿条件は抽出時に確認） | [COL_H](https://microdatos.dane.gov.co/index.php/catalog/643/data-dictionary/F8?file_name=VIVENDAS) |
| 衛生 | 下水道、便所 | 変数辞書確認。municipio（個別変数の公開・秘匿条件は抽出時に確認） | [COL_H](https://microdatos.dane.gov.co/index.php/catalog/643/data-dictionary/F8?file_name=VIVENDAS) |
| 家庭エネルギー | 電気、都市ガス | 変数辞書確認。municipio（個別変数の公開・秘匿条件は抽出時に確認） | [COL_H](https://microdatos.dane.gov.co/index.php/catalog/643/data-dictionary/F8?file_name=VIVENDAS) |
| デジタル接続 | 住宅の固定／モバイルネット | 変数辞書確認。municipio（個別変数の公開・秘匿条件は抽出時に確認） | [COL_H](https://microdatos.dane.gov.co/index.php/catalog/643/data-dictionary/F8?file_name=VIVENDAS) |
| 教育 | 識字、就学、学歴 | 変数辞書確認。municipio（個別変数の公開・秘匿条件は抽出時に確認） | [COL_P](https://microdatos.dane.gov.co/index.php/catalog/643/data-dictionary/F11?file_name=PERSONAS) |
| 就業・生計 | 前週の活動状態。産業・職業詳細の収録は未確認 | 変数辞書確認。municipio（個別変数の公開・秘匿条件は抽出時に確認） | [COL_P](https://microdatos.dane.gov.co/index.php/catalog/643/data-dictionary/F11?file_name=PERSONAS) |
| 包摂・健康の一部 | 機能上の困難、民族・言語、最近の健康問題・受診 | 変数辞書確認。municipio（個別変数の公開・秘匿条件は抽出時に確認） | [COL_P](https://microdatos.dane.gov.co/index.php/catalog/643/data-dictionary/F11?file_name=PERSONAS) |
| 移住 | 出生地、1年前・5年前の居住地 | 変数辞書確認。municipio（個別変数の公開・秘匿条件は抽出時に確認） | [COL_P](https://microdatos.dane.gov.co/index.php/catalog/643/data-dictionary/F11?file_name=PERSONAS) |

**DDPT業務の自動化への適用案。** DANE2018のmunicipio指標をPDT診断の基礎にし、DNPの地方ツールと各自治体のPDT・予算・投資を接続する。住宅ネットと個人の利用を同一指標にしない。

**残る確認。** 各地方の最新PDTと承認行為、POTの適用種別・版、国勢調査以外の最新分野統計の全件取得は残件。

<a id="country-CRI"></a>

### 6. コスタリカ（CRI）

**計画法体系。** 国家計画法5525と自治体法7794の役割を分ける。MIDEPLANの国家・地域計画と、cantónの自治体開発計画・年次計画を接続する。

Ley 5525（1974）の国家計画体系＋Código Municipal 7794（1998）→cantónの開発計画／PAO→予算。都市規制は別計画。

| 主要法令・規範 | 制定／改正・発出年 | 概要・適用と留意点 |
| --- | --- | --- |
| [Ley 7794 Código Municipal](https://www.pgrweb.go.cr/DOCS/NORMAS/1/VIGENTE/L/1990-1999/1995-1999/1998/9D05/17C506.HTML) | 1998 | 自治体議会の開発計画承認等。art.13の現行号記は改正で変わるため統合条文で確認。 |
| [Ley 5525 de Planificación Nacional](https://www.mideplan.go.cr/index.php/marco-legal-inversion-publica) | 1974 | 国家計画体系とMIDEPLAN。自治体の計画権限・都市規制とは区別する。 |

| 国と地方の関係 | 確認した制度と運用 |
| --- | --- |
| 国の所管・関係機関 | [MIDEPLAN（国家計画）／自治体。地方支援機関・都市規制は業務別](https://www.mideplan.go.cr/documentos_leyes?field_ano_value=&order=title&page=0&sort=asc&title=) |
| 国の役割 | MIDEPLANは国家計画・公共投資等の制度所管。自治体への支援や都市規制に関わる別機関は、対象業務に応じて追加確認する。 |
| 地方自治体の役割 | 基本の自治体域はcantón。distritoの統計があっても、すべての地区を独立した同権限の自治体とは扱わない。 |
| 作成・協議・承認 | 自治体議会の計画承認権限と自治体執行側の作成・提出を分ける。MIDEPLANの資料掲載を自治体計画の承認と読み替えない。 |
| 期間・見直し | 自治体の開発計画・年次実施計画・規制計画の実際の期間を別々に取得する。 |

関係の根拠：[CRI_L](https://www.pgrweb.go.cr/DOCS/NORMAS/1/VIGENTE/L/1990-1999/1995-1999/1998/9D05/17C506.HTML)、[CRI_L2](https://www.mideplan.go.cr/index.php/marco-legal-inversion-publica)。制度枠組みの一次確認であり、個別自治体の最新承認・全改正の審査は含まない。

| 計画・統計の粒度 | この国での扱い |
| --- | --- |
| 法定主体に合わせる基本単位 | cantón（municipalidad） |
| 計画の種類 | Plan de Desarrollo Municipal／PAO等 |
| 調査・結果の段階 | 不完全収集を補正した2022公式推計 |
| 調査年／詳細利用候補年 | 2022／2022 |
| 確認した統計の公表粒度 | provincia／cantón／distritoの推計指標 |
| 自治体内部の補助粒度 | distrito。ただし指標別の品質注記を確認 |
| 取得形式 | 推計報告PDF・指標ビューア・地理ビューア |
| 利用上の条件 | 44社会住宅指標は補正推計。実査の全数値として扱わず、地区別の品質を確認。 |

**国勢調査の分野別項目。** 次の確認段階は原表の全件抽出・統合検証とは異なる。

| テーマ | 具体的な項目 | 確認段階・粒度 | 根拠 |
| --- | --- | --- | --- |
| 人口・世帯 | 人口性比・年齢依存、世帯類型 | 方法・項目一覧確認。provincia／cantón／distritoの推計指標 | [CRI_C](https://admin.inec.cr/sites/default/files/2024-11/meSocialMetodologiaEstimacionesSocialesVivienda2022.pdf) |
| 住宅 | 住宅状態、所有・賃貸、居住者数 | 方法・項目一覧確認。provincia／cantón／distritoの推計指標 | [CRI_C](https://admin.inec.cr/sites/default/files/2024-11/meSocialMetodologiaEstimacionesSocialesVivienda2022.pdf) |
| 水 | 屋内配管＋水道由来 | 方法・項目一覧確認。provincia／cantón／distritoの推計指標 | [CRI_C](https://admin.inec.cr/sites/default/files/2024-11/meSocialMetodologiaEstimacionesSocialesVivienda2022.pdf) |
| 衛生 | 下水道または浄化槽 | 方法・項目一覧確認。provincia／cantón／distritoの推計指標 | [CRI_C](https://admin.inec.cr/sites/default/files/2024-11/meSocialMetodologiaEstimacionesSocialesVivienda2022.pdf) |
| 家庭エネルギー | 電気 | 方法・項目一覧確認。provincia／cantón／distritoの推計指標 | [CRI_C](https://admin.inec.cr/sites/default/files/2024-11/meSocialMetodologiaEstimacionesSocialesVivienda2022.pdf) |
| デジタル接続 | 住宅ネット、PC、携帯 | 方法・項目一覧確認。provincia／cantón／distritoの推計指標 | [CRI_C](https://admin.inec.cr/sites/default/files/2024-11/meSocialMetodologiaEstimacionesSocialesVivienda2022.pdf) |
| 教育 | 識字、教育年数、就学、学歴、学年遅滞 | 方法・項目一覧確認。provincia／cantón／distritoの推計指標 | [CRI_C](https://admin.inec.cr/sites/default/files/2024-11/meSocialMetodologiaEstimacionesSocialesVivienda2022.pdf) |
| 就業・生計 | 就業・失業・非労働力、3産業部門 | 方法・項目一覧確認。provincia／cantón／distritoの推計指標 | [CRI_C](https://admin.inec.cr/sites/default/files/2024-11/meSocialMetodologiaEstimacionesSocialesVivienda2022.pdf) |
| 包摂・健康の一部 | 医療保険加入。障害指標は44指標内で未確認 | 方法・項目一覧確認。provincia／cantón／distritoの推計指標 | [CRI_C](https://admin.inec.cr/sites/default/files/2024-11/meSocialMetodologiaEstimacionesSocialesVivienda2022.pdf) |
| 移住 | 外国人比率 | 方法・項目一覧確認。provincia／cantón／distritoの推計指標 | [CRI_C](https://admin.inec.cr/sites/default/files/2024-11/meSocialMetodologiaEstimacionesSocialesVivienda2022.pdf) |

**DDPT業務の自動化への適用案。** 2022の44社会住宅推計をcantón単位で整理し、distrito別の品質注記を残す。法定計画に必要な水道・医療・教育の供給面を各機関の資料で補う。

**残る確認。** 各推計の地区品質、自治体計画の最新様式・期間、独立した地区制度の例外は個別確認。

<a id="country-CUB"></a>

### 7. キューバ（CUB）

**計画法体系。** Decreto 33/2021は自治体と省の開発戦略を区別し、国家の政策・投資、土地利用、経済計画、予算との整合を求める。

Decreto 33（2021）→自治体・省の開発戦略→地方開発事業。土地・都市計画、経済計画、予算を併読。

| 主要法令・規範 | 制定／改正・発出年 | 概要・適用と留意点 |
| --- | --- | --- |
| [Decreto 33 Para la Gestión Estratégica del Desarrollo Territorial](https://www.gacetaoficial.gob.cu/sites/default/files/goc-2021-o40.pdf) | 2021 | art.6–8。自治体行政評議会が戦略を作成・実施・評価・更新し、自治体人民権力議会へ承認のため提出。省の計画とも接続。 |

| 国と地方の関係 | 確認した制度と運用 |
| --- | --- |
| 国の所管・関係機関 | [Ministerio de Economía y Planificación（制度上の関係機関）／地方政府。現行組織図の追認は残件](https://www.gacetaoficial.gob.cu/es/gaceta-oficial-no-40-ordinaria-de-2021) |
| 国の役割 | 制度上MEP等が関係し、国の政策・投資と地方の利益を調整する。現在の個別提出部署・機関再編の追認は残件。 |
| 地方自治体の役割 | 自治体行政評議会が自治体戦略を作成・実施・評価・更新する。省の戦略は知事が担当し、自治体の戦略と調整する。 |
| 作成・協議・承認 | 自治体戦略は自治体人民権力議会へ承認のため提出。省戦略は省評議会へ提出する（art.7）。 |
| 期間・見直し | 戦略の実際の期間と更新条件、経済計画・予算の期間を本文から取得する。法令発出年2021を計画対象年としない。 |

関係の根拠：[CUB_L_TEXT](https://www.gacetaoficial.gob.cu/sites/default/files/goc-2021-o40.pdf)。制度枠組みの一次確認であり、個別自治体の最新承認・全改正の審査は含まない。

| 計画・統計の粒度 | この国での扱い |
| --- | --- |
| 法定主体に合わせる基本単位 | municipio（provinciaとの接続） |
| 計画の種類 | Estrategia de Desarrollo Municipal |
| 調査・結果の段階 | 確認できた詳細調査は2012。UNSDは2026を予定表記 |
| 調査年／詳細利用候補年 | 2012／2012 |
| 確認した統計の公表粒度 | municipioの公表データ取得は未確認 |
| 自治体内部の補助粒度 | 調査票の地域識別≠公開データの最小粒度 |
| 取得形式 | 調査票PDF（CEPAL保管）・追加資料探索 |
| 利用上の条件 | 2012調査票の設問を確認。現行ONEIの地方別データ取得・2026結果は未確認。 |

**国勢調査の分野別項目。** 次の確認段階は原表の全件抽出・統合検証とは異なる。

| テーマ | 具体的な項目 | 確認段階・粒度 | 根拠 |
| --- | --- | --- | --- |
| 人口・世帯 | 性・年齢、続柄 | 調査票確認。公表粒度未確認（票ではmunicipioを識別） | [CUB_C](https://celade.cepal.org/censosinfo/Boletas/CU_BDef_2012.pdf) |
| 住宅 | 種類・材料・状態・室数・保有形態 | 調査票確認。公表粒度未確認（票ではmunicipioを識別） | [CUB_C](https://celade.cepal.org/censosinfo/Boletas/CU_BDef_2012.pdf) |
| 水 | 水源、供給頻度、貯水 | 調査票確認。公表粒度未確認（票ではmunicipioを識別） | [CUB_C](https://celade.cepal.org/censosinfo/Boletas/CU_BDef_2012.pdf) |
| 衛生 | 便所、排水、共同利用 | 調査票確認。公表粒度未確認（票ではmunicipioを識別） | [CUB_C](https://celade.cepal.org/censosinfo/Boletas/CU_BDef_2012.pdf) |
| 家庭エネルギー | 照明電源、調理燃料 | 調査票確認。公表粒度未確認（票ではmunicipioを識別） | [CUB_C](https://celade.cepal.org/censosinfo/Boletas/CU_BDef_2012.pdf) |
| デジタル接続 | PC・電話保有。確認した住宅設備票にネット接続設問なし。電話やPC保有をインターネット普及率へ置換しない | 調査票確認。公表粒度未確認（票ではmunicipioを識別） | [CUB_C](https://celade.cepal.org/censosinfo/Boletas/CU_BDef_2012.pdf) |
| 教育 | 識字・就学・学歴・資格 | 調査票確認。公表粒度未確認（票ではmunicipioを識別） | [CUB_C](https://celade.cepal.org/censosinfo/Boletas/CU_BDef_2012.pdf) |
| 就業・生計 | 前週活動、職業・産業、就業地 | 調査票確認。公表粒度未確認（票ではmunicipioを識別） | [CUB_C](https://celade.cepal.org/censosinfo/Boletas/CU_BDef_2012.pdf) |
| 包摂・健康の一部 | 障害・疾患型の設問、肌の色。機能困難型との比較注意 | 調査票確認。公表粒度未確認（票ではmunicipioを識別） | [CUB_C](https://celade.cepal.org/censosinfo/Boletas/CU_BDef_2012.pdf) |
| 移住 | 出生地、従前居住地・居住期間 | 調査票確認。公表粒度未確認（票ではmunicipioを識別） | [CUB_C](https://celade.cepal.org/censosinfo/Boletas/CU_BDef_2012.pdf) |

**DDPT業務の自動化への適用案。** まず2012の調査票と実際に提供される自治体表を対応付け、取得できた表だけで診断を作る。地方戦略・予算・事業資料を分散収集し、2026調査の結果段階を別監視する設計にする。

**残る確認。** ONEIの自治体別詳細データ取得、2026の結果段階、現行手引きと地方戦略本文・承認資料は未確認。

<a id="country-ECU"></a>

### 8. エクアドル（ECU）

**計画法体系。** COOTADとCOPFPが自治分権と計画・財政を接続する。州・郡・農村教区のGADは、それぞれ権限を持つ地方計画主体として扱う。

COOTAD（2010）＋COPFP（2010）→国家計画・領土戦略と各GADのPDOT→年度計画・予算・投資。

| 主要法令・規範 | 制定／改正・発出年 | 概要・適用と留意点 |
| --- | --- | --- |
| [Código Orgánico de Planificación y Finanzas Públicas（COPFP）](https://www.planificacion.gob.ec/wp-content/uploads/2021/10/Codigo-Org%C3%A1nico-de-Planificaci%C3%B3n-y-Finanzas-P%C3%BAblicas.pdf) | 2010 | art.41以下のPDOT。GADの開発・土地利用計画と財政・国家計画の関係を規定。 |
| [PDOT作成・更新ガイド（Acuerdo SNP-SNP-2023-0049-A）](https://www.planificacion.gob.ec/wp-content/uploads/2023/06/PDOT-ACUERDO-Nro.-SNP-SNP-2023-0049-A.pdf) | 2023 | 法令ではなく運用手引き。州・郡・農村教区等の対象を確認。案件時に後続版を確認する。 |
| [COOTAD](https://www.planificacion.gob.ec/wp-content/uploads/downloads/2018/09/CODIGO-ORGANICO-DE-ORGANIZACION-TERRITORIAL-COOTAD.pdf) | 2010 | 地方政府の種類・権限とPDOTを規定。参照PDFは2018改正収録版のため後続改正確認が必要。 |
| [Decreto Ejecutivo 95（機関統合）](https://planificacion.presidencia.gob.ec/wp-content/uploads/2026/03/3-Acta-de-reunion-RDC-2025-SNP.pdf) | 2025 | 旧SNPを大統領府へ吸収。2026年3月の政府文書で承継を確認。 |

| 国と地方の関係 | 確認した制度と運用 |
| --- | --- |
| 国の所管・関係機関 | [Presidencia・Secretaría General de la Administración Pública y Gabinete（旧SNPを2025吸収。2026資料確認）](https://planificacion.presidencia.gob.ec/wp-content/uploads/2026/03/3-Acta-de-reunion-RDC-2025-SNP.pdf) |
| 国の役割 | 国家計画の制度・手引きと地方PDOTの整合を扱う。旧SNPは2025年に大統領府へ吸収され、2026の政府文書で承継を確認した。 |
| 地方自治体の役割 | provincia、cantón、parroquia ruralの各GADを区別する。都市parroquiaという地理名称だけで同種の自治政府を作らない。 |
| 作成・協議・承認 | 各GADの執行側・立法側・参加機構の手続きに沿って策定・承認を区別する。上位計画との整合と、中央が地方計画を代行することは別。 |
| 期間・見直し | PDOTの採用期間と現行更新ガイドを案件時に確認する。2023ガイドを現行最新版と無条件に扱わない。 |

関係の根拠：[ECU_L](https://www.planificacion.gob.ec/wp-content/uploads/2021/10/Codigo-Org%C3%A1nico-de-Planificaci%C3%B3n-y-Finanzas-P%C3%BAblicas.pdf)、[ECU_L3](https://www.planificacion.gob.ec/wp-content/uploads/downloads/2018/09/CODIGO-ORGANICO-DE-ORGANIZACION-TERRITORIAL-COOTAD.pdf)、[ECU_L4](https://planificacion.presidencia.gob.ec/wp-content/uploads/2026/03/3-Acta-de-reunion-RDC-2025-SNP.pdf)。制度枠組みの一次確認であり、個別自治体の最新承認・全改正の審査は含まない。

| 計画・統計の粒度 | この国での扱い |
| --- | --- |
| 法定主体に合わせる基本単位 | provincia・cantón・parroquia ruralのGAD |
| 計画の種類 | PDOT |
| 調査・結果の段階 | 2022結果表・テーマ別データ公開 |
| 調査年／詳細利用候補年 | 2022／2022 |
| 確認した統計の公表粒度 | cantón／parroquia（項目別） |
| 自治体内部の補助粒度 | セクター等の数値公表は追加確認 |
| 取得形式 | XLS・CSV・地域診断ページ |
| 利用上の条件 | 農村parroquiaは自治政府。都市parroquiaを同じ法定計画主体と扱わない。 |

**国勢調査の分野別項目。** 次の確認段階は原表の全件抽出・統合検証とは異なる。

| テーマ | 具体的な項目 | 確認段階・粒度 | 根拠 |
| --- | --- | --- | --- |
| 人口・世帯 | 人口構造、世帯構成 | 公表目録確認。テーマ別カタログ確認。水・衛生・電気はparroquia公表例あり | [ECU_C](https://www.censoecuador.gob.ec/resultados-censo/) |
| 住宅 | 住宅一般、保有・居住条件 | 公表目録確認。テーマ別カタログ確認。水・衛生・電気はparroquia公表例あり | [ECU_C](https://www.censoecuador.gob.ec/resultados-censo/) |
| 水 | 水源・供給主体 | 公表目録確認。テーマ別カタログ確認。水・衛生・電気はparroquia公表例あり | [ECU_C](https://www.censoecuador.gob.ec/resultados-censo/) |
| 衛生 | 下水・衛生設備 | 公表目録確認。テーマ別カタログ確認。水・衛生・電気はparroquia公表例あり | [ECU_C](https://www.censoecuador.gob.ec/resultados-censo/) |
| 家庭エネルギー | 電気、調理用エネルギー | 公表目録確認。テーマ別カタログ確認。水・衛生・電気はparroquia公表例あり | [ECU_C](https://www.censoecuador.gob.ec/resultados-censo/) |
| デジタル接続 | 世帯ICT | 公表目録確認。テーマ別カタログ確認。水・衛生・電気はparroquia公表例あり | [ECU_C](https://www.censoecuador.gob.ec/resultados-censo/) |
| 教育 | 識字、就学、学歴 | 公表目録確認。テーマ別カタログ確認。水・衛生・電気はparroquia公表例あり | [ECU_C](https://www.censoecuador.gob.ec/resultados-censo/) |
| 就業・生計 | 経済活動 | 公表目録確認。テーマ別カタログ確認。水・衛生・電気はparroquia公表例あり | [ECU_C](https://www.censoecuador.gob.ec/resultados-censo/) |
| 包摂・健康の一部 | 機能上の困難、民族、ジェンダー、NBI | 公表目録確認。テーマ別カタログ確認。水・衛生・電気はparroquia公表例あり | [ECU_C](https://www.censoecuador.gob.ec/resultados-censo/) |
| 移住 | 国内外移住 | 公表目録確認。テーマ別カタログ確認。水・衛生・電気はparroquia公表例あり | [ECU_C](https://www.censoecuador.gob.ec/resultados-censo/) |

**DDPT業務の自動化への適用案。** GAD類型と国勢調査コードを対応付け、水・衛生・電気等のparroquia表を採用する。PDOTの法定章に指標を対応させ、土地利用・環境・財政・事業資料を補う。

**残る確認。** 2025再編後の提出部署・新ガイド、各GADの現行PDOT・承認行為、テーマ別のparroquia提供条件は追加確認。

<a id="country-SLV"></a>

### 9. エルサルバドル（SLV）

**計画法体系。** 自治体法の計画権限と、2023再編法に基づく2024以降の44自治体を組み合わせる。旧自治体に対応する262地区は現在の同等の計画責任主体ではない。

Código Municipal（1986）＋自治体再編法（2023）→44自治体の計画・予算。土地利用等の個別法・条例は追加照合。

| 主要法令・規範 | 制定／改正・発出年 | 概要・適用と留意点 |
| --- | --- | --- |
| [Código Municipal（Decreto 274）](https://www.asamblea.gob.sv/leyes-y-decretos/decretos-por-anios/1986/0) | 1986 | 自治体の開発計画等の権限を規定。新44自治体の対象区域・適用計画は改編法と併読。 |
| [Ley Especial para la Reestructuración Municipal](https://www.asamblea.gob.sv/node/12819) | 2023 | 44自治体・262地区への再編。統計の地区と計画責任を負う自治体の対応表が必要。 |

| 国と地方の関係 | 確認した制度と運用 |
| --- | --- |
| 国の所管・関係機関 | [Ministerio de Desarrollo Local（MINDEL）／自治体。国土計画・予算は別所管](https://www.transparencia.gob.sv/perfil/371) |
| 国の役割 | MINDELが地方開発の関係機関。国土・都市・予算に関わる他機関と自治体の責任分担は計画種類別に整理する。 |
| 地方自治体の役割 | 新municipioを基本の計画単位にする。262 distritoは住民サービス・自治体内部診断の単位として保持する。 |
| 作成・協議・承認 | 現行自治体法と新自治体の条例・議会資料から作成・協議・承認を確認する。旧地区ごとの計画を新自治体の現行計画とみなさない。 |
| 期間・見直し | 再編前後の計画対象域・期間と継承関係を優先して確認する。全44自治体の現行周期は今回未確定。 |

関係の根拠：[SLV_L](https://www.asamblea.gob.sv/leyes-y-decretos/decretos-por-anios/1986/0)、[SLV_L2](https://www.asamblea.gob.sv/node/12819)、[SLV_A](https://www.transparencia.gob.sv/perfil/371)。制度枠組みの一次確認であり、個別自治体の最新承認・全改正の審査は含まない。

| 計画・統計の粒度 | この国での扱い |
| --- | --- |
| 法定主体に合わせる基本単位 | 44 municipios（262 distritosは下位区分） |
| 計画の種類 | 自治体開発計画／土地利用計画を類型別確認 |
| 調査・結果の段階 | 2024結果報告・地理ポータル公開 |
| 調査年／詳細利用候補年 | 2024／2024 |
| 確認した統計の公表粒度 | municipio・distrito（項目別）。住宅表はdepartamento例 |
| 自治体内部の補助粒度 | distritoを自治体内部診断に利用 |
| 取得形式 | 報告PDF・地理ポータル・表 |
| 利用上の条件 | 2023再編法による2024からの44自治体と旧262自治体を混同しない。 |

**国勢調査の分野別項目。** 次の確認段階は原表の全件抽出・統合検証とは異なる。

| テーマ | 具体的な項目 | 確認段階・粒度 | 根拠 |
| --- | --- | --- | --- |
| 人口・世帯 | 人口、性・年齢、出生・死亡 | 報告の章・表目録確認。項目別。人口・教育・活動・ICTはdistrito章あり。全項目の地区表は未点検 | [SLV_C](https://censo2024.bcr.gob.sv/wp-content/uploads/tablas-geoportal/2025/Informe%20_VII_Censo_de_Poblacion_y_VI_de_Vivienda_marzo_2025.pdf) |
| 住宅 | 住宅種類・材料・居住状態 | 報告の章・表目録確認。項目別。人口・教育・活動・ICTはdistrito章あり。全項目の地区表は未点検 | [SLV_C](https://censo2024.bcr.gob.sv/wp-content/uploads/tablas-geoportal/2025/Informe%20_VII_Censo_de_Poblacion_y_VI_de_Vivienda_marzo_2025.pdf) |
| 水 | 給水 | 報告の章・表目録確認。項目別。人口・教育・活動・ICTはdistrito章あり。全項目の地区表は未点検 | [SLV_C](https://censo2024.bcr.gob.sv/wp-content/uploads/tablas-geoportal/2025/Informe%20_VII_Censo_de_Poblacion_y_VI_de_Vivienda_marzo_2025.pdf) |
| 衛生 | 衛生設備 | 報告の章・表目録確認。項目別。人口・教育・活動・ICTはdistrito章あり。全項目の地区表は未点検 | [SLV_C](https://censo2024.bcr.gob.sv/wp-content/uploads/tablas-geoportal/2025/Informe%20_VII_Censo_de_Poblacion_y_VI_de_Vivienda_marzo_2025.pdf) |
| 家庭エネルギー | 電気 | 報告の章・表目録確認。項目別。人口・教育・活動・ICTはdistrito章あり。全項目の地区表は未点検 | [SLV_C](https://censo2024.bcr.gob.sv/wp-content/uploads/tablas-geoportal/2025/Informe%20_VII_Censo_de_Poblacion_y_VI_de_Vivienda_marzo_2025.pdf) |
| デジタル接続 | 個人のネット・ICT利用 | 報告の章・表目録確認。項目別。人口・教育・活動・ICTはdistrito章あり。全項目の地区表は未点検 | [SLV_C](https://censo2024.bcr.gob.sv/wp-content/uploads/tablas-geoportal/2025/Informe%20_VII_Censo_de_Poblacion_y_VI_de_Vivienda_marzo_2025.pdf) |
| 教育 | 識字・学歴 | 報告の章・表目録確認。項目別。人口・教育・活動・ICTはdistrito章あり。全項目の地区表は未点検 | [SLV_C](https://censo2024.bcr.gob.sv/wp-content/uploads/tablas-geoportal/2025/Informe%20_VII_Censo_de_Poblacion_y_VI_de_Vivienda_marzo_2025.pdf) |
| 就業・生計 | 経済活動、就業状態・時間・部門 | 報告の章・表目録確認。項目別。人口・教育・活動・ICTはdistrito章あり。全項目の地区表は未点検 | [SLV_C](https://censo2024.bcr.gob.sv/wp-content/uploads/tablas-geoportal/2025/Informe%20_VII_Censo_de_Poblacion_y_VI_de_Vivienda_marzo_2025.pdf) |
| 包摂・健康の一部 | 機能上の困難、先住民・アフロ系 | 報告の章・表目録確認。項目別。人口・教育・活動・ICTはdistrito章あり。全項目の地区表は未点検 | [SLV_C](https://censo2024.bcr.gob.sv/wp-content/uploads/tablas-geoportal/2025/Informe%20_VII_Censo_de_Poblacion_y_VI_de_Vivienda_marzo_2025.pdf) |
| 移住 | 国内移住、国外移住 | 報告の章・表目録確認。項目別。人口・教育・活動・ICTはdistrito章あり。全項目の地区表は未点検 | [SLV_C](https://censo2024.bcr.gob.sv/wp-content/uploads/tablas-geoportal/2025/Informe%20_VII_Censo_de_Poblacion_y_VI_de_Vivienda_marzo_2025.pdf) |

**DDPT業務の自動化への適用案。** 2024の地区別統計を新自治体コードと対応付け、必要なら検証済みの分子分母で集計する。地区のネット利用・教育・人口を自治体内部診断に使い、旧計画の区域と継承を明示する。

**残る確認。** 全44自治体の最新計画、旧新コード・境界の公式対応、住宅サービスの全地区表、個別土地利用法の現行適用は残件。

<a id="country-GTM"></a>

### 10. グアテマラ（GTM）

**計画法体系。** 自治体法による土地利用・総合開発計画と、開発評議会制度による参加型計画を接続する。SEGEPLANのPDM-OT手引きはその実務上の入口になる。

Código Municipal 12-2002（art.142、2010改正）＋Consejos de Desarrollo法11-2002→PDM-OT→複数年・年次実施計画／事業。

| 主要法令・規範 | 制定／改正・発出年 | 概要・適用と留意点 |
| --- | --- | --- |
| [Código Municipal（Decreto 12-2002）](https://portal.segeplan.gob.gt/segeplan/wp-content/uploads/2022/07/107_PDM_OT_San_Pedro_Ayampuc.pdf) | 2002 | art.142（2010改正）は自治体の土地利用・総合開発計画の策定・実施を規定。PDM-OT手引きへ接続。 |
| [Ley de los Consejos de Desarrollo Urbano y Rural（11-2002）](https://www.congreso.gob.gt/detalle_pdf/decretos/231) | 2002 | 国・地方・共同体をつなぐ参加型開発計画の評議会制度。2026改正の現行適用は追加照合。 |

| 国と地方の関係 | 確認した制度と運用 |
| --- | --- |
| 国の所管・関係機関 | [SEGEPLAN／地方政府の計画部局](https://portal.segeplan.gob.gt/segeplan/?page_id=6433) |
| 国の役割 | SEGEPLANが技術的な計画・プログラミングを支援し、国・地方の計画をつなぐ資料・手引きを提供する。 |
| 地方自治体の役割 | 自治体が自らの区域の計画を策定・実施する。COMUDE・COCODE等の参加と自治体政府の決定は異なる役割として記録する。 |
| 作成・協議・承認 | 自治体の採択文書と参加機構の記録を別に収集する。SEGEPLANサイトでのPDM-OT掲載と自治体の正式採択の根拠を区別する。 |
| 期間・見直し | PDM-OTの長期対象期間、複数年計画、年次POAを別管理。公開された各計画の期間を採用し、周期を一律に固定しない。 |

関係の根拠：[GTM_L](https://portal.segeplan.gob.gt/segeplan/wp-content/uploads/2022/07/107_PDM_OT_San_Pedro_Ayampuc.pdf)、[GTM_L2](https://www.congreso.gob.gt/detalle_pdf/decretos/231)、[GTM_A](https://portal.segeplan.gob.gt/segeplan/?page_id=6433)。制度枠組みの一次確認であり、個別自治体の最新承認・全改正の審査は含まない。

| 計画・統計の粒度 | この国での扱い |
| --- | --- |
| 法定主体に合わせる基本単位 | municipio |
| 計画の種類 | PDM-OT |
| 調査・結果の段階 | 2018地域集計・地域内小地区資料公開 |
| 調査年／詳細利用候補年 | 2018／2018 |
| 確認した統計の公表粒度 | municipio |
| 自治体内部の補助粒度 | lugar pobladoの選定指標 |
| 取得形式 | Excel・CSV・結果エクスプローラ |
| 利用上の条件 | 個人ネット利用7歳以上と世帯のネット設備を分ける。 |

**国勢調査の分野別項目。** 次の確認段階は原表の全件抽出・統合検証とは異なる。

| テーマ | 具体的な項目 | 確認段階・粒度 | 根拠 |
| --- | --- | --- | --- |
| 人口・世帯 | 性・5歳階級、続柄、都市農村 | 公表目録確認。municipio | [GTM_C](https://censo2018.ine.gob.gt/explorador) |
| 住宅 | 居住条件、世帯設備 | 公表目録確認。municipio | [GTM_C](https://censo2018.ine.gob.gt/explorador) |
| 水 | 水源・給水 | 公表目録確認。municipio | [GTM_C](https://censo2018.ine.gob.gt/explorador) |
| 衛生 | 便所・排水 | 公表目録確認。municipio | [GTM_C](https://censo2018.ine.gob.gt/explorador) |
| 家庭エネルギー | 照明、調理燃料 | 公表目録確認。municipio | [GTM_C](https://censo2018.ine.gob.gt/explorador) |
| デジタル接続 | 個人の携帯・PC・ネット7歳以上／世帯ネット | 公表目録確認。municipio | [GTM_C](https://censo2018.ine.gob.gt/explorador) |
| 教育 | 識字・就学・学歴、不就学理由 | 公表目録確認。municipio | [GTM_C](https://censo2018.ine.gob.gt/explorador) |
| 就業・生計 | 未確認：この台帳では就業詳細表を未点検 | 未確認。当該項目の公表粒度未確認 | [GTM_C](https://censo2018.ine.gob.gt/explorador) |
| 包摂・健康の一部 | 機能上の困難4歳以上、pueblos等 | 公表目録確認。municipio | [GTM_C](https://censo2018.ine.gob.gt/explorador) |
| 移住 | 出生地、2013年の居住地 | 公表目録確認。municipio | [GTM_C](https://censo2018.ine.gob.gt/explorador) |

**DDPT業務の自動化への適用案。** 2018municipio表、lugar poblado選定表、SEGEPLANのPDM-OT資料集を取得経路の核とする。法定診断の不足を教育・保健・投資資料から補い、参加記録と事業案を接続する。

**残る確認。** 2026改正を含む評議会法の現行条文、各自治体の最新計画・実施計画、就業等の詳細表は追加確認。

<a id="country-HTI"></a>

### 11. ハイチ（HTI）

**計画法体系。** 2006年の地方分権・自治体関係政令を制度の起点とする。法令上の地方計画制度と、現時点で実際に機能している行政・協議・承認の体制を分けて調べる。

地方分権の枠組み政令／自治体政令（2006）→communeの開発計画PDC→投資・予算。国家側の計画・公共投資資料と接続。

| 主要法令・規範 | 制定／改正・発出年 | 概要・適用と留意点 |
| --- | --- | --- |
| [Décret du 1er février 2006 sur la collectivité municipale](https://www.mict.gouv.ht/wp-content/uploads/2016/04/Decret-Portant-Organisation-et-Fonctionnement-de-la-Collectivite-Municipale.pdf) | 2006 | communeの組織・権限と地域開発の枠組み。現行施行状況・個別計画手続きを案件別に確認。 |

| 国と地方の関係 | 確認した制度と運用 |
| --- | --- |
| 国の所管・関係機関 | [Ministère de la Planification et de la Coopération Externe（MPCE）／MICT・自治体](https://mpce.gouv.ht/) |
| 国の役割 | MPCEが国家の計画・公共投資・対外協力、MICTが地方制度に関係する。省庁資料で示された制度上の役割と現地運用を照合する。 |
| 地方自治体の役割 | 基本対象はcommune。section communale等の下位区分・共同体の関係を確認する。細地域を同じ権限の独立自治体へ置き換えない。 |
| 作成・協議・承認 | 法令に規定された機関と現在の実際の権限主体を個別確認する。計画の存在、現在の有効性、承認状態を公開情報の不足から推定しない。 |
| 期間・見直し | PDCと公共投資の実際の期間を原資料から取得する。全国共通の現行周期は今回未確定。 |

関係の根拠：[HTI_L](https://www.mict.gouv.ht/wp-content/uploads/2016/04/Decret-Portant-Organisation-et-Fonctionnement-de-la-Collectivite-Municipale.pdf)、[HTI_A](https://mpce.gouv.ht/)。制度枠組みの一次確認であり、個別自治体の最新承認・全改正の審査は含まない。

| 計画・統計の粒度 | この国での扱い |
| --- | --- |
| 法定主体に合わせる基本単位 | commune |
| 計画の種類 | Plan de Développement Communal（PDC） |
| 調査・結果の段階 | RGPH2003が公式サイトで確認できる詳細結果 |
| 調査年／詳細利用候補年 | 2003／2003 |
| 確認した統計の公表粒度 | communeは人口・就業の一部。住宅設備は全国表を確認 |
| 自治体内部の補助粒度 | section communale／SDEとの対応・公開範囲は未確認 |
| 取得形式 | IHSI HTML表目録・PDF |
| 利用上の条件 | 古い基準年。近年の人口推計・人道データを2003調査値へ混ぜない。 |

**国勢調査の分野別項目。** 次の確認段階は原表の全件抽出・統合検証とは異なる。

| テーマ | 具体的な項目 | 確認段階・粒度 | 根拠 |
| --- | --- | --- | --- |
| 人口・世帯 | 性・年齢別人口 | 公表目録確認。主に全国表目録。人口・就業のcommune表は個別確認 | [HTI_C](https://ihsi.gouv.ht/recensement/autres_resultat_rgph_2003) |
| 住宅 | 建物材料、室数、保有形態 | 公表目録確認。主に全国表目録。人口・就業のcommune表は個別確認 | [HTI_C](https://ihsi.gouv.ht/recensement/autres_resultat_rgph_2003) |
| 水 | 配水接続、水源・利用 | 公表目録確認。主に全国表目録。人口・就業のcommune表は個別確認 | [HTI_C](https://ihsi.gouv.ht/recensement/autres_resultat_rgph_2003) |
| 衛生 | 便所種類 | 公表目録確認。主に全国表目録。人口・就業のcommune表は個別確認 | [HTI_C](https://ihsi.gouv.ht/recensement/autres_resultat_rgph_2003) |
| 家庭エネルギー | 照明、調理燃料 | 公表目録確認。主に全国表目録。人口・就業のcommune表は個別確認 | [HTI_C](https://ihsi.gouv.ht/recensement/autres_resultat_rgph_2003) |
| デジタル接続 | 電話・PC等。ネット接続は今回の表目録で未確認 | 公表目録確認。主に全国表目録。人口・就業のcommune表は個別確認 | [HTI_C](https://ihsi.gouv.ht/recensement/autres_resultat_rgph_2003) |
| 教育 | 就学・学歴・識字 | 公表目録確認。主に全国表目録。人口・就業のcommune表は個別確認 | [HTI_C](https://ihsi.gouv.ht/recensement/autres_resultat_rgph_2003) |
| 就業・生計 | 就業、産業・職業・地位 | 公表目録確認。主に全国表目録。人口・就業のcommune表は個別確認 | [HTI_C](https://ihsi.gouv.ht/recensement/autres_resultat_rgph_2003) |
| 包摂・健康の一部 | 未確認：この台帳では障害・医療保障表を未点検 | 未確認。当該項目の公表粒度未確認 | [HTI_C](https://ihsi.gouv.ht/recensement/autres_resultat_rgph_2003) |
| 移住 | 未確認：この台帳では移住の詳細表を未点検 | 未確認。当該項目の公表粒度未確認 | [HTI_C](https://ihsi.gouv.ht/recensement/autres_resultat_rgph_2003) |

**DDPT業務の自動化への適用案。** 2003のcommune人口・就業等を歴史的基礎として明示し、近年推計・行政・人道資料を出典別の別系列で追加する。まず自治体単位で利用可能な基礎資料と不足一覧を完成させる。

**残る確認。** 現在の地方統治・承認実務、commune別住宅サービスの入手、新しい人口資料との整合、各PDC本文は未網羅。

<a id="country-HND"></a>

### 12. ホンジュラス（HND）

**計画法体系。** 自治体法、国家のVisión de País／Plan de Nación、PDM-OT作成規範を区別して接続する。2026年の中央機関再編を必ず反映する。

Ley de Municipalidades 134-90（1990）＋国家計画のDecreto 286-2009（2010公布）→2013 PDM-OT作成規範→自治体計画・年次予算。

| 主要法令・規範 | 制定／改正・発出年 | 概要・適用と留意点 |
| --- | --- | --- |
| [Normativa para la Formulación de PDM con enfoque de OT（Acuerdo 00132）](https://www.tsc.gob.hn/web/leyes/Normativa_formulacion_planes_desarrollo_municipal_2013.pdf) | 2013 | 自治体開発計画の作成方法を定める規範。Ley de Municipalidades等の現行統合条文は案件時に併読。 |
| [PCM-004-2026（機関再編）](https://portalunico.iaip.gob.hn/498/) | 2026 | SPE廃止を政府透明性ポータルが明記。計画・予算接続はSEFIN-DGPの暫定権限を確認。 |
| [Ley de Municipalidades（Decreto 134-90）](https://www.tsc.gob.hn/web/leyes/Ley_de_Municipalidades.pdf) | 1990 | 自治体の自治・権限・地方開発の基本法。PDM-OT規範と併読。 |
| [Ley de Visión de País y Plan de Nación（286-2009）](https://tsc.gob.hn/biblioteca/index.php/leyes/128-ley-para-establecimiento-de-una-vision-de-pais-y-la-adpcion-de-un-plan-de-nacion-para-honduras) | 2009 | 国家の長期・中期計画の枠組み。2010公布、182-2010等の改正があり、現行運用は再確認。 |

| 国と地方の関係 | 確認した制度と運用 |
| --- | --- |
| 国の所管・関係機関 | [SGJD（自治体開発支援）／SEFIN-DGP（2026暫定計画調整）。旧SPEは廃止](https://www.sefin.gob.hn/wp-content/uploads/2026/05/Presentacion-Lineamientos-para-la-Ejecucion-y-Evaluacion-Presupuestaria_2026.pdf) |
| 国の役割 | 自治体支援側のSGJDと、2026に暫定計画調整を担うSEFIN-DGPを区別する。旧SPEを現行所管として自動登録しない。 |
| 地方自治体の役割 | 自治体法に基づくmunicipioの自治と地方開発計画を対象とする。298自治体の統計・計画本文・参加・投資の各台帳を地域コードで接続する。 |
| 作成・協議・承認 | 自治体の法定承認と国の方法面の支援、予算との整合確認を別に扱う。自治体の決議・採択根拠は各原本から取得する。 |
| 期間・見直し | 旧国家計画の対象期間、現政府の計画、各PDM-OTの期間を別に保持する。旧長期計画の名称だけで現行運用を確定しない。 |

関係の根拠：[HND_L](https://www.tsc.gob.hn/web/leyes/Normativa_formulacion_planes_desarrollo_municipal_2013.pdf)、[HND_L2](https://portalunico.iaip.gob.hn/498/)、[HND_L3](https://www.tsc.gob.hn/web/leyes/Ley_de_Municipalidades.pdf)、[HND_L4](https://tsc.gob.hn/biblioteca/index.php/leyes/128-ley-para-establecimiento-de-una-vision-de-pais-y-la-adpcion-de-un-plan-de-nacion-para-honduras)、[HND_A](https://www.sefin.gob.hn/wp-content/uploads/2026/05/Presentacion-Lineamientos-para-la-Ejecucion-y-Evaluacion-Presupuestaria_2026.pdf)。制度枠組みの一次確認であり、個別自治体の最新承認・全改正の審査は含まない。

| 計画・統計の粒度 | この国での扱い |
| --- | --- |
| 法定主体に合わせる基本単位 | municipio |
| 計画の種類 | PDM-OT |
| 調査・結果の段階 | 2013詳細結果。2026は準備・実施関連情報で結果未確認 |
| 調査年／詳細利用候補年 | 2013／2013 |
| 確認した統計の公表粒度 | municipio（298自治体別報告の目録） |
| 自治体内部の補助粒度 | aldea／caseríoは票で識別。公開数値の粒度は別確認 |
| 取得形式 | 自治体別PDF・調査票PDF |
| 利用上の条件 | 2026という事業名や準備記事を公表済み国勢調査結果と扱わない。 |

**国勢調査の分野別項目。** 次の確認段階は原表の全件抽出・統合検証とは異なる。

| テーマ | 具体的な項目 | 確認段階・粒度 | 根拠 |
| --- | --- | --- | --- |
| 人口・世帯 | 性・年齢、続柄 | 調査票確認。municipioの報告目録は確認。項目別表・下位粒度は追加確認 | [HND_Q](https://celade.cepal.org/censosinfo/Boletas/HD_Bdef_2013.pdf) |
| 住宅 | 種類・材料、室数、保有形態 | 調査票確認。municipioの報告目録は確認。項目別表・下位粒度は追加確認 | [HND_Q](https://celade.cepal.org/censosinfo/Boletas/HD_Bdef_2013.pdf) |
| 水 | 水源、配管位置 | 調査票確認。municipioの報告目録は確認。項目別表・下位粒度は追加確認 | [HND_Q](https://celade.cepal.org/censosinfo/Boletas/HD_Bdef_2013.pdf) |
| 衛生 | 便所・排水、共同利用 | 調査票確認。municipioの報告目録は確認。項目別表・下位粒度は追加確認 | [HND_Q](https://celade.cepal.org/censosinfo/Boletas/HD_Bdef_2013.pdf) |
| 家庭エネルギー | 電源、調理燃料 | 調査票確認。municipioの報告目録は確認。項目別表・下位粒度は追加確認 | [HND_Q](https://celade.cepal.org/censosinfo/Boletas/HD_Bdef_2013.pdf) |
| デジタル接続 | 世帯のInternetサービス、PC・電話 | 調査票確認。municipioの報告目録は確認。項目別表・下位粒度は追加確認 | [HND_Q](https://celade.cepal.org/censosinfo/Boletas/HD_Bdef_2013.pdf) |
| 教育 | 識字、就学、学歴3歳以上 | 調査票確認。municipioの報告目録は確認。項目別表・下位粒度は追加確認 | [HND_Q](https://celade.cepal.org/censosinfo/Boletas/HD_Bdef_2013.pdf) |
| 就業・生計 | 未確認：この台帳では就業の設問・表を未点検 | 未確認。当該項目の公表粒度未確認 | [HND_Q](https://celade.cepal.org/censosinfo/Boletas/HD_Bdef_2013.pdf) |
| 包摂・健康の一部 | 恒常的な障害、民族、出生登録 | 調査票確認。municipioの報告目録は確認。項目別表・下位粒度は追加確認 | [HND_Q](https://celade.cepal.org/censosinfo/Boletas/HD_Bdef_2013.pdf) |
| 移住 | 出生地、入国年、世帯員の国外移住 | 調査票確認。municipioの報告目録は確認。項目別表・下位粒度は追加確認 | [HND_Q](https://celade.cepal.org/censosinfo/Boletas/HD_Bdef_2013.pdf) |

**DDPT業務の自動化への適用案。** 2013自治体別報告から採用値を取り込み、2026調査は結果公表が確認できた項目から更新する。SGJD等の規範・自治体計画・予算を別取得処理で接続する。

**残る確認。** 2026再編後の地方計画支援の細分掌、国家計画法の後続改正、各PDM-OTの現行版・298自治体の全数値抽出は残件。

<a id="country-MEX"></a>

### 13. メキシコ（MEX）

**計画法体系。** 連邦の計画法と州・自治体の計画法を分ける。国のLey de Planeaciónだけから全国一律の自治体PDMの義務・期限・様式を決めない。

連邦憲法・Ley de Planeación（1983）→対象州の計画法・自治体法→自治体PDM。都市・土地利用計画は別の連邦／州制度も確認。

| 主要法令・規範 | 制定／改正・発出年 | 概要・適用と留意点 |
| --- | --- | --- |
| [Ley de Planeación](https://www.diputados.gob.mx/LeyesBiblio/pdf_mov/Ley_de_Planeacion.pdf) | 1983 | 連邦の計画制度。自治体PDMの義務・期限は州計画法・自治体法を追加照合する。 |
| [Ley de Planeación del Estado de México y Municipios（州の例）](https://legislacion.edomex.gob.mx/sites/legislacion.edomex.gob.mx/files/files/pdf/ley/vig/leyvig087.pdf) | 2001 | 一州の地方計画制度。全国の自治体へ一律転用しない。対象州の法令へ差し替える。 |

| 国と地方の関係 | 確認した制度と運用 |
| --- | --- |
| 国の所管・関係機関 | [SHCP（国家計画）／SEDATU（土地・都市）／州の計画機関・自治体](https://situ.sedatu.gob.mx/) |
| 国の役割 | SHCPは国家計画、SEDATUは土地・都市関連の業務を担う。州の計画機関との分担がある。国家の指標や補助制度は地方の計画・財源の文脈として接続する。 |
| 地方自治体の役割 | municipioを基礎にし、CDMXのalcaldíaを特別制度として区別する。州ごとに権限・手続き・行政区分を確定する。 |
| 作成・協議・承認 | 対象州の法令に基づく地方の作成・協議・議会等の承認を確認する。Estado de Méxicoの法を他州へコピーしない。 |
| 期間・見直し | 州法と地方任期・計画種類によって確認する。国家PNDの周期を自治体へそのまま適用しない。 |

関係の根拠：[MEX_L](https://www.diputados.gob.mx/LeyesBiblio/pdf_mov/Ley_de_Planeacion.pdf)、[MEX_L2](https://legislacion.edomex.gob.mx/sites/legislacion.edomex.gob.mx/files/files/pdf/ley/vig/leyvig087.pdf)、[MEX_A](https://situ.sedatu.gob.mx/)。制度枠組みの一次確認であり、個別自治体の最新承認・全改正の審査は含まない。

| 計画・統計の粒度 | この国での扱い |
| --- | --- |
| 法定主体に合わせる基本単位 | municipio／CDMX alcaldía（州・特別制度別） |
| 計画の種類 | 州法に基づくPDM／都市開発計画等 |
| 調査・結果の段階 | 2020全数基本票・標本拡大票。2025中間調査は別 |
| 調査年／詳細利用候補年 | 2020／2020 |
| 確認した統計の公表粒度 | 基本票・標本ともmunicipio、ただし提供項目差 |
| 自治体内部の補助粒度 | 基本票の選定指標はlocalidad／AGEB／manzana |
| 取得形式 | INEGI CSV・DBF・Excel・microdata・地理データ |
| 利用上の条件 | 基本38問と拡大103問を区別。拡大票は小街区までの推計を保証しない。 |

**国勢調査の分野別項目。** 次の確認段階は原表の全件抽出・統合検証とは異なる。

| テーマ | 具体的な項目 | 確認段階・粒度 | 根拠 |
| --- | --- | --- | --- |
| 人口・世帯 | 性・年齢、世帯、出生・死亡 | 公表目録確認。municipio。AGEB／manzanaは選定指標のみ | [MEX_C](https://inegi.org.mx/rnm/index.php/catalog/632) |
| 住宅 | 材料、室数、設備、保有 | 公表目録確認。municipio。AGEB／manzanaは選定指標のみ | [MEX_C](https://inegi.org.mx/rnm/index.php/catalog/632) |
| 水 | 水道・給水 | 公表目録確認。municipio。AGEB／manzanaは選定指標のみ | [MEX_C](https://inegi.org.mx/rnm/index.php/catalog/632) |
| 衛生 | 便所・排水 | 公表目録確認。municipio。AGEB／manzanaは選定指標のみ | [MEX_C](https://inegi.org.mx/rnm/index.php/catalog/632) |
| 家庭エネルギー | 電気 | 公表目録確認。municipio。AGEB／manzanaは選定指標のみ | [MEX_C](https://inegi.org.mx/rnm/index.php/catalog/632) |
| デジタル接続 | 住宅ネット・ICT設備 | 公表目録確認。municipio。AGEB／manzanaは選定指標のみ | [MEX_C](https://inegi.org.mx/rnm/index.php/catalog/632) |
| 教育 | 識字、就学、学歴 | 公表目録確認。municipio。AGEB／manzanaは選定指標のみ | [MEX_C](https://inegi.org.mx/rnm/index.php/catalog/632) |
| 就業・生計 | 経済活動（基本／標本の細目を確認） | 公表目録確認。municipio。AGEB／manzanaは選定指標のみ | [MEX_C](https://inegi.org.mx/rnm/index.php/catalog/632) |
| 包摂・健康の一部 | 障害、民族、医療サービス加入 | 公表目録確認。municipio。AGEB／manzanaは選定指標のみ | [MEX_C](https://inegi.org.mx/rnm/index.php/catalog/632) |
| 移住 | 出生地、従前居住地 | 公表目録確認。municipio。AGEB／manzanaは選定指標のみ | [MEX_C](https://inegi.org.mx/rnm/index.php/catalog/632) |

**DDPT業務の自動化への適用案。** 一州の法体系と自治体を先に選び、INEGI2020の基本／拡大票と公式コードを結合する。AGEB・manzanaの選定指標は自治体内部診断へ使い、PDM・都市計画・投資の資料へ接続する。

**残る確認。** 全州法の網羅確認、CDMXの詳細制度、自治体ごとの現行PDM・都市計画、標本小地域の精度は別調査。

<a id="country-NIC"></a>

### 14. ニカラグア（NIC）

**計画法体系。** 自治体法40と改正法に基づく地方開発計画を基本とし、国家の開発・貧困削減計画、計画予算投資の運用へ接続する。

Ley 40（1988、1997・2012等の改正）→municipioの開発計画・投資／予算→国家計画と財政運用の整合。

| 主要法令・規範 | 制定／改正・発出年 | 概要・適用と留意点 |
| --- | --- | --- |
| [Ley 40 de Municipios](https://legislacion.asamblea.gob.ni/SILEG/Iniciativas.nsf/c9a0faf9d8c5e28f062572c70052cde2/7ebe8ba4e242fa7b062579eb0064e3b6/%24FILE/Ley%20No.%20792%20reforma%20Ley%20de%20municipios.pdf) | 1988 | 自治体の開発計画等。1997・2012等の改正を併読。掲載リンクはLey 792による改正。 |

| 国と地方の関係 | 確認した制度と運用 |
| --- | --- |
| 国の所管・関係機関 | [大統領府・MHCP（計画予算投資）／自治体。地方支援の現行分掌は追加確認](https://www.hacienda.gob.ni/politica-institucional/) |
| 国の役割 | 大統領府・MHCPの国家計画、財政・投資の資料を利用する。地方計画支援の現在の分掌を旧組織名から推定しない。 |
| 地方自治体の役割 | municipioの地方開発と自治体議会の計画権限を扱う。自治区等の特別制度は通常自治体と別に適用を確認する。 |
| 作成・協議・承認 | 地方開発計画の自治体議会での承認等を、現行法・自治体の採択資料で確認する。古い計画の掲載だけで有効性を推定しない。 |
| 期間・見直し | 各PDMと国家計画・予算の対象年を原資料から取得する。2005の統計年と現行計画期間を分ける。 |

関係の根拠：[NIC_L](https://legislacion.asamblea.gob.ni/SILEG/Iniciativas.nsf/c9a0faf9d8c5e28f062572c70052cde2/7ebe8ba4e242fa7b062579eb0064e3b6/%24FILE/Ley%20No.%20792%20reforma%20Ley%20de%20municipios.pdf)、[NIC_A](https://www.hacienda.gob.ni/politica-institucional/)。制度枠組みの一次確認であり、個別自治体の最新承認・全改正の審査は含まない。

| 計画・統計の粒度 | この国での扱い |
| --- | --- |
| 法定主体に合わせる基本単位 | municipio |
| 計画の種類 | Plan de Desarrollo Municipal |
| 調査・結果の段階 | 2024実施情報あり。詳細結果は未確認、2005公開表を採用候補 |
| 調査年／詳細利用候補年 | 2024／2005 |
| 確認した統計の公表粒度 | 2005 municipio別巻 |
| 自治体内部の補助粒度 | barrios／comarcasの選定NBI等。混合出典に注意 |
| 取得形式 | 2005 PDF・圧縮ファイル。2024取得経路は未確認 |
| 利用上の条件 | 調査年2024と実際に使える詳細2005を分ける。古い値を最新と表示しない。 |

**国勢調査の分野別項目。** 次の確認段階は原表の全件抽出・統合検証とは異なる。

| テーマ | 具体的な項目 | 確認段階・粒度 | 根拠 |
| --- | --- | --- | --- |
| 人口・世帯 | 人口一般・世帯 | 公表目録確認。2005 municipio別巻の目録確認。項目別の表を追加取得 | [NIC_C](https://www.inide.gob.ni/docu/censos2005/censo2005.htm) |
| 住宅 | 住宅特性 | 公表目録確認。2005 municipio別巻の目録確認。項目別の表を追加取得 | [NIC_C](https://www.inide.gob.ni/docu/censos2005/censo2005.htm) |
| 水 | 水源・配管 | 調査票確認。2005 municipio別巻の目録確認。項目別の表を追加取得 | [NIC_Q](https://celade.cepal.org/censosinfo/Boletas/NI_BDef_2005.pdf) |
| 衛生 | 衛生設備 | 調査票確認。2005 municipio別巻の目録確認。項目別の表を追加取得 | [NIC_Q](https://celade.cepal.org/censosinfo/Boletas/NI_BDef_2005.pdf) |
| 家庭エネルギー | 照明電源・調理燃料 | 調査票確認。2005 municipio別巻の目録確認。項目別の表を追加取得 | [NIC_Q](https://celade.cepal.org/censosinfo/Boletas/NI_BDef_2005.pdf) |
| デジタル接続 | 未確認：2005のネット項目をこの台帳では確認できていない | 未確認。当該項目の公表粒度未確認 | [NIC_C](https://www.inide.gob.ni/docu/censos2005/censo2005.htm) |
| 教育 | 教育 | 公表目録確認。2005 municipio別巻の目録確認。項目別の表を追加取得 | [NIC_C](https://www.inide.gob.ni/docu/censos2005/censo2005.htm) |
| 就業・生計 | 経済活動 | 公表目録確認。2005 municipio別巻の目録確認。項目別の表を追加取得 | [NIC_C](https://www.inide.gob.ni/docu/censos2005/censo2005.htm) |
| 包摂・健康の一部 | NBI等は別公表資料・算定年を確認 | 公表目録確認。2005 municipio別巻の目録確認。項目別の表を追加取得 | [NIC_C](https://www.inide.gob.ni/docu/censos2005/censo2005.htm) |
| 移住 | 未確認：この台帳では移住詳細を未点検 | 未確認。当該項目の公表粒度未確認 | [NIC_C](https://www.inide.gob.ni/docu/censos2005/censo2005.htm) |

**DDPT業務の自動化への適用案。** 詳細公開を確認できる2005municipio表を古い基準年として取り込み、2024の新しい詳細結果の取得経路を別タスクとして解決する。近年の行政統計・投資で法定診断の不足を補う。

**残る確認。** 2024詳細結果、自治体・特別自治の最新改正、現在の地方計画支援部署、各PDMの現行本文は未網羅。

<a id="country-PAN"></a>

### 15. パナマ（PAN）

**計画法体系。** 地方分権法37と2015改正を基に、distrito単位の自治体計画PED、参加、投資・予算を接続する。

Ley 37（2009）・Ley 66改正（2015）→PED→参加・事業・予算。comarca等の特別制度は別確認。

| 主要法令・規範 | 制定／改正・発出年 | 概要・適用と留意点 |
| --- | --- | --- |
| [Ley 37 de Descentralización](https://www.descentralizacion.gob.pa/page/ley-37-2009-descentralizacion) | 2009 | 地方分権と地区計画。Ley 66（2015）等の改正を含めてPED・参加・予算へ接続。 |

| 国と地方の関係 | 確認した制度と運用 |
| --- | --- |
| 国の所管・関係機関 | [MEF（地域計画）／Autoridad Nacional de Descentralización（AND）／自治体](https://www.mef.gob.pa/2025/10/panama-presenta-el-presupuesto-mas-alto-de-su-historia-para-2026/) |
| 国の役割 | MEFの地域計画機能とANDの地方分権関連機能を区別する。国からの支援・資金と自治体の計画責任を同一視しない。 |
| 地方自治体の役割 | distritoを区域とするmunicipioが主要対象。corregimientoとlugar pobladoは自治体内の区分として保持し、別制度の計画・事業があれば別類型で管理する。 |
| 作成・協議・承認 | PEDの正式採択、参加記録、予算・事業の決定を各公式文書から確認する。計画が存在することと実施資金が確定していることを分ける。 |
| 期間・見直し | PEDの公表期間と現行改正・手引き、年次事業予算を個別に確認する。 |

関係の根拠：[PAN_L](https://www.descentralizacion.gob.pa/page/ley-37-2009-descentralizacion)、[PAN_A](https://www.mef.gob.pa/2025/10/panama-presenta-el-presupuesto-mas-alto-de-su-historia-para-2026/)。制度枠組みの一次確認であり、個別自治体の最新承認・全改正の審査は含まない。

| 計画・統計の粒度 | この国での扱い |
| --- | --- |
| 法定主体に合わせる基本単位 | distrito（municipio）。comarca等の特別制度は別確認 |
| 計画の種類 | Plan Estratégico Distrital（PED） |
| 調査・結果の段階 | 2023 Vol.V lugares poblados等公開 |
| 調査年／詳細利用候補年 | 2023／2023 |
| 確認した統計の公表粒度 | distrito／corregimiento／lugar pobladoの選定指標 |
| 自治体内部の補助粒度 | lugar poblado |
| 取得形式 | Excel・PDF・統計局集計表 |
| 利用上の条件 | 小地域表は選定項目。comarca・corregimientoを一律に自治体へ置換しない。 |

**国勢調査の分野別項目。** 次の確認段階は原表の全件抽出・統合検証とは異なる。

| テーマ | 具体的な項目 | 確認段階・粒度 | 根拠 |
| --- | --- | --- | --- |
| 人口・世帯 | 人口、性・年齢 | 公開表確認。distrito／corregimiento／lugar pobladoの選定指標 | [PAN_T](https://www.inec.gob.pa/archivos/P0705547520240201165824Panam%C3%A1.pdf) |
| 住宅 | 住宅、土間床等 | 公開表確認。distrito／corregimiento／lugar pobladoの選定指標 | [PAN_T](https://www.inec.gob.pa/archivos/P0705547520240201165824Panam%C3%A1.pdf) |
| 水 | 飲用水の有無 | 公開表確認。distrito／corregimiento／lugar pobladoの選定指標 | [PAN_T](https://www.inec.gob.pa/archivos/P0705547520240201165824Panam%C3%A1.pdf) |
| 衛生 | 便所の有無 | 公開表確認。distrito／corregimiento／lugar pobladoの選定指標 | [PAN_T](https://www.inec.gob.pa/archivos/P0705547520240201165824Panam%C3%A1.pdf) |
| 家庭エネルギー | 電気、薪・炭調理 | 公開表確認。distrito／corregimiento／lugar pobladoの選定指標 | [PAN_T](https://www.inec.gob.pa/archivos/P0705547520240201165824Panam%C3%A1.pdf) |
| デジタル接続 | 住宅の固定／モバイルネット欠如 | 公開表確認。distrito／corregimiento／lugar pobladoの選定指標 | [PAN_T](https://www.inec.gob.pa/archivos/P0705547520240201165824Panam%C3%A1.pdf) |
| 教育 | 識字・学歴等の選定項目 | 公開表確認。distrito／corregimiento／lugar pobladoの選定指標 | [PAN_T](https://www.inec.gob.pa/archivos/P0705547520240201165824Panam%C3%A1.pdf) |
| 就業・生計 | 経済活動の選定項目 | 公開表確認。distrito／corregimiento／lugar pobladoの選定指標 | [PAN_T](https://www.inec.gob.pa/archivos/P0705547520240201165824Panam%C3%A1.pdf) |
| 包摂・健康の一部 | 未確認：この台帳では障害・医療保障表を未点検 | 未確認。当該項目の公表粒度未確認 | [PAN_T](https://www.inec.gob.pa/archivos/P0705547520240201165824Panam%C3%A1.pdf) |
| 移住 | 未確認：この台帳では移住詳細を未点検 | 未確認。当該項目の公表粒度未確認 | [PAN_T](https://www.inec.gob.pa/archivos/P0705547520240201165824Panam%C3%A1.pdf) |

**DDPT業務の自動化への適用案。** 2023のlugares poblados選定表をdistrito・corregimientoへ対応付け、住宅サービスの欠如を診断する。PED・地方投資・予算をMEF、AND、自治体、公報から収集する。

**残る確認。** 全地区PEDの最新版・承認資料、comarcaの適用法、全テーマの小地域表、予算の地域帰属は残件。

<a id="country-PRY"></a>

### 16. パラグアイ（PRY）

**計画法体系。** 自治体基本法3966が持続可能な開発計画PDSと都市・土地利用計画POUTを区別して規定する。旧STPの国家計画業務は2023年設置のMEFに接続する。

Ley 3966（2010）→PDS＋POUT→自治体投資・予算。国家計画機関はLey 7158（2023）によるMEF体制。

| 主要法令・規範 | 制定／改正・発出年 | 概要・適用と留意点 |
| --- | --- | --- |
| [Ley 3966 Orgánica Municipal](https://www.bacn.gov.py/leyes-paraguayas/969/ley-n-3966-organica-municipall) | 2010 | art.224–226。持続可能な開発計画PDSと都市・土地利用計画POUTを区別して策定。 |
| [Ley 7158（MEF設置）](https://www.bacn.gov.py/leyes-paraguayas/11893/ley-n-7158-crea-el-ministerio-de-economia-) | 2023 | 財務省・公務機関・旧STPをMEFへ統合。古いSTP宛の規定と現在の所管を区別する。 |

| 国と地方の関係 | 確認した制度と運用 |
| --- | --- |
| 国の所管・関係機関 | [Ministerio de Economía y Finanzas（MEF）・Viceministerio de Economía y Planificación](https://www.mef.gov.py/es/institucional/organigrama-y-funciones) |
| 国の役割 | MEFの経済・計画担当が国家計画の関係機関。旧STP名のガイド・法令と現在の担当部署の対応を記録する。 |
| 地方自治体の役割 | municipioの持続可能な開発と都市・土地利用の二つを扱う。distritoの統計コードと自治体区域の一致は実データで確認する。 |
| 作成・協議・承認 | 自治体の執行側・議会側の権限と参加手続きを確認し、PDSとPOUTの採択資料を別々に管理する。 |
| 期間・見直し | PDSとPOUT、年度予算の対象期間・見直し条件をそれぞれの文書から取得する。 |

関係の根拠：[PRY_L](https://www.bacn.gov.py/leyes-paraguayas/969/ley-n-3966-organica-municipall)、[PRY_L2](https://www.bacn.gov.py/leyes-paraguayas/11893/ley-n-7158-crea-el-ministerio-de-economia-)、[PRY_A](https://www.mef.gov.py/es/institucional/organigrama-y-funciones)。制度枠組みの一次確認であり、個別自治体の最新承認・全改正の審査は含まない。

| 計画・統計の粒度 | この国での扱い |
| --- | --- |
| 法定主体に合わせる基本単位 | municipio／distrito |
| 計画の種類 | PDS／POUT |
| 調査・結果の段階 | 2022確報・住宅巻・地区地理指標公開 |
| 調査年／詳細利用候補年 | 2022／2022 |
| 確認した統計の公表粒度 | distrito |
| 自治体内部の補助粒度 | 細区分の公開テーマは追加確認 |
| 取得形式 | PDF・Excel・地理カタログ |
| 利用上の条件 | 住宅設備表と個人票・NBI・先住民調査を別に照合する。 |

**国勢調査の分野別項目。** 次の確認段階は原表の全件抽出・統合検証とは異なる。

| テーマ | 具体的な項目 | 確認段階・粒度 | 根拠 |
| --- | --- | --- | --- |
| 人口・世帯 | 人口、性・年齢 | 公表目録確認。distrito | [PRY_C](https://censo2022.ine.gov.py/) |
| 住宅 | 材料、所有・賃貸、室数 | 公表目録確認。distrito | [PRY_H](https://www.ine.gov.py/censo2022/documentos/2%20resultados%20finales%20viviendas.pdf) |
| 水 | 水源・給水 | 公表目録確認。distrito | [PRY_H](https://www.ine.gov.py/censo2022/documentos/2%20resultados%20finales%20viviendas.pdf) |
| 衛生 | 便所・排水 | 公表目録確認。distrito | [PRY_H](https://www.ine.gov.py/censo2022/documentos/2%20resultados%20finales%20viviendas.pdf) |
| 家庭エネルギー | 電気 | 公表目録確認。distrito | [PRY_H](https://www.ine.gov.py/censo2022/documentos/2%20resultados%20finales%20viviendas.pdf) |
| デジタル接続 | 住宅ネット・電話・PC | 公表目録確認。distrito | [PRY_H](https://www.ine.gov.py/censo2022/documentos/2%20resultados%20finales%20viviendas.pdf) |
| 教育 | 教育の公表巻あり。個別指標・粒度を追加確認 | 公表目録確認。distrito | [PRY_C](https://censo2022.ine.gov.py/) |
| 就業・生計 | 前週活動・職業等 | 調査票確認。当該項目の公表粒度未点検 | [PRY_H](https://www.ine.gov.py/censo2022/documentos/2%20resultados%20finales%20viviendas.pdf) |
| 包摂・健康の一部 | NBI・先住民関連の公表。障害等は追加確認 | 公表目録確認。distrito | [PRY_C](https://censo2022.ine.gov.py/) |
| 移住 | 未確認：この台帳では移住詳細を未点検 | 未確認。当該項目の公表粒度未確認 | [PRY_C](https://censo2022.ine.gov.py/) |

**DDPT業務の自動化への適用案。** 2022distrito住宅・人口指標をPDSの基礎にし、土地利用・環境・インフラ等をPOUTのために補完する。先住民調査・NBIは母集団と計算方法を別に確認する。

**残る確認。** 全自治体のPDS・POUTの採択状況、現行ガイド、就業等の個人票項目の地域別公表、公式区域の全照合は残件。

<a id="country-PER"></a>

### 17. ペルー（PER）

**計画法体系。** SINAPLANとCEPLANの国家計画体系に、地域政府のPDRCと県・地区自治体の協議型PDLCを接続する。

Ley 27972（2003）＋Decreto Legislativo 1088（2008）→地域PDRC／provincia・distritoのPDLC→機関計画・実施計画・予算。

| 主要法令・規範 | 制定／改正・発出年 | 概要・適用と留意点 |
| --- | --- | --- |
| [Ley 27972 Orgánica de Municipalidades](https://www.gob.pe/96430-el-plan-de-desarrollo-municipal-concertado) | 2003 | art.97等。地区・県自治体の協議型開発計画を接続。地域政府のPDRCは別の計画主体。 |
| [Decreto Legislativo 1088（SINAPLAN・CEPLAN）](https://www.gob.pe/institucion/ceplan/campa%C3%B1as/6243-conoce-las-normas-del-sinaplan) | 2008 | 国家戦略計画体系とCEPLANを規定。自治体のPDLCは自治体法・最新手引きと併読。 |

| 国と地方の関係 | 確認した制度と運用 |
| --- | --- |
| 国の所管・関係機関 | [CEPLAN（PCMに属する国家計画機関）／地方政府](https://www.gob.pe/ceplan) |
| 国の役割 | CEPLANが国家戦略計画体系の技術的な基準・手引きを提供する。財務・投資制度とは役割を分けて接続する。 |
| 地方自治体の役割 | municipalidad provincialとmunicipalidad distritalの両方が対象になり、地区の計画を県・地域と調整する。regionとprovinciaを同じ型にしない。 |
| 作成・協議・承認 | 自治体の協議型計画と議会の承認等を区別して原資料を収集する。CEPLANの方法への対応だけで地方の合意・承認が完成したとはしない。 |
| 期間・見直し | PDLCの対象期間と最新CEPLANガイド、PEI・POI、予算年度を分ける。任期の長さだけから計画期間を自動算出しない。 |

関係の根拠：[PER_L](https://www.gob.pe/96430-el-plan-de-desarrollo-municipal-concertado)、[PER_L2](https://www.gob.pe/institucion/ceplan/campa%C3%B1as/6243-conoce-las-normas-del-sinaplan)、[PER_A](https://www.gob.pe/ceplan)。制度枠組みの一次確認であり、個別自治体の最新承認・全改正の審査は含まない。

| 計画・統計の粒度 | この国での扱い |
| --- | --- |
| 法定主体に合わせる基本単位 | municipalidad provincial／distrital（地域政府はPDRC） |
| 計画の種類 | PDLC |
| 調査・結果の段階 | 2025結果公表開始・地区人口確認。2017詳細システムも利用可能 |
| 調査年／詳細利用候補年 | 2025／2025 |
| 確認した統計の公表粒度 | 2025 distrito人口。テーマ結果はdepartamentoの公表例確認 |
| 自治体内部の補助粒度 | 2017 REDATAMはdistrict／manzana等。2025同粒度は未確認 |
| 取得形式 | 2025結果資料・2017 REDATAM・地区情報システム |
| 利用上の条件 | 2025の人口地区表を、全テーマ地区公開済みという意味にしない。必要時は2017を別系列で採用。 |

**国勢調査の分野別項目。** 次の確認段階は原表の全件抽出・統合検証とは異なる。

| テーマ | 具体的な項目 | 確認段階・粒度 | 根拠 |
| --- | --- | --- | --- |
| 人口・世帯 | 人口、性・年齢 | 公式結果記事確認。2025 departamento公表例。人口のみprovincia／distritoも確認 | [PER_T](https://www.gob.pe/institucion/inei/noticias/1426058-inei-poblacion-de-cusco-registro-1-millon-379-mil-habitantes-segun-resultados-de-los-censos-nacionales-2025) |
| 住宅 | 種類、居住、壁・屋根 | 公式結果記事確認。2025 departamento公表例。人口のみprovincia／distritoも確認 | [PER_T](https://www.gob.pe/institucion/inei/noticias/1426058-inei-poblacion-de-cusco-registro-1-millon-379-mil-habitantes-segun-resultados-de-los-censos-nacionales-2025) |
| 水 | 屋内公共給水 | 公式結果記事確認。2025 departamento公表例。人口のみprovincia／distritoも確認 | [PER_T](https://www.gob.pe/institucion/inei/noticias/1426058-inei-poblacion-de-cusco-registro-1-millon-379-mil-habitantes-segun-resultados-de-los-censos-nacionales-2025) |
| 衛生 | 下水 | 公式結果記事確認。2025 departamento公表例。人口のみprovincia／distritoも確認 | [PER_T](https://www.gob.pe/institucion/inei/noticias/1426058-inei-poblacion-de-cusco-registro-1-millon-379-mil-habitantes-segun-resultados-de-los-censos-nacionales-2025) |
| 家庭エネルギー | 電気、調理燃料 | 公式結果記事確認。2025 departamento公表例。人口のみprovincia／distritoも確認 | [PER_T](https://www.gob.pe/institucion/inei/noticias/1426058-inei-poblacion-de-cusco-registro-1-millon-379-mil-habitantes-segun-resultados-de-los-censos-nacionales-2025) |
| デジタル接続 | 世帯ネット・携帯・PC | 公式結果記事確認。2025 departamento公表例。人口のみprovincia／distritoも確認 | [PER_T](https://www.gob.pe/institucion/inei/noticias/1426058-inei-poblacion-de-cusco-registro-1-millon-379-mil-habitantes-segun-resultados-de-los-censos-nacionales-2025) |
| 教育 | 学歴 | 公式結果記事確認。2025 departamento公表例。人口のみprovincia／distritoも確認 | [PER_T](https://www.gob.pe/institucion/inei/noticias/1426058-inei-poblacion-de-cusco-registro-1-millon-379-mil-habitantes-segun-resultados-de-los-censos-nacionales-2025) |
| 就業・生計 | 未確認：2025就業表の対象粒度 | 未確認。当該項目の公表粒度未確認 | [PER_T](https://www.gob.pe/institucion/inei/noticias/1426058-inei-poblacion-de-cusco-registro-1-millon-379-mil-habitantes-segun-resultados-de-los-censos-nacionales-2025) |
| 包摂・健康の一部 | 未確認：2025障害・医療保障表の対象粒度 | 未確認。当該項目の公表粒度未確認 | [PER_T](https://www.gob.pe/institucion/inei/noticias/1426058-inei-poblacion-de-cusco-registro-1-millon-379-mil-habitantes-segun-resultados-de-los-censos-nacionales-2025) |
| 移住 | 2020–2025移住 | 公式結果記事確認。2025 departamento公表例。人口のみprovincia／distritoも確認 | [PER_T](https://www.gob.pe/institucion/inei/noticias/1426058-inei-poblacion-de-cusco-registro-1-millon-379-mil-habitantes-segun-resultados-de-los-censos-nacionales-2025) |

**DDPT業務の自動化への適用案。** 2025地区人口と確認済みテーマ結果を採用し、2025の詳細粒度が不足する指標は2017系列を明示して接続する。UBIGEO等の公式コードを介してPDLC・公共投資・施設統計を補完する。

**残る確認。** 2025全テーマの地区表・一括データ、全PDLCの最新承認、現行ガイドの期間条件、地理改編への対応は追加確認。

<a id="country-DOM"></a>

### 18. ドミニカ共和国（DOM）

**計画法体系。** SNPIP、END、自治体法に基づくPMDを接続する。県・広域の計画・協議と自治体政府の計画権限を区別する。

Ley 498-06（2006）→END Ley 1-12（2012）・国家複数年計画→Ley 176-07（2007）の自治体PMD→行動計画・公共投資・予算。

| 主要法令・規範 | 制定／改正・発出年 | 概要・適用と留意点 |
| --- | --- | --- |
| [Ley 176-07 del Distrito Nacional y los Municipios](https://ayuntamientocomendador.gob.do/transparencia/wp-content/uploads/2026/01/PDM-Comendador-2025-2029.pdf) | 2007 | art.122等の自治体開発計画・参加。PMDと県・地域の基礎資料を別の制度・主体として扱う。 |
| [Ley 498-06 de Planificación e Inversión Pública](https://www.hacienda.gob.do/wp-content/uploads/2023/12/PNPSP-Plan-Nacional-Plurianual-del-Sector-Pu%CC%81blico_compressed.pdf) | 2006 | 国家計画・公共投資体系。地方計画と上位計画・事業投資の整合確認に使う。 |
| [Ley 1-12 Estrategia Nacional de Desarrollo 2030](https://transparencia.hacienda.gob.do/wp-content/uploads/2023/04/1-Ley-No-1-12-Ley-de-la-Estrategia-Nacional-de-Desarrollo-2030_.pdf) | 2012 | 長期国家開発戦略。地方の課題・目標・事業との対応根拠に使う。 |
| [Ley 45-25（省庁統合）](https://www.presidencia.gob.do/noticias/presidente-abinader-promulga-ley-que-dispone-fusion-del-ministerio-de-hacienda-y-el) | 2025 | HaciendaとMEPyDを統合しMHEを設置。旧組織名と現在の提出・技術支援先を区別する。 |

| 国と地方の関係 | 確認した制度と運用 |
| --- | --- |
| 国の所管・関係機関 | [Ministerio de Hacienda y Economía（MHE、2025統合）／地方政府](https://www.presidencia.gob.do/noticias/presidente-abinader-promulga-ley-que-dispone-fusion-del-ministerio-de-hacienda-y-el) |
| 国の役割 | 2025年のLey 45-25でMHEに統合。中央の計画・技術支援機能と地方政府の作成・決定を分ける。DDPT等の現在の部署名・分掌は案件時の公式組織で照合する。 |
| 地方自治体の役割 | municipioのPMDを基本にし、distrito municipalの権限・適用は別確認する。provinciaを市町村と同型の自治体政府として扱わない。 |
| 作成・協議・承認 | 自治体の計画作成、CDM等による参加・協議、議会等の正式な採択を区別する。SISMAPの評価・証拠は資料源として使い、取得進捗と混ぜない。 |
| 期間・見直し | PMDの実際の対象期間、国家計画・投資・予算年度を原本に従って別管理する。県の基礎資料の作成段階を自治体PMDの公式状態へ転用しない。 |

関係の根拠：[DOM_L](https://ayuntamientocomendador.gob.do/transparencia/wp-content/uploads/2026/01/PDM-Comendador-2025-2029.pdf)、[DOM_L2](https://www.hacienda.gob.do/wp-content/uploads/2023/12/PNPSP-Plan-Nacional-Plurianual-del-Sector-Pu%CC%81blico_compressed.pdf)、[DOM_L3](https://transparencia.hacienda.gob.do/wp-content/uploads/2023/04/1-Ley-No-1-12-Ley-de-la-Estrategia-Nacional-de-Desarrollo-2030_.pdf)、[DOM_L4](https://www.presidencia.gob.do/noticias/presidente-abinader-promulga-ley-que-dispone-fusion-del-ministerio-de-hacienda-y-el)。制度枠組みの一次確認であり、個別自治体の最新承認・全改正の審査は含まない。

| 計画・統計の粒度 | この国での扱い |
| --- | --- |
| 法定主体に合わせる基本単位 | municipio（distrito municipalは権限・適用を別確認） |
| 計画の種類 | PMD／上位の地域・県計画を区別 |
| 調査・結果の段階 | 2022結果表・2026刊行の水衛生特集等 |
| 調査年／詳細利用候補年 | 2022／2022 |
| 確認した統計の公表粒度 | municipio／distrito municipal（項目別） |
| 自治体内部の補助粒度 | sección／barrio等の当該テーマ公開範囲は追加確認 |
| 取得形式 | ONE Excel・PDF・統計表 |
| 利用上の条件 | 個人ネット5歳以上・過去3か月と世帯の接続を混同しない。2026刊行でも統計年は2022。 |

**国勢調査の分野別項目。** 次の確認段階は原表の全件抽出・統合検証とは異なる。

| テーマ | 具体的な項目 | 確認段階・粒度 | 根拠 |
| --- | --- | --- | --- |
| 人口・世帯 | 性・年齢、世帯 | 公表目録確認。municipio／distrito municipal（項目別） | [DOM_C](https://www.one.gob.do/datos-y-estadisticas/temas/censos/poblacion-y-vivienda/2022/) |
| 住宅 | 材料、室数、居住条件 | 公表目録確認。municipio／distrito municipal（項目別） | [DOM_C](https://www.one.gob.do/datos-y-estadisticas/temas/censos/poblacion-y-vivienda/2022/) |
| 水 | 家庭用・飲用の水源 | 公表目録確認。municipio／distrito municipal（項目別） | [DOM_W](https://www.one.gob.do/publicaciones/2026/fasciculo-ii-agua-y-saneamiento-en-los-hogares-de-la-republica-dominicana/) |
| 衛生 | 便所・共同利用 | 公表目録確認。municipio／distrito municipal（項目別） | [DOM_W](https://www.one.gob.do/publicaciones/2026/fasciculo-ii-agua-y-saneamiento-en-los-hogares-de-la-republica-dominicana/) |
| 家庭エネルギー | 照明・調理燃料 | 公表目録確認。municipio／distrito municipal（項目別） | [DOM_C](https://www.one.gob.do/datos-y-estadisticas/temas/censos/poblacion-y-vivienda/2022/) |
| デジタル接続 | 個人ネット利用5歳以上・過去3か月 | 公表目録確認。municipioの表を確認。DMの同表は未確認 | [DOM_C](https://www.one.gob.do/datos-y-estadisticas/temas/censos/poblacion-y-vivienda/2022/) |
| 教育 | 就学・学歴（学歴3歳以上等） | 公表目録確認。municipio／distrito municipal（項目別） | [DOM_C](https://www.one.gob.do/datos-y-estadisticas/temas/censos/poblacion-y-vivienda/2022/) |
| 就業・生計 | 職業・経済活動設問 | 設問の公式説明確認。2022自治体別就業表は未確認 | [DOM_Q](https://www.one.gob.do/media/jo4holms/cabalidad-en-las-respuestas-de-censos-2010-y-2022.pdf) |
| 包摂・健康の一部 | 機能上の困難5歳以上 | 公表目録確認。provinciaの表を確認。municipioの同表は未確認 | [DOM_C](https://www.one.gob.do/datos-y-estadisticas/temas/censos/poblacion-y-vivienda/2022/) |
| 移住 | 未確認：この台帳では移住詳細を未点検 | 未確認。当該項目の公表粒度未確認 | [DOM_C](https://www.one.gob.do/datos-y-estadisticas/temas/censos/poblacion-y-vivienda/2022/) |

**DDPT業務の自動化への適用案。** ONE2022を共通基礎とし、Temáticoの省庁資料をsource単位に再取得可能にする。診断文、参加・要求票、RUDCT相当の事業整理、PMD章別草案を根拠IDで接続し、地域の判断に応じて再生成する。

**残る確認。** MHEの現行内部権限の細部、全自治体の承認根拠、DMの対象条件、各分野の最新地域統計・再配布条件の全確認は今回の調査範囲外。

<a id="country-URY"></a>

### 19. ウルグアイ（URY）

**計画法体系。** 自治体の地域開発・管理計画と、departamentoが担う土地利用・予算の重要な権限を分ける。自治体財源は部門政府の配分と国家FIGM等に接続する。

Ley 18.308（2008）の土地利用制度＋Ley 19.272（2014）の自治体制度→departamentoの土地利用／予算とmunicipioのPQM・POA。

| 主要法令・規範 | 制定／改正・発出年 | 概要・適用と留意点 |
| --- | --- | --- |
| [Ley 19.272 Descentralización y Participación Ciudadana](https://www.impo.com.uy/bases/leyes/19272-2014) | 2014 | 自治体の機能と計画・参加の枠組み。2026のOPP実務でPQM・POA・管理合意を確認。 |
| [Ley 18.308 Ordenamiento Territorial y Desarrollo Sostenible](https://www.impo.com.uy/bases/leyes/18308-2008) | 2008 | 土地利用計画の重要な権限はdepartamento側。Plan Localという名称だけでmunicipio所管と決めない。 |

| 国と地方の関係 | 確認した制度と運用 |
| --- | --- |
| 国の所管・関係機関 | [Oficina de Planeamiento y Presupuesto（OPP）／土地利用は部門政府・MVOT](https://www.opp.gub.uy/es/noticias/ciclo-de-apoyo-la-planificacion-figm-2026) |
| 国の役割 | OPPがFIGM等を通じた自治体計画・管理を支援し、2026にPQM・POA・管理合意の運用を確認。土地利用は部門政府・MVOTの関係を別に扱う。 |
| 地方自治体の役割 | municipioは地域開発プログラム等を作り、公聴の対象とする。departamentoのIntendencia・Juntaと権限・財源の関係がある。 |
| 作成・協議・承認 | 自治体プログラムの住民への提示、部門政府の予算、FIGMの条件を区別する。Plan Localという名称だけで自治体単独の承認権限と判断しない。 |
| 期間・見直し | 2026運用で5年のPQMと年次POAがあることを確認。実際の対象期間、部門予算、個別土地利用計画の改定時期を分ける。 |

関係の根拠：[URY_L](https://www.impo.com.uy/bases/leyes/19272-2014)、[URY_L2](https://www.impo.com.uy/bases/leyes/18308-2008)、[URY_A](https://www.opp.gub.uy/es/noticias/ciclo-de-apoyo-la-planificacion-figm-2026)、[URY_REL](https://www.impo.com.uy/bases/leyes/19272-2014/19)。制度枠組みの一次確認であり、個別自治体の最新承認・全改正の審査は含まない。

| 計画・統計の粒度 | この国での扱い |
| --- | --- |
| 法定主体に合わせる基本単位 | municipio（管理・開発）＋departamento（土地利用） |
| 計画の種類 | PQM／POA、部門政府の土地利用計画 |
| 調査・結果の段階 | 2023加重版（2026年5月更新）。旧2024版は置換済み |
| 調査年／詳細利用候補年 | 2023／2023 |
| 確認した統計の公表粒度 | 2026版でmunicipio／localidad等を拡張 |
| 自治体内部の補助粒度 | segmento等。秘匿・変数提供条件を確認 |
| 取得形式 | 加重microdata・表・Shapefile／GeoPackage |
| 利用上の条件 | 旧版との混在不可。個票行数を人口総数にせず、公式ウェイトと母集団に従う。 |

**国勢調査の分野別項目。** 次の確認段階は原表の全件抽出・統合検証とは異なる。

| テーマ | 具体的な項目 | 確認段階・粒度 | 根拠 |
| --- | --- | --- | --- |
| 人口・世帯 | 人口・世帯・住宅の加重データ | 公開データ案内確認。2026版でmunicipio／localidad等を拡張 | [URY_C](https://www.gub.uy/instituto-nacional-estadistica/politicas-y-gestion/microdatos-censo-2023-ponderados) |
| 住宅 | 壁・屋根・床、住宅種類・居住状態 | 変数辞書確認。2026年7月版辞書にmunicipio／segmento等あり。変数別の利用範囲を追加照合 | [URY_D](https://www4.ine.gub.uy/Anda5/index.php/catalog/781/data-dictionary/F1) |
| 水 | 水源、住宅への水の到達方法 | 変数辞書確認。2026年7月版辞書にmunicipio／segmento等あり。変数別の利用範囲を追加照合 | [URY_D](https://www4.ine.gub.uy/Anda5/index.php/catalog/781/data-dictionary/F1) |
| 衛生 | 便所・水洗、排水方法 | 調査票確認。2023調査票で確認。2026加重版の同変数・municipio集計条件は追加照合 | [URY_Q](https://www.gub.uy/instituto-nacional-estadistica/sites/instituto-nacional-estadistica/files/2025-02/Cuestionario_censo2023%20%281%29.pdf) |
| 家庭エネルギー | 主な電気照明の方法。2023調査票には調理・暖房燃料もある。2026版の同変数提供条件を確認する。 | 変数辞書確認。2026年7月版辞書にmunicipio／segmento等あり。変数別の利用範囲を追加照合 | [URY_D](https://www4.ine.gub.uy/Anda5/index.php/catalog/781/data-dictionary/F1) |
| デジタル接続 | 世帯のインターネットアクセス、PC等の設備 | 調査票確認。2023調査票で確認。2026加重版の同変数・municipio集計条件は追加照合 | [URY_Q](https://www.gub.uy/instituto-nacional-estadistica/sites/instituto-nacional-estadistica/files/2025-02/Cuestionario_censo2023%20%281%29.pdf) |
| 教育 | 就学・教育段階・教育歴 | 調査票確認。2023調査票で確認。2026加重版の同変数・municipio集計条件は追加照合 | [URY_Q](https://www.gub.uy/instituto-nacional-estadistica/sites/instituto-nacional-estadistica/files/2025-02/Cuestionario_censo2023%20%281%29.pdf) |
| 就業・生計 | 前週活動、求職、職業・産業・従業上の地位、就業場所 | 調査票確認。2023調査票で確認。2026加重版の同変数・municipio集計条件は追加照合 | [URY_Q](https://www.gub.uy/instituto-nacional-estadistica/sites/instituto-nacional-estadistica/files/2025-02/Cuestionario_censo2023%20%281%29.pdf) |
| 包摂・健康の一部 | 日常生活上の困難、ケア関連設問 | 調査票確認。2023調査票で確認。2026加重版の同変数・municipio集計条件は追加照合 | [URY_Q](https://www.gub.uy/instituto-nacional-estadistica/sites/instituto-nacional-estadistica/files/2025-02/Cuestionario_censo2023%20%281%29.pdf) |
| 移住 | 出生地・従前居住地・入国年 | 調査票確認。2023調査票で確認。2026加重版の同変数・municipio集計条件は追加照合 | [URY_Q](https://www.gub.uy/instituto-nacional-estadistica/sites/instituto-nacional-estadistica/files/2025-02/Cuestionario_censo2023%20%281%29.pdf) |

**DDPT業務の自動化への適用案。** 2026加重版のmunicipio_136等のコードと人口・住宅変数を照合して診断を作る。自治体PQM・POAと部門政府の土地利用・財政を別資料として同じ地域から参照させる。

**残る確認。** 加重版の項目別母集団・秘匿、各自治体のPQM・POAと部門計画、未自治体化地域の扱い・全域対応は追加確認。

<a id="country-VEN"></a>

### 20. ベネズエラ（VEN）

**計画法体系。** 国家・州・自治体の計画に加え、コミューン等の参加型計画の系統を持つ。通常の自治体計画とコミューンの計画を同じ行政粒度として統合しない。

Ley Orgánica de Planificación Pública y Popular（2010、2014改正）→国家・州・自治体・コミュニティの計画→年次実施等。

| 主要法令・規範 | 制定／改正・発出年 | 概要・適用と留意点 |
| --- | --- | --- |
| [Ley Orgánica de Planificación Pública y Popular](https://mppp.gob.ve/marco-legal/leyes-y-reglamentos/) | 2010 | 国・地方・コミュニティの計画体系。所管省は2014改正法を掲載しており、2010本文のみで実装しない。 |
| [Ley Orgánica de Planificación Pública y Popular（改正）](https://mppp.gob.ve/marco-legal/leyes-y-reglamentos/) | 2014 | MPPPがG.O.E.6.148（2014-11-18）を掲載。案件時に条文・追加改正を照合。 |

| 国と地方の関係 | 確認した制度と運用 |
| --- | --- |
| 国の所管・関係機関 | [Ministerio del Poder Popular de Planificación（MPPP）／地方政府](https://mppp.gob.ve/) |
| 国の役割 | MPPPが国家の計画体系の所管。省の法令ページに2014改正法があり、2010原文だけで現行の権限を確定しない。 |
| 地方自治体の役割 | municipioのPlan Municipal de Desarrolloと州・コミューンの計画を別類型として扱う。parroquiaの統計地理は自治体内部との関係を照合する。 |
| 作成・協議・承認 | 首長・地方公共計画評議会等の役割と採択機関を現行改正法で点検する。資料取得が難しい地域について、承認や計画不存在を断定しない。 |
| 期間・見直し | 国家計画・自治体計画・年次実施の対象期間をそれぞれ取得する。古い国家計画の年を現在の期間へ転記しない。 |

関係の根拠：[VEN_L](https://mppp.gob.ve/marco-legal/leyes-y-reglamentos/)、[VEN_L2](https://mppp.gob.ve/marco-legal/leyes-y-reglamentos/)、[VEN_A](https://mppp.gob.ve/)。制度枠組みの一次確認であり、個別自治体の最新承認・全改正の審査は含まない。

| 計画・統計の粒度 | この国での扱い |
| --- | --- |
| 法定主体に合わせる基本単位 | municipio（州・コミューン計画と区別） |
| 計画の種類 | Plan Municipal de Desarrollo |
| 調査・結果の段階 | 詳細票2011確認。UNSDの2021実施日記録は結果と未照合 |
| 調査年／詳細利用候補年 | 2011／2011 |
| 確認した統計の公表粒度 | municipio／parroquiaは票で識別。公開表未取得 |
| 自治体内部の補助粒度 | 公開数値の最小粒度未確認 |
| 取得形式 | 2011調査票PDF・公式公開経路の再探索 |
| 利用上の条件 | 2021記録の意味・結果公表を確定できていない。2011を現在人口・設備率として扱わない。 |

**国勢調査の分野別項目。** 次の確認段階は原表の全件抽出・統合検証とは異なる。

| テーマ | 具体的な項目 | 確認段階・粒度 | 根拠 |
| --- | --- | --- | --- |
| 人口・世帯 | 性・年齢、続柄 | 調査票確認。公開粒度未確認（票ではmunicipio／parroquiaを識別） | [VEN_C](https://celade.cepal.org/censosinfo/Boletas/VE_BDef_2011.pdf) |
| 住宅 | 材料、室数、所有・賃貸 | 調査票確認。公開粒度未確認（票ではmunicipio／parroquiaを識別） | [VEN_C](https://celade.cepal.org/censosinfo/Boletas/VE_BDef_2011.pdf) |
| 水 | 水源・供給頻度、飲用処理 | 調査票確認。公開粒度未確認（票ではmunicipio／parroquiaを識別） | [VEN_C](https://celade.cepal.org/censosinfo/Boletas/VE_BDef_2011.pdf) |
| 衛生 | 便所・排水 | 調査票確認。公開粒度未確認（票ではmunicipio／parroquiaを識別） | [VEN_C](https://celade.cepal.org/censosinfo/Boletas/VE_BDef_2011.pdf) |
| 家庭エネルギー | 電力網・発電機・太陽光、調理燃料 | 調査票確認。公開粒度未確認（票ではmunicipio／parroquiaを識別） | [VEN_C](https://celade.cepal.org/censosinfo/Boletas/VE_BDef_2011.pdf) |
| デジタル接続 | 世帯固定／モバイルネット | 調査票確認。公開粒度未確認（票ではmunicipio／parroquiaを識別） | [VEN_C](https://celade.cepal.org/censosinfo/Boletas/VE_BDef_2011.pdf) |
| 教育 | 識字、就学、学歴 | 調査票確認。公開粒度未確認（票ではmunicipio／parroquiaを識別） | [VEN_C](https://celade.cepal.org/censosinfo/Boletas/VE_BDef_2011.pdf) |
| 就業・生計 | 未確認：この台帳では就業設問・表を未点検 | 未確認。当該項目の公表粒度未確認 | [VEN_C](https://celade.cepal.org/censosinfo/Boletas/VE_BDef_2011.pdf) |
| 包摂・健康の一部 | 障害・疾患、民族・言語、医療保障・受診先 | 調査票確認。公開粒度未確認（票ではmunicipio／parroquiaを識別） | [VEN_C](https://celade.cepal.org/censosinfo/Boletas/VE_BDef_2011.pdf) |
| 移住 | 出生地・国籍、2006年居住地 | 調査票確認。公開粒度未確認（票ではmunicipio／parroquiaを識別） | [VEN_C](https://celade.cepal.org/censosinfo/Boletas/VE_BDef_2011.pdf) |

**DDPT業務の自動化への適用案。** まず2011調査票と取得可能な公表表の対応を確定する。UNSD2021記録との不一致を残したまま最新年を更新せず、計画資料・公式地理情報を独立した取得経路で調べる。

**残る確認。** 2021記録と統計結果の対応、2011自治体表の取得、現行法の後続改正、各自治体・コミューンの計画と承認資料は未確認。

## ドミ共の仕事をどう自動化するか

DDPT参照モデルの「診断→投資→需要→計画策定」を起点に、作業を8工程へ分ける。これは本調査からの実装提案であり、以下の全機能が既に動作するという報告ではない。[リポジトリのDDPT参照記録](../../01_DDPT_REFERENCE.md)と[今回追加した方法](../../PLANNING_CENSUS_METHOD.md)を参照。

| 工程・ドミ共との対応 | 自動化する作業 | 成果物 | 現地の判断・確認 | 実装状態 |
| --- | --- | --- | --- | --- |
| 01 制度・対象を定める | 法令・機関の候補収集、制定／改正／施行年抽出、計画類型と責任自治体の対応案 | 地域制度台帳・適用法一覧・提出様式候補 | 曖昧な権限・特別自治・現行改正の判断 | 方法として今回追加。法令解釈の完全自動決定は未実装 |
| 02 ONEに相当する基礎統計をそろえる | 表取得、正規化、指標辞書、地域結合、欠測と定義差検査 | 国勢調査の地域診断・出典台帳・結合例外 | 曖昧な地域対応と秘匿・推計の採用 | WDI/参照境界の初期収集は既存。20か国censusアダプターは未実装 |
| 03 Temáticoの不足を埋める | 不足指標から省庁・公式データセットを探索し、source別に取得・差分更新 | 省庁別ソース台帳、テーマ比較、データ不足一覧 | 指標採用・比較条件・優先度 | 探索方法を追加。省庁別コネクターは国別に実装 |
| 04 地域診断と課題仮説を作る | 人口構成、サービス不足、比較、出典付き記述案 | Diagnóstico territorial／章別の基礎資料 | 因果解釈、現地実態、地域が重視する課題 | 共通画面・基礎出力は既存。根拠拘束型の章別生成は段階実装 |
| 05 住民の要求・合意を整理する | 転記、分類、地域・課題との紐付け、重複候補抽出 | 参加履歴・要求台帳・未決事項 | 発言の意味、代表性、優先順位、合意 | 公開記録の整理まで。未実施の会合や合意は生成しない |
| 06 事業案を整える | 課題・対象・候補事業の対応案、既存事業重複照合、RUDCT相当の様式記入補助 | 事業候補票、根拠、対象地域、費用未確定欄 | 事業選定、技術設計、見積、資金確保、担当合意 | 方法を追加。ドミ共の様式・承認経路は国別に適応 |
| 07 PMD相当の計画草案を組む | 章立て対応、根拠付き下書き、表・図・指標・出典の組み込み | 編集可能な計画草案・根拠索引・補完欄 | 目標値、責任主体、財政約束、公式承認 | 既存Markdown/印刷HTMLを基礎。国別Word様式は採用後に実装・検証 |
| 08 実施・見直しにつなぐ | 新旧差分、期間整合、更新候補、計画の見直し箇所提示 | 予算執行／事業進捗／成果／評価の別表示 | 政策の見直し、優先順位の変更、評価の確定 | 計画資料契約は既存。更新スケジュール・APIは案件別設定 |

### 水道を例にした一連の処理

これは処理設計の例であり、架空の自治体に実数値を与えた例ではない。

1. その国の自治体計画・診断ガイドから、水道・衛生に関する要求と担当する地方政府を抽出する。
2. 国勢調査の水源・屋内配管・衛生設備を公式コードで結合し、対象世帯数と不足世帯数を集計する。対応が不明な地域は未結合として残す。
3. 条件が一致する自治体間で不足の分布を示す。小地域表があれば自治体内部の格差も示す。
4. 給水事業者や関係省庁から、供給時間・水質・管路・計画済み事業を補う。国勢調査だけではサービス品質や工事の必要性まで断定しない。
5. 診断の事実に出典を付け、「原因として現地確認が必要な点」を課題仮説として分ける。
6. 協議記録・要求票と照合し、重複する要求、既存事業との重複、未確認の受益範囲を整理する。
7. 事業案の対象・目的・根拠を現地様式に下書きする。費用・技術方式・目標・実施責任・財源は資料や合意がない限り未確定欄とする。
8. 合意した内容を計画草案・行動計画へ組み込み、実施後は事業進捗と給水の改善を別指標で追う。設備を建てたことと継続給水が改善したことを同一視しない。

### SISMAPがない国の計画資料

必要なのは統合システムの存在を前提にすることではなく、計画の内容・期間・対象地域・公式状態の根拠を集められること。地方政府のサイト、公報・議会決議、計画省庁の資料集、予算・決算、監査・評価を別々の情報源として扱う。公開APIがあれば使用し、なければExcel・PDF・公開目録から取得する。

資料を取得できなかった自治体にも、取得済みの統計・上位計画・公式手引きから策定用の基礎資料を出す。表示は「計画本文を未取得」「承認根拠は未確認」のように具体化し、計画が存在しないとは断定しない。承認状態、予算執行率、目標達成率、公式評価点は別々に保持する。

## 実装の順序

| 段階 | 追加するもの | 完了条件 |
|---|---|---|
| A 制度と国勢調査 | 制度台帳、自治体コード、票・変数の対応表、再実行可能な国別取得処理 | 代表自治体で値・定義・地域・出典・出力が一致し、全対象へ拡張した際の欠落を説明できる |
| B Temático補完 | 法定要求から作る不足一覧、省庁別アダプター、比較条件 | 必要項目について取得済み／未確認／秘匿／非該当を分け、原表から再現できる |
| C 策定実務 | 既存計画の整理、協議・要求・事業の根拠関係、現地様式の章別草案 | 草案中の事実を出典へ遡れ、合意と未決を分け、編集・差し戻し・再生成できる |
| D 見直し | 原資料の差分監視、予算・事業・成果・評価の接続 | 変更箇所と影響を提示し、候補版の検証失敗時に正常版を保持できる |

着手順の提案は、国内の公式表・自治体粒度・計画手引きの組が確認しやすい国から、Aを一国で通して検証すること。今回の調査ではボリビア、グアテマラ、コロンビア、エクアドルにその出発点となる資料がある。ただし取得速度・全自治体カバー率・法令適合性の性能比較は未実施であり、順位付けした評価ではない。

工数削減率はこの調査から算定しない。最初の案件で、資料探索、表抽出、地域照合、診断作成、草案修正の実時間と例外件数を測定して、自動化の効果を確認する。優先順位や住民合意の形成まで「自動化率」に算入しない。

## 残件と国別案件への引継ぎ

- ニカラグア2024の詳細結果、ベネズエラのUNSD2021記録と公表結果の対応、キューバ2026・ホンジュラス2026の実施／結果段階は、案件開始時の重点再確認対象。
- ペルーは2025人口の地区結果とテーマ別公表を分け、必要項目の詳細公開が確認できない時は2017を明示した別系列にする。
- コスタリカ2022は補正推計、ウルグアイ2023は2026年の加重版、ブラジル2022は全数・標本を分ける。
- アルゼンチン・メキシコの州法、特別自治、人口要件、各国の最新条例・手引き・提出部署は個別案件で確定する。
- 全20か国の全数値取得、著作権・再配布条件の全件照合、境界結合、サイト生成はこのレポートの実施範囲外。ここで確定したのは調査結果・探索先・方法である。

## 付属データ

- [テーマ別項目と確認段階](THEME_DETAILS.md)
- [20か国一覧CSV](countries.csv)
- [テーマ200行CSV](themes.csv)
- [主要法令CSV](laws.csv)
- [機械可読の研究台帳JSON](research.json)
- [出典台帳](SOURCES.md)
- [テンプレートへ組み込んだ方法](../../PLANNING_CENSUS_METHOD.md)

Excel版は同じ研究台帳から生成し、国別比較、計画法と所管、国と地方、テーマ項目、共通18テーマ、自動化工程、出典の7シートへ整理した。研究台帳はruntimeのdashboard.jsonへ直接投入するデータではない。本文に全20か国の章とテーマ表を含むため、補助ファイルを開かなくても国別レポートを読める。
