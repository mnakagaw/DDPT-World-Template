export const SUPPORTED_LANGUAGES=['en','es','ja'];

const COPY={
  'Explore':['Explorar','探索'],
  'Territorial diagnostic':['Diagnóstico territorial','地域診断'],
  'Thematic diagnostic':['Diagnóstico temático','テーマ診断'],
  'Data database':['Base de datos','データベース'],
  'Planning and resources':['Planificación y recursos','計画と資料'],
  'Planning materials':['Materiales de planificación','計画資料'],
  'Main pages':['Páginas principales','主要ページ'],
  'Language':['Idioma','言語'],
  'English':['Inglés','英語'],
  'Spanish':['Español','スペイン語'],
  'Japanese':['Japonés','日本語'],
  'Skip to content':['Saltar al contenido','本文へ移動'],
  'Return to the AreaData start':['Volver al inicio de AreaData','AreaDataの入口へ戻る'],
  'Loading acquired evidence…':['Cargando los datos recopilados…','収集済みデータを読み込んでいます…'],
  'AreaData · Source-reported and calculated values are labelled separately · Missing data remain explicit':['AreaData · Los valores publicados y calculados se identifican por separado · Los datos faltantes permanecen explícitos','AreaData・出典公表値と算出値を区別・欠測を明示'],
  'Share selection':['Compartir selección','選択内容を共有'],
  'Print page':['Imprimir página','ページを印刷'],
  'Source period':['Período de la fuente','出典年'],
  'Theme / indicator':['Tema / indicador','テーマ／指標'],
  'Selected area':['Área seleccionada','選択地域'],
  'Selected area · all records':['Área seleccionada · todos los registros','選択地域・全地域'],
  'All-area selector':['Selector de todas las áreas','全地域から選択'],
  'Find an area by name or code':['Buscar un área por nombre o código','地域名またはコードで検索'],
  'Name or code':['Nombre o código','名称またはコード'],
  'No matching areas.':['No hay áreas coincidentes.','一致する地域がありません。'],
  'Return to world view':['Volver a la vista mundial','世界表示へ戻る'],
  'Return to national view':['Volver a la vista nacional','全国表示へ戻る'],
  'Area hierarchy':['Jerarquía territorial','地域階層'],
  'Area identity and boundary edition':['Identidad del área y edición de límites','地域IDと境界版'],
  'Code system:':['Sistema de códigos:','コード体系：'],
  'Boundary edition:':['Edición de límites:','境界版：'],
  'Not specified':['No especificado','未指定'],
  'Not verified':['No verificado','未確認'],
  'No verified link':['Sin enlace verificado','確認済みリンクなし'],
  'No verified source collected':['No se recopiló una fuente verificada','確認済み出典なし'],
  'No periods acquired':['No se recopilaron períodos','取得済みの年なし'],
  'No source period':['Sin período de fuente','出典年なし'],
  'No data':['Sin datos','データなし'],
  'Not collected':['No recopilado','未収集'],
  'Not available':['No disponible','利用不可'],
  'Unavailable':['No disponible','利用不可'],
  'Not applicable':['No aplicable','非該当'],
  'Unverified':['No verificado','未確認'],
  'Source reported':['Publicado por la fuente','出典公表値'],
  'AreaData calculated':['Calculado por AreaData','AreaData算出値'],
  'Incomplete coverage':['Cobertura incompleta','被覆不完全'],
  'Comparison not established':['Comparación no establecida','比較未成立'],
  'Acquisition failed':['Falló la adquisición','取得失敗'],
  'Acquired':['Adquirido','取得済み'],
  'Link verified':['Enlace verificado','リンク確認済み'],
  'Body acquired':['Contenido adquirido','本文取得済み'],
  'Extracted':['Extraído','抽出済み'],
  'Pending':['Pendiente','保留'],
  'Other':['Otros','その他'],
  'Population':['Población','人口'],
  'Health':['Salud','保健'],
  'Basic services':['Servicios básicos','基礎サービス'],
  'Connectivity':['Conectividad','接続性'],
  'Official census population':['Población del censo oficial','公式国勢調査人口'],
  'UN population estimate / medium projection':['Estimación / proyección media de población de la ONU','国連人口推計／中位推計'],
  'UN World Population Prospects population':['Población de World Population Prospects de la ONU','国連世界人口推計の人口'],
  'Life expectancy at birth':['Esperanza de vida al nacer','出生時平均余命'],
  'Life expectancy at birth, total (years)':['Esperanza de vida al nacer, total (años)','出生時平均余命（年）'],
  'Access to electricity':['Acceso a electricidad','電力アクセス'],
  'Access to electricity (% of population)':['Acceso a electricidad (% de la población)','電力アクセス（人口比）'],
  'Individuals using the Internet':['Personas que usan Internet','インターネット利用者'],
  'Individuals using the Internet (% of population)':['Personas que usan Internet (% de la población)','インターネット利用者（人口比）'],
  'Central America — 7-country pilot':['Centroamérica — piloto de 7 países','中米7か国パイロット'],
  'Seven Central American countries':['Siete países de Centroamérica','中米7か国'],
  'Belize':['Belice','ベリーズ'],
  'Guatemala':['Guatemala','グアテマラ'],
  'El Salvador':['El Salvador','エルサルバドル'],
  'Honduras':['Honduras','ホンジュラス'],
  'Nicaragua':['Nicaragua','ニカラグア'],
  'Costa Rica':['Costa Rica','コスタリカ'],
  'Panama':['Panamá','パナマ'],
  'National':['Nacional','全国'],
  'country':['país','国'],
  'people':['personas','人'],
  'years':['años','年'],
  '% of population':['% de la población','人口比（%）'],
  'Location':['Ubicación','位置'],
  'Fit selected area':['Ajustar al área seleccionada','選択地域に合わせる'],
  'Show whole country':['Mostrar todo el país','国全体を表示'],
  'Sources and gaps':['Fuentes y vacíos','出典と不足'],
  'Sources, definitions and acquisition gaps':['Fuentes, definiciones y vacíos de adquisición','出典・定義・取得上の不足'],
  'Source register':['Registro de fuentes','出典台帳'],
  'Remaining acquisition gaps':['Vacíos de adquisición pendientes','未取得項目'],
  'Source':['Fuente','出典'],
  'Selected-area source':['Fuente del área seleccionada','選択地域の出典'],
  'Indicator sources; see calculation or gap details':['Fuentes del indicador; consulte el cálculo o los vacíos','指標の出典（計算・不足の詳細を参照）'],
  'Identity and evidence':['Identidad y evidencia','地域IDと根拠'],
  'Area':['Área','地域'],
  'Value':['Valor','値'],
  'Period':['Período','年'],
  'Status':['Estado','状態'],
  'Unit':['Unidad','単位'],
  'Compare this indicator':['Comparar este indicador','この指標を比較'],
  'Selected-period CSV':['CSV del período seleccionado','選択年のCSV'],
  'Time series CSV':['CSV de serie temporal','時系列CSV'],
  'Selected-area history':['Historial del área seleccionada','選択地域の履歴'],
  'Find and compare areas':['Buscar y comparar áreas','地域を検索・比較'],
  'Search ranking by name or code':['Buscar en la clasificación por nombre o código','ランキングを名称・コードで検索'],
  'Order':['Orden','並び順'],
  'Highest first':['Mayor primero','高い順'],
  'Lowest first':['Menor primero','低い順'],
  'Show selected in ranking':['Mostrar selección en la clasificación','選択地域をランキングに表示'],
  'Comparable geographic level':['Nivel geográfico comparable','比較する地域階層'],
  'No local areas acquired':['No se recopilaron áreas locales','取得済みの地方地域なし'],
  'World value · source-reported':['Valor mundial · publicado por la fuente','世界値・出典公表値'],
  'National value · source-reported':['Valor nacional · publicado por la fuente','全国値・出典公表値'],
  'Median of comparable local areas':['Mediana de áreas locales comparables','比較可能な地域の中央値'],
  'Local data coverage':['Cobertura de datos locales','地方データ被覆'],
  'Observed local range':['Rango local observado','観測済み地域の範囲'],
  'Open territorial diagnostic':['Abrir diagnóstico territorial','地域診断を開く'],
  'Open planning resources':['Abrir recursos de planificación','計画資料を開く'],
  'Comparison CSV':['CSV de comparación','比較CSV'],
  'Explore territorial data':['Explorar datos territoriales','地域データを探索'],
  'Compare an indicator':['Comparar un indicador','指標を比較'],
  'Open data database':['Abrir la base de datos','データベースを開く'],
  'Choose an entry area':['Elegir un área de entrada','入口となる地域を選択'],
  'Explore a place →':['Explorar un lugar →','地域を探索 →'],
  'Compare a theme →':['Comparar un tema →','テーマを比較 →'],
  'Open planning →':['Abrir planificación →','計画資料を開く →'],
  'AreaData data database':['Base de datos de AreaData','AreaDataデータベース'],
  'Inspect the database':['Consultar la base de datos','データベースを見る'],
  'From a region to each country,':['De una región a cada país,','地域から各国へ、'],
  'with every gap visible.':['con todos los vacíos visibles.','不足もすべて見える。'],
  'Territories':['Territorios','地域数'],
  'Source-reported values':['Valores publicados por las fuentes','出典公表値'],
  'Periods':['Períodos','収録年'],
  'Variable dictionary':['Diccionario de variables','変数辞書'],
  'Indicator catalog CSV':['CSV del catálogo de indicadores','指標台帳CSV'],
  'All observations CSV':['CSV de todas las observaciones','全観測CSV'],
  'Territory register CSV':['CSV del registro territorial','地域台帳CSV'],
  'Theme / indicator':['Tema / indicador','テーマ／指標'],
  'Definition and population':['Definición y población','定義と対象集団'],
  'Series / unit / aggregation':['Serie / unidad / agregación','系列／単位／集計'],
  'Build the regional database in stages':['Construir la base regional por etapas','地域データベースを段階的に構築'],
  'Inspect the data behind the dashboard.':['Consultar los datos del tablero.','ダッシュボードのデータを確認する。'],
  'Planning resources':['Recursos de planificación','計画資料'],
  'Choose one planning territory':['Elegir un territorio de planificación','計画対象地域を1つ選択'],
  'Choose an area':['Elegir un área','地域を選択'],
  'Prepare a working evidence base':['Preparar una base de evidencia de trabajo','計画作業用の根拠資料を作成'],
  'Download editable Markdown':['Descargar Markdown editable','編集用Markdownをダウンロード'],
  'Print-ready HTML':['HTML listo para imprimir','印刷用HTML'],
  'Evidence CSV':['CSV de evidencia','根拠CSV'],
  'Materials and findings CSV':['CSV de materiales y hallazgos','資料・所見CSV'],
  'Preview planning base':['Vista previa de la base de planificación','計画基礎資料をプレビュー'],
  'Outstanding evidence and next actions':['Evidencia pendiente y próximas acciones','未取得の根拠と次の対応'],
  'Review territorial evidence':['Revisar evidencia territorial','地域データを確認'],
  'Compare countries':['Comparar países','国を比較'],
  'Inspect source data':['Consultar datos fuente','元データを確認'],
  'Compare across areas':['Comparar áreas','地域間で比較'],
  'Back to top':['Volver arriba','ページ上部へ'],
  'Same-year international context':['Contexto internacional del mismo año','同一年の国際比較値'],
  'Mixed-year Census series':['Serie censal con años distintos','国ごとに年が異なる国勢調査系列'],
  'Series:':['Serie:','系列：'],
  'Exact sources follow.':['Las fuentes exactas se indican a continuación.','個別の出典は以下のとおりです。'],
  'opens a new tab':['se abre en una pestaña nueva','新しいタブで開きます'],
  '(opens a new tab)':['(se abre en una pestaña nueva)','（新しいタブで開きます）'],
  'Source first, complete cover second.':['Primero la fuente; después la cobertura completa.','出典を優先し、完全被覆の場合だけ集計します。'],
  'An exact observation for the selected area has priority. Only indicators with an approved method may be calculated from a complete, non-overlapping membership cover. A country total makes missing municipalities beneath it irrelevant. Percentages and non-additive measures are never simply averaged.':['Tiene prioridad una observación exacta del área seleccionada. Solo se calculan indicadores con un método aprobado y cobertura completa sin superposición. Si existe un total nacional, la ausencia de datos municipales no lo altera. Los porcentajes y medidas no aditivas nunca se promedian de forma simple.','選択地域そのものの観測値を優先します。承認した方法があり、重複のない構成地域を完全に被覆できる指標だけを集計します。国の公表値があれば、市の欠測は国の値に影響しません。率や加算できない指標は単純平均しません。'],
  'Showing':['Mostrando','表示中'],
  '. Choose “Whole …” to make that parent the selected area and clear its lower-area selection.':['. Elija «Todo…» para seleccionar el área superior y borrar la selección inferior.','。「全体…」を選ぶと上位地域全体へ切り替わり、下位地域の選択を解除します。'],
  'A location map. Fill colors do not represent population or service levels.':['Mapa de ubicación. Los colores de relleno no representan población ni niveles de servicio.','位置図です。塗り色は人口やサービス水準を示しません。'],
  'Gold outline':['Contorno dorado','金色の枠線'],
  '= selected area.':['= área seleccionada.','= 選択地域。'],
  'Calculated value.':['Valor calculado.','算出値。'],
  'No acquired time series for this area. National series are not substituted.':['No se adquirió una serie temporal para esta área. No se sustituyen series nacionales.','この地域の時系列は未取得です。全国系列で代用しません。'],
  'Comparison not established':['Comparación no establecida','比較未成立'],
  'Data edition':['Edición de datos','データ版'],
  'Schema':['Esquema','スキーマ'],
  'Retrieved':['Recuperado','取得日'],
  'Reference period':['Período de referencia','基準年'],
  'License':['Licencia','ライセンス'],
  'Original source':['Fuente original','原出典'],
  'Source terms':['Condiciones de la fuente','出典の利用条件'],
  'License source':['Fuente de la licencia','ライセンス出典'],
  'Next:':['Siguiente:','次の対応：'],
  'Reload':['Recargar','再読み込み'],
  'Dashboard data could not be loaded':['No se pudieron cargar los datos del tablero','ダッシュボードのデータを読み込めませんでした']
};

