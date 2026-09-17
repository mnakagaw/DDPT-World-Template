# AreaData / DDPT World Template

**AreaDataの地域探索・データベース・計画資料と、国名を指定してDDPT型の国別ダッシュボードを作るための共通テンプレートです。**

実行テンプレート：0.9.2。データschema：0.2（任意項目で後方互換を維持）。共通UX仕様：0.5 candidate（改善後のv1.0採用は別途検証）。

地域診断の上部には分析対象を選ぶ位置図・階層選択・基本情報を置き、下部の各指標には対象内部の比較地図・全件表を置く。上部で地域を選ぶとその全体を即時診断し、下部の図・行への注目は上部の対象・他指標・URLを変えない。市・県の後に同じ所属先のRegion／Subregionを選び直した場合も、下位を解除して上位全体へ切り替える。指標・年を保持し、親の値が未取得なら親の欠測を示す。[操作契約](docs/02_COMMON_SPEC.md)を参照。

計画・資料ページでも同じ上位再選択を使える。計画の内容、予算・実績、公式評価を、それぞれの期間・単位・根拠とともに表示し、取得工程は補助情報へまとめる。`dataset.planning`で名称・採用区分・出力・地図の意味を設定する。[任意のデータ契約](docs/PLANNING_DATA_CONTRACT.md)と[実資料の再現例](examples/planning-evidence/README.md)を参照。

公開画面の見出し・導入文は、国勢調査で地域を知る、地図をたどる、地域を比較する、研究・計画へデータを再利用するという利用者の目的を先に伝える。試作段階・取得工程・欠測処理・集計方式をサイトの主見出しやキャッチコピーにしない。世界から地域へつながる構想と、現在の収録国・利用可能な地域階層を区別し、実装済みの機能だけを案内する。数値の解釈に必要な年・出典・欠測表示は各数値に残し、詳しい算出方法は出典欄で確認できる形にする。英語・スペイン語・日本語で同じ説明方針を使う。

## 新しいAIプロジェクトへの依頼

```text
https://github.com/mnakagaw/DDPT-World-Template を参照して、ウガンダ版を作って。
START_HERE.mdから読み、取得可能な公式データの収集から、動作するサイトと出力の検証まで進めてください。
```

国名を替えて利用できます。AIが開始シート、資料台帳、機能の採用判断を作ります。Privateリポジトリを読めるGitHub接続が必要です。

**[START_HERE.md](START_HERE.md)から開始してください。** 初期生成の後、現地統計局・国勢調査・公式行政区分・計画・予算資料の収集と統合を続ける手順です。

## 実行できること

| 段階 | 実装・手順 |
|---|---|
| 世界入口 | UN M49の国・地域台帳と5大陸、広域の所属を収集。WDIの人口・保健・電力・Internetの最新数年系列と参照地図を取得 |
| 国の特定 | 英語名・ISOコード・日本語名等を解決。曖昧な入力と地域集計グループを国として採用しない |
| 初期自動収集 | World Bank WDIの12指標の全国系列、geoBoundariesの取得可能なADM1参照境界、国別・国際共通sourceの調査開始票 |
| 記録 | 原資料、取得日時、SHA-256、出典、期間、境界の出所・版・利用条件、取得失敗と不足項目 |
| サイト生成 | 地域診断・テーマ比較・計画資料の独立ページ、地域保持URL、検索、位置図、指標別の内部比較地図・全件表、出典・欠測 |
| 出力 | 数値CSV、全指標・内部比較を含む診断Markdown・印刷用HTML・全件CSV、採用した計画資料出力。国別公式様式への適応は後続工程 |
| 国別の仕上げ | AIが国内公式資料を収集し、再実行できるアダプターを追加して地方値・資料を統合、再生成・検証 |

全国値を地方へ配分しません。geoBoundariesのIDは公式行政コードではなく、古い境界や行政・統計分類の違いを含む場合があります。公式コード・現行区分との対応は国別に確認します。