const indexFor=language=>language==='es'?0:language==='ja'?1:-1;

export function normalizeLanguage(value){
  const primary=String(value||'').trim().toLowerCase().split('-')[0];
  return SUPPORTED_LANGUAGES.includes(primary)?primary:'';
}

export function resolveLanguage({query='',stored='',browserLanguages=[]}={}){
  const explicit=normalizeLanguage(query);if(explicit)return explicit;
  const remembered=normalizeLanguage(stored);if(remembered)return remembered;
  for(const candidate of browserLanguages||[]){const resolved=normalizeLanguage(candidate);if(resolved)return resolved;}
  return 'en';
}

export function languageLocale(language){return language==='es'?'es':language==='ja'?'ja-JP':'en-US';}

const patternTranslations=[
  [/^Census (\d{4})$/,(m,l)=>l==='es'?`Censo ${m[1]}`:`国勢調査 ${m[1]}年`],
  [/^UN estimate (\d{4})$/,(m,l)=>l==='es'?`Estimación de la ONU ${m[1]}`:`国連推計 ${m[1]}年`],
  [/^UN medium projection (\d{4})$/,(m,l)=>l==='es'?`Proyección media de la ONU ${m[1]}`:`国連中位推計 ${m[1]}年`],
  [/^International reference(?: (.+))?$/,(m,l)=>l==='es'?`Referencia internacional${m[1]?` ${m[1]}`:''}`:`国際比較系列${m[1]?`・${m[1]}`:''}`],
  [/^Source series(?: (.+))?$/,(m,l)=>l==='es'?`Serie de la fuente${m[1]?` ${m[1]}`:''}`:`出典系列${m[1]?`・${m[1]}`:''}`],
  [/^Within the selected area — (.+)$/,(m,l)=>l==='es'?`Dentro del área seleccionada — ${m[1]}`:`選択地域内の比較 — ${m[1]}`],
  [/^All (\d+) member areas — including missing values$/,(m,l)=>l==='es'?`${m[1]} áreas miembros — incluidos los valores faltantes`:`構成地域 ${m[1]}件（欠測を含む）`],
  [/^Source register \((\d+)\)$/,(m,l)=>l==='es'?`Registro de fuentes (${m[1]})`:`出典台帳（${m[1]}件）`],
  [/^Remaining acquisition gaps \((\d+)\)$/,(m,l)=>l==='es'?`Vacíos de adquisición pendientes (${m[1]})`:`未取得項目（${m[1]}件）`],
  [/^Explore lower areas \((\d+)\)$/,(m,l)=>l==='es'?`Explorar áreas inferiores (${m[1]})`:`下位地域を探索（${m[1]}件）`],
  [/^(\d+) acquired indicators$/,(m,l)=>l==='es'?`${m[1]} indicadores adquiridos`:`取得済み指標 ${m[1]}件`],
  [/^(\d+) lower areas$/,(m,l)=>l==='es'?`${m[1]} áreas inferiores`:`下位地域 ${m[1]}件`],
  [/^Retrieved (.+)\.$/,(m,l)=>l==='es'?`Recuperado ${m[1]}.`:`取得日 ${m[1]}。`],
  [/^(.+) · data, diagnosis & planning$/,(m,l)=>l==='es'?`${m[1]} · datos, diagnóstico y planificación`:`${m[1]}・データ、診断、計画`],
  [/^(.+) — selected area$/,(m,l)=>l==='es'?`${m[1]} — área seleccionada`:`${m[1]} — 選択地域`],
  [/^(.+) — available materials$/,(m,l)=>l==='es'?`${m[1]} — materiales disponibles`:`${m[1]} — 利用可能な資料`],
  [/^Source reported · (.+)$/,(m,l)=>l==='es'?`Publicado por la fuente · ${m[1]}`:`出典公表値・${m[1]}`],
  [/^AreaData calculated · (.+)$/,(m,l)=>l==='es'?`Calculado por AreaData · ${m[1]}`:`AreaData算出値・${m[1]}`],
  [/^(.+) · (.+) · (AreaData calculated|Source reported|No data|Not available)$/,(m,l)=>`${translateText(m[1],l)} · ${m[2]} · ${translateText(m[3],l)}`],
  [/^people · (.+)$/,(m,l)=>l==='es'?`personas · ${m[1]}`:`人・${m[1]}`],
  [/^Code (.+)$/,(m,l)=>l==='es'?`Código ${m[1]}`:`コード ${m[1]}`]
];