世界入口は2026-09-13の実取得で248の国・地域、4分野3,544公表値を保存した。世界値は公式WLD系列を使い、同一範囲の公式系列を取得していない大陸・広域は欠測を維持する。「Central America + Caribbean」はUN M49の013＋029を組み合わせた独自の探索区分で、Mexicoを含む。国際指標と国内統計の定義・単位・母集団を自動同一化しない。国版は別datasetとして接続し、国内行政階層・法定計画主体はその国の資料で確認する。参照図形に未結合・省略された79地域も台帳・表から消さない。[取得範囲と再現手順](docs/WORLD_ADAPTER.md)を参照。

0.10ではUN M49 Americas（019）の57国・地域を、Northern America、Central America + Caribbean、South Americaから探索できるアメリカ大陸adapterを追加した。UN WPP 2024人口は原本に行がある55国・地域へ同一年系列を統合し、BVTとSGSは欠測のまま保持する。中米7か国の検証済み国勢調査・国内階層だけを選択的に再利用し、残り50国・地域へCensus値を転用しない。地域版の[受入条件](templates/REGIONAL_ACCEPTANCE.md)、[独立監査](templates/REGIONAL_INDEPENDENT_AUDIT.md)、`verify-regional-delivery.mjs`を追加し、別担当の`ACCEPT`前は公開ゲートを通さない。

最初のAreaData公開試作は**中米7か国**（Belize、Guatemala、El Salvador、Honduras、Nicaragua、Costa Rica、Panama）。これはUN M49 013（Mexicoを含む）とは異なるAreaDataの明示的な試作範囲である。国別・国内地域診断は国勢調査を主系列にする。0.7では7か国の公式全国人口と採用可能な国内階層を取得・正規化した。国勢調査年が違うため、地域値は「最新利用可能国勢調査による混合基準年」とし、Belize 2022、Guatemala 2018、El Salvador 2024、Honduras 2013、Nicaragua 2005、Costa Rica 2022、Panama 2023を構成表に明記する。国の全国値があれば、その国内の自治体欠測は地域合計へ影響しない。率・平均は単純平均せず、不完全時は全体値を出さない。0.8ではUN WPP 2024 Rev.1の同一年人口推計を別系列として追加し、国勢調査との差を誤差幅と扱わない。画面は英語・スペイン語・日本語を切り替えられ、初回はブラウザ言語、明示選択後は保存した言語を使う。URLの`lang`指定を最優先し、画面内リンクにも引き継ぐ。

初期収集だけの状態は、地方統計・承認済み計画が揃った完成版ではありません。取得可能な国内資料を調べた結果と、未取得・未照合・未検証を残すことを作業手順で必須にしています。

[共通データと国別情報源の事前台帳](docs/COMMON_DATA_AND_SOURCE_REGISTRY.md)には、ラテンアメリカ20か国、ウガンダ、ベリーズの国勢調査・計画制度等の所在、および地域別データを持つ10の国際・複数国sourceを登録した。国別初期生成は`evidence/SOURCE_PREFLIGHT.json`と`.md`を自動作成する。中米生成は7か国をまとめた`evidence/CENSUS_SOURCE_PREFLIGHT.json`と`.md`も作る。所在登録は実データ取得・地理照合・指標採用とは別で、案件時点の再確認が必要である。

## コマンドで初期生成

Node.js 22以降。実行時の外部npm依存やAPIキーは不要です。実データの取得にはネット接続が必要です。XLSX原本の読取専用棚卸し・抽出にはPython 3と`openpyxl`が必要です。Node.jsだけでも世界・国別の初期生成と登録済み原本の収集は実行できます。

```sh
gh repo clone mnakagaw/DDPT-World-Template ./DDPT-World-Template
node ./DDPT-World-Template/scripts/create-country.mjs --country "ウガンダ" --out ./uganda-dashboard
node ./DDPT-World-Template/scripts/serve.mjs --dir ./uganda-dashboard/site --port 4173
```

`http://127.0.0.1:4173/`を開きます。作成先が既にある場合は上書きせず終了します。失敗時も取得済みの証拠を残します。ネットワーク障害で一部を取得できなかった場合は不足を記録し、取得できた情報で生成します。数値を１件も取得できなければ成功終了しません。

世界入口はテンプレート直下から別の出力先へ生成する。既定は実行年と直前5年。保存原本を使う再生成では外部取得を行わない。

```sh
node scripts/create-world.mjs --out generated/world
node scripts/serve.mjs --dir generated/world/site --port 4173
node scripts/create-world.mjs --source-dir generated/world/raw --out generated/world-replay
node scripts/create-central-america.mjs --source-dir generated/world/raw --out generated/central-america
npm run collect:census:central-america -- --out .work/central-america-census-YYYY-MM-DD
npm run collect:census:honduras-municipal -- --root .work/central-america-census-YYYY-MM-DD
python scripts/inspect-census-workbooks.py --root .work/central-america-census-YYYY-MM-DD
npm run extract:census:central-america -- --root .work/central-america-census-YYYY-MM-DD
node scripts/create-central-america.mjs --source-dir generated/world/raw --census-data .work/central-america-census-YYYY-MM-DD/normalized-census.json --out generated/central-america-with-census
# 取得原本を使わず、保存済みの正規化版から再生成する場合
node scripts/create-central-america.mjs --source-dir generated/world/raw --census-data data/census/central-america-population-v0.7.json --census-history-data data/census/central-america-census-history-v0.9.json --un-population-data data/international/un-wpp2024-central-america-population.json --out generated/central-america-replay
```

国勢調査原本の収集コマンドは、登録済みの公式HTTPS URLだけを取得し、ファイル署名・容量・リダイレクト先を検査してSHA-256付き`receipt.json`を作る。現在のmanifestは7か国12資料、別のHonduras取得器は公式WordPress台帳から298自治体PDFを発見・重複排除して保存する。`--reuse <以前の取得ディレクトリ>`でハッシュ一致原本を再利用できる。原本の再配布可否、表・変数の採用、地理コード・境界との対応は別の審査であり、取得成功だけでサイトへ値を入れない。[再利用用の正規化人口データ](data/census/README.md)は原本を含まず、出典・ハッシュ・年・方法・不整合を保持する。国勢調査比較表では`Census 年`を各国の公式Censusページへリンクし、統計機関名と採用表を別に表示する。0.9では採用データ年と直近約3回の調査年を別台帳にし、世界位置図では採用データ年が新しい国を濃い緑、10年以上前を薄赤、未収録国を灰色で示す。実施・準備情報だけで採用年を更新しない。[UN WPP人口系列](data/international/README.md)は、異なる国勢調査年の合計と同一年の国連推計・中位予測を混同せず併記する。Public化前に`terms_review_required`の利用条件を確認する。

地方データと資料を`data/dashboard.json`へ統合した後は、テンプレートから次を実行します。

```sh
node scripts/validate-country.mjs --project ../uganda-dashboard
node scripts/build-country.mjs --project ../uganda-dashboard
npm run sources:plan -- --country UGA
```

生成器が管理する`site/`のコードを直接編集する場合、再構築で戻ることに注意してください。恒久的な国別変更は、国別アダプター・設定と、案件用に管理した生成コードへ反映します。テンプレート本体に一国のデータを混ぜません。

生成サイトにはApache／LiteSpeedで`.mjs`をJavaScriptとして配信するための`.htaccess`を含める。別のWebサーバーでは、同等のMIME type設定をホスティング側へ適用する。

## GitHub Actionsでの生成

`Build country baseline`を手動実行し、`country`に国名またはISOコードを入力すると、初期収集・サイト・証拠をArtifactとして保存します。自動のWeb公開や、AIによる国内資料調査までは行いません。国内公式資料の調査は、新しいAI案件が[国別作業手順](docs/COUNTRY_AGENT_WORKFLOW.md)に沿って続けます。

Artifactは７日間保存します。必要な成果は案件側へ取得してください。取得先の障害や対象国のデータ状況によって収集範囲は変わります。