export function translateText(value,language){
  if(language==='en')return String(value??'');
  const original=String(value??''),match=original.match(/^(\s*)([\s\S]*?)(\s*)$/);
  const core=match?.[2]??original,index=indexFor(language),translated=COPY[core]?.[index];
  if(translated!==undefined)return `${match[1]}${translated}${match[3]}`;
  for(const [pattern,render] of patternTranslations){const found=core.match(pattern);if(found)return `${match[1]}${render(found,language)}${match[3]}`;}
  return original;
}

export function translateInterface(root,language){
  const documentNode=root?.ownerDocument||root;if(!documentNode?.createTreeWalker)return;
  documentNode.documentElement.lang=language;
  for(const element of documentNode.querySelectorAll('[data-i18n]'))element.textContent=translateText(element.dataset.i18n,language);
  const walker=documentNode.createTreeWalker(root,4);let node;
  while((node=walker.nextNode())){
    if(node.parentElement?.closest('script,style,[data-i18n-skip]'))continue;
    node.nodeValue=translateText(node.nodeValue,language);
  }
  for(const element of root.querySelectorAll?.('[aria-label],[title],[placeholder]')||[]){
    for(const attribute of ['aria-label','title','placeholder'])if(element.hasAttribute(attribute))element.setAttribute(attribute,translateText(element.getAttribute(attribute),language));
  }
  for(const button of documentNode.querySelectorAll('[data-language]'))button.setAttribute('aria-pressed',String(button.dataset.language===language));
}

export function sourceSeriesLabel(indicator,observation,period=observation?.period,language='en'){
  const year=String(period||'').trim();
  if(indicator?.series_family==='census'){
    if(/^\d{4}$/.test(year))return translateText(`Census ${year}`,language);
    return translateText('Mixed-year Census series',language);
  }
  const stage=observation?.series_stage||indicator?.series_stage_by_period?.[year];
  if(stage==='estimate')return translateText(`UN estimate${year?` ${year}`:''}`,language);
  if(stage==='medium_projection')return translateText(`UN medium projection${year?` ${year}`:''}`,language);
  const base=indicator?.series_family==='international_reference'?'International reference':'Source series';
  return translateText(`${base}${year?` ${year}`:''}`,language);
}