## 構成と検証

```text
START_HERE.md             新しいAI案件の入口
lib/                     収集、検証、生成、CLI共通処理
scripts/                 初期生成、再構築、検証、ローカル配信
config/                  世界の所属・指標・参照境界設定、取得検証receipt
data/census/              再生成用の出典付き正規化国勢調査データ
scaffold/site/           DDPT型画面の共通実装
prompts/                 国名だけで始める依頼文
docs/                    共通仕様、国別適応、公式資料収集手順
templates/               記入様式、受入試験、設計用設定一覧
references/              元のユーザビリティレビュー
tests/                   欠測、地域状態、出典、出力、取得障害等の回帰検査
.github/workflows/       Windows/LinuxのCIと国別初期生成
```

```sh
npm run check
npm test
```

CIはWindows/Linux、Node 22/24で検証します。初期収集の結果は[0.2検証記録](docs/VALIDATION_v0.2.md)、上位再選択等は[0.2.1検証記録](docs/VALIDATION_v0.2.1.md)、計画・資料機能は[0.3検証記録](docs/VALIDATION_v0.3.md)、世界入口・指標別内部比較・診断出力は[0.4検証記録](docs/VALIDATION_v0.4.md)、共通sourceと国別所在台帳は[0.4.1検証記録](docs/VALIDATION_v0.4.1.md)、中米7か国・完全被覆集計・MariaDB基礎は[0.5検証記録](docs/VALIDATION_v0.5.md)、ベリーズ・グアテマラ国勢調査の実収集と部分統合は[0.6検証記録](docs/VALIDATION_v0.6.md)、7か国の公式人口・国内階層・混合基準年集計は[0.7検証記録](docs/VALIDATION_v0.7.md)、UN人口比較・国勢調査リンク・3言語UIは[0.8検証記録](docs/VALIDATION_v0.8.md)、Census採用年地図・調査履歴は[0.9検証記録](docs/VALIDATION_v0.9.md)、国別制作の完成工程は[0.9.1検証記録](docs/VALIDATION_v0.9.1.md)、独立完成監査工程は[0.9.2検証記録](docs/VALIDATION_v0.9.2.md)、アメリカ大陸版は[0.10検証記録](docs/VALIDATION_v0.10.md)に保存します。42の受入シナリオは案件の採用範囲に応じて検証し、シナリオの追加を合格件数と扱いません。

## 維持するモデル

### 世界国勢調査データベースのOSS構想

[世界国勢調査DBのOSS機能要件](docs/WORLD_CENSUS_DATABASE_SPEC.md)を採用した。既存のIPUMS等との機能重複を除外理由にせず、検索、変数辞書、表の作成、抽出カート、図表・地図、API、再現パッケージ、境界履歴、自営・共同更新など23機能を実装順付きで整理している。これは設計要件の追加であり、新DBの実装完了を意味しない。コードのOSS化予定と資料別の再配布条件を分け、現在のリポジトリはPrivateのままとする。DBの研究機能とDDPTの通常画面への採用は区別する。

[AreaDataのサービス構成](docs/AREADATA_ARCHITECTURE.md)は、当面`areadata.net/`、`/database/`、`/planning/`へ三機能を集約する。国別・国内地域診断の主系列は[国勢調査系列契約](docs/CENSUS_SERIES_CONTRACT.md)に従い、同一年の国際参照系列と分ける。MariaDB基礎schemaは`database/mariadb/001_schema.sql`。WorldCensus／AreaPlanの別ドメインと公開APIは中米試作後に検討する。[旧Good Government案](docs/GOOD_GOVERNMENT_ARCHITECTURE.md)は経緯として保持する。

### 国別の計画・診断

国勢調査を地方計画の基礎へ使う手順を追加した。[計画制度から国勢調査・分野別資料へつなぐ方法](docs/PLANNING_CENSUS_METHOD.md)は、法定計画主体の地域を先に定め、国勢調査の不足を省庁別資料で補い、診断・要求・事業・草案をつなぐ。[ラテンアメリカ20か国の国勢調査・計画制度レポート](docs/research/latin-america-2026/REPORT.md)には調査年、テーマ項目、粒度、法令・制定年・機関と未確認事項を記録した。これは調査と方法の追加であり、20か国の数値収集アダプターの実装完了を意味しない。

共通化するのは「地域から総合的に読む」「テーマから地域間を比べる」の役割、地域選択の連動、出典・対象範囲・取得操作です。国別制度、指標、言語、粒度、頻度、図表・提供機能は根拠に応じて適応します。

[ウガンダ2案件の14教訓](docs/research/uganda-lessons-2026-09-14.md)を国別作業手順へ反映した。原資料の全項目棚卸し、付表・地域報告書の探索、代表地域での事前確認、同じ上位への再選択、計画様式の必要欄、実出力と性能を[12観点の補助確認票](templates/COUNTRY_LESSON_AUDIT.md)で確認する。AIが案件ごとの証拠と判定を記入する手順であり、12観点の自動検査実装や合格を意味しない。

[Census Dashboard Kitから得た国別制作・独立監査工程](docs/research/census-dashboard-kit-country-lessons-2026-09-17.md)も国別作業手順へ反映した。公式資料目録の全件処置、原表の全数値列、6分野、地域コード・境界、計画制度、実出力を閉じ、別担当が[独立完成監査](templates/INDEPENDENT_AUDIT.md)で原資料・意味・最新年・比較集合・実出力を確認してから公開する。Public KitのJICA対象142か国preflightと監査手順は[commit・hash固定の外部台帳](config/external-source-registries.json)から参照する。国別通常画面の指標別最新版と、世界・広域・研究DBの期間・履歴は役割を分ける。0.10では地域版にも専用の受入票・独立監査票・公開ゲートを実装した。国別Wordのdelivery gateは依然としてCensus Dashboard Kit側の機能である。

[DDPT・ウガンダ公開版の3ページ比較](docs/research/ddpt-uganda-template-comparison-2026-09-14.md)では、ユーザビリティと国別制作の容易性、共通図表、計画資料、投資情報の段階的な搭載を検討した。2026-09-14の公開画面と実装構造に基づく提案であり、共通UXの採用決定や実装変更ではない。

[AI契約・実行環境・再現性の要求仕様案](docs/AI_ENVIRONMENT_REQUIREMENTS.md)は、Public配布を想定したGoogle Antigravity（Gemini）／Claude Code／Codexの最低契約、推奨環境、共通の受入条件をまとめた。料金・条件は2026-09-14の公式情報。個人向けGemini CLI終了の移行告知に基づきGoogleの入口を訂正した。3製品での比較制作試験とリポジトリのPublic化は未実施。

Google AI Proを使う初心者向けには、[Geminiで作る開始手順](docs/GET_STARTED_WITH_GEMINI.md)にAntigravityアプリの初回設定、必要ソフトの導入もAIへ任せる開始プロンプト、再開方法を記載した。新規PCでの一連の実機試験は未実施。

- [共通デザイン・機能仕様C01～C07](docs/02_COMMON_SPEC.md)
- [国別設定とデータ条件](docs/03_COUNTRY_AND_DATA.md)
- [公式資料のアダプター追加](docs/SOURCE_ADAPTER_GUIDE.md)
- [DDPT参照版](docs/01_DDPT_REFERENCE.md)・[ウガンダの教訓](docs/UGANDA_LESSONS.md)
- [添付レビュー９所見](docs/REVIEW_TRACEABILITY.md)・[42の受入シナリオ](templates/ACCEPTANCE.md)

既知のF01～F03（地域引き継ぎ、文書取得、集計定義・基準日）の解消を確認してから、改善後の共通UX v1.0を採用します。実行テンプレート0.4での生成と、その採用判断・各国の実利用者による受入は分けて扱います。

このリポジトリはPrivateの再利用テンプレートです。取得データ・境界・第三者資料には、それぞれの出典に記録した利用条件が適用されます。
