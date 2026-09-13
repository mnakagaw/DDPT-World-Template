# DDPT参照モデルの採用候補

状態：**ドラフト／ソースで確認した基準候補**。DDPTの全画面・全挙動をそのまま正解として認定する資料ではない。利用者が評価する導線を残し、既知の不具合を除き、国別データに適応するための参照資料である。

## 1. 確認範囲と基準版

- 確認日：2026-09-13。
- GitHub：`mnakagaw/DDPT-TOP`。初回参照版はmain `6d2aee5f767515c5b20118ed642f832f21a15151`。修正適用の連絡後にも `git ls-remote` とGitHub APIを読み取り、**mainは同じSHAのまま**と確認した。
- 修正を含む別ブランチ `codex/usability-20260913` の先頭は `18cd962806c1342329c12bb376b42cde4afeb246`。新しい参照候補として初回mainと区別する。以下の構造説明のソースリンクは初回main、直下の追記は修正ブランチの固定コミットを参照する。
- `X:/Codex/DDPT-TOP` のローカル作業ブランチは `codex/ddpt-auto-update-status`、HEADは `bbde7bf976b293ae49d9bea77a3e71f8f20c55ef`。多数の変更が残るため、現在のGitHub基準版と区別した。読み取り監査中に編集・checkout・commit・公開は行っていない。
- 初回はブラウザー接続等の制約で公開画面を再検証できなかった。その後、担当エージェントが公開デスクトップ画面でF01の原再現経路と章ナビゲーションの存在を確認した。確認範囲と残件は直下に記録する。公開ファイルのSHAと修正ブランチの同一性を検証したという意味ではない。
- 2026-09-12の利用性評価と、本資料のソース確認は証拠の時点・種類を分ける。課題の採否は [REVIEW_TRACEABILITY.md](REVIEW_TRACEABILITY.md)、ウガンダ移植の経緯は [UGANDA_LESSONS.md](UGANDA_LESSONS.md) で追跡する。

### 修正適用後の再確認（2026-09-13）

GitHub比較では修正ブランチがmainより9コミット先行し、後退はない。うち7件は9月4～5日の既存修正で、今回の新規変更は [f44bf4a（地域導線・根拠表示）](https://github.com/mnakagaw/DDPT-TOP/commit/f44bf4a6de5e31c9986a26b8d003cdd59ea9b82e) と [18cd962（新FTPS資産の事前不存在確認）](https://github.com/mnakagaw/DDPT-TOP/commit/18cd962806c1342329c12bb376b42cde4afeb246)。mainへ取り込み済みとは扱わない。

| 所見 | 修正ブランチで確認したもの | 今回の公開確認 |
|---|---|---|
| F01 地域の引継ぎ | 国・階層・地域IDのURL生成、地域解決、不明地域の説明、reload/popstate用の回帰試験 | **原再現経路は合格**。テーマ画面で「19. Valverde 173 centros」を選択→「Ver diagnóstico territorial」→県全体のValverdeを保持した |
| F02 Word取得入口 | 未認証時の「Iniciar sesión y descargar Word」と取得条件、認証後用ラベルの切替 | 未認証・認証復帰・実Word本文の確認は未完了。今回使えた既存セッションはORPであり、匿名検証の代用にしない |
| F03 件数・基準日の説明 | PMD公式根拠・CDM自身の確認根拠を共通集計。ソースデータを再計算して162自治体／PMD42／CDM71、overviewの42／71との一致を確認。投資の固定版は日付と差の理由を表示 | ページ間の実表示・全地域・Wordとの照合は未完了 |
| F04 章移動 | 章リンク・検索・現在位置の実装 | 公開地域診断に「Capítulos del diagnóstico」、検索、章アンカーが存在することを確認。代表利用者の操作試験までは未実施 |

F01の遷移先は [Valverde県全体の診断](https://prodecare.net/viplan/ddpt/diagnostico-territorial/?pais=do&nivel=provincia&territorio=do-prov-27)。確認時の見出しは「Diagnóstico Territorial – Provincia de Valverde」、選択欄はCibao Noroeste／Valverde／Valverde（provincia completa）だった。全205地域scopeの試験コードが存在することと、今回その全件を実行したことは区別する。

修正の根拠：[採否台帳](https://github.com/mnakagaw/DDPT-TOP/blob/18cd962806c1342329c12bb376b42cde4afeb246/docs/USABILITY_REVIEW_20260913.md#L7-L17)、[F01 URL契約](https://github.com/mnakagaw/DDPT-TOP/blob/18cd962806c1342329c12bb376b42cde4afeb246/modules/shared/territorialSelection.js#L5-L50)、[F01回帰試験](https://github.com/mnakagaw/DDPT-TOP/blob/18cd962806c1342329c12bb376b42cde4afeb246/modules/dashboard-territorial/src/context/territorialNavigation.test.jsx#L20-L35)、[F02県計画リンク](https://github.com/mnakagaw/DDPT-TOP/blob/18cd962806c1342329c12bb376b42cde4afeb246/modules/planificacion-provincial/src/App.jsx#L151-L174)、[F03共通集計](https://github.com/mnakagaw/DDPT-TOP/blob/18cd962806c1342329c12bb376b42cde4afeb246/scripts/lib/observatory-planning.mjs#L10-L36)。これを改善後の参照候補へ追加するが、世界共通UX v1.0の採用完了とはしない。

## 2. ページの目的と保持候補

| ページ系統 | 確認した目的・操作・配置 | 世界版で保持する候補 | 国別に決めるもの |
|---|---|---|---|
| ポータル | 診断、公共投資、地域計画、地域需要の入口を分ける。診断内でも地域から入る画面とテーマから入る画面を説明している | 利用目的別の入口と、各入口から得られる成果を明示する | モジュールの有無、説明、名称、公開可能範囲 |
| 地域診断 | 一つの地域について複数分野を続けて読む。上部は左に階層選択と基本指標、右に地図。その下に分野別の図表、比較、診断文章が続く | 地域を選ぶ→地域全体を読む→比較・計画材料へ進む流れ。地図と選択欄の同期 | 地域階層数、名称、初期選択、指標、時点、比較対象、分野構成 |
| テーマ別診断 | 地理レベル・テーマ・指標・期間を選び、全国要約、地図と地域検索・順位・詳細、分布、条件を満たす時系列を読む | 同じ指標・期間・単位で地域間を比較し、選択地域から地域診断へ進める | 使えるレベル・期間、分類・色、比較可能性、全国値の定義 |
| 市町村計画 | 計画・草案・協議体・計画担当組織の状態を地図で切替。地域選択後に詳細やWord/PDF資料へ進む | 状況を俯瞰→対象を選択→根拠・作業資料を開く | 計画制度、承認状態、担当組織、文書名称、公開権限 |
| 県・地域計画 | 地図と対象選択、診断・公共投資・需要の要約、関連資料への導線。診断→投資→需要→計画策定の順序を説明 | データを計画策定の材料につなぐこと。草案と公式計画の区別 | 行政・計画単位、参加主体、策定手順、予算、資料様式 |
| 公共投資・需要 | 投資は執行・年度予算・複数年計画を入口で分ける。需要には利用可能な階層と準備中の階層がある | 異なる情報の意味を混ぜず、利用可能な機能を明示する | 投資制度、会計年度・通貨、事業の地域配分、需要収集方法 |

根拠：ポータル [PortalApp.tsx:170–284](https://github.com/mnakagaw/DDPT-TOP/blob/6d2aee5f767515c5b20118ed642f832f21a15151/app/PortalApp.tsx#L170-L284)、需要 [同:287–315](https://github.com/mnakagaw/DDPT-TOP/blob/6d2aee5f767515c5b20118ed642f832f21a15151/app/PortalApp.tsx#L287-L315)。投資・需要の記述はここでは入口仕様の確認であり、各モジュールの機能全体を監査したものではない。

地域診断の上部は [TopSelectionAndMap.jsx:50–150](https://github.com/mnakagaw/DDPT-TOP/blob/6d2aee5f767515c5b20118ed642f832f21a15151/modules/dashboard-territorial/src/components/TopSelectionAndMap.jsx#L50-L150)、地図から階層を同期する処理は [DashboardContext.jsx:37–60](https://github.com/mnakagaw/DDPT-TOP/blob/6d2aee5f767515c5b20118ed642f832f21a15151/modules/dashboard-territorial/src/context/DashboardContext.jsx#L37-L60)、下部の構成は [App.jsx:195–342](https://github.com/mnakagaw/DDPT-TOP/blob/6d2aee5f767515c5b20118ed642f832f21a15151/modules/dashboard-territorial/src/App.jsx#L195-L342)。

テーマ画面は [ThemeAnalysisDashboard.jsx:250–286](https://github.com/mnakagaw/DDPT-TOP/blob/6d2aee5f767515c5b20118ed642f832f21a15151/modules/dashboard-tematico/src/components/ThemeAnalysisDashboard.jsx#L250-L286)、URLでテーマ・指標・地域を渡す処理は [App.jsx:163–222](https://github.com/mnakagaw/DDPT-TOP/blob/6d2aee5f767515c5b20118ed642f832f21a15151/modules/dashboard-tematico/src/App.jsx#L163-L222)。

市町村計画の状態レイヤーは [PortalApp.tsx:147–218](https://github.com/mnakagaw/DDPT-TOP/blob/6d2aee5f767515c5b20118ed642f832f21a15151/modules/planificacion-municipal/app/PortalApp.tsx#L147-L218)、詳細と資料は [同:1316–1451](https://github.com/mnakagaw/DDPT-TOP/blob/6d2aee5f767515c5b20118ed642f832f21a15151/modules/planificacion-municipal/app/PortalApp.tsx#L1316-L1451)。県・地域の策定手順は [県App.jsx:540–548](https://github.com/mnakagaw/DDPT-TOP/blob/6d2aee5f767515c5b20118ed642f832f21a15151/modules/planificacion-provincial/src/App.jsx#L540-L548)、[地域App.jsx:374–381](https://github.com/mnakagaw/DDPT-TOP/blob/6d2aee5f767515c5b20118ed642f832f21a15151/modules/planificacion-regional/src/App.jsx#L374-L381)。

## 3. デザインの抽出単位

DDPTには既に複数の画面系統がある。「DDPTと同じ」を一つの色・カード・サイドバーの指定だけで表現しない。

- ポータル：濃紺のヘッダー、緑の地域コンテキスト、白系背景、セマンティックな色変数、Segoe UI等の文字。実値は `--navy-950: #041d37`、`--green-700: #008467`、`--ink: #0b203a` など。[globals.css:3–35](https://github.com/mnakagaw/DDPT-TOP/blob/6d2aee5f767515c5b20118ed642f832f21a15151/app/globals.css#L3-L35)、[同:58–129](https://github.com/mnakagaw/DDPT-TOP/blob/6d2aee5f767515c5b20118ed642f832f21a15151/app/globals.css#L58-L129)
- 地域診断：淡い背景、中央の読み進める領域、分野別カード、上部二列。画面と印刷で構成を切り替え、印刷・PDFボタンを持つ。[App.jsx:136–173](https://github.com/mnakagaw/DDPT-TOP/blob/6d2aee5f767515c5b20118ed642f832f21a15151/modules/dashboard-territorial/src/App.jsx#L136-L173)
- テーマ別診断：フィルターと要約を先に置き、大画面では地図と地域探索を横に並べる。地域プロフィールの画面とは情報の主従が異なる。[ThemeAnalysisDashboard.jsx:269–286](https://github.com/mnakagaw/DDPT-TOP/blob/6d2aee5f767515c5b20118ed642f832f21a15151/modules/dashboard-tematico/src/components/ThemeAnalysisDashboard.jsx#L269-L286)

国別変更では、色・ロゴ・言語と、操作順序・選択の意味・情報の主従を別項目として記録する。後者を変える場合は変更理由と利用者への影響を示す。ピクセル値や自動初期選択まで、無条件の不変条件にはしない。

## 4. 再利用できるデータ契約とドミ共依存

テーマデータには `meta / themes / indicators / sources / territories / coverage / observations` が存在する。観測は指標・期間・地域レベル・地域IDの組で一意となる。指標には単位、出典、集約方法、値の方向、使える期間・階層がある。観測には値、分子・分母、対象日、coverage、quality_flag等が含まれる。[theme-analysis.json](https://github.com/mnakagaw/DDPT-TOP/blob/6d2aee5f767515c5b20118ed642f832f21a15151/modules/dashboard-tematico/public/data/theme-analysis.json)、[検証コード:69–89](https://github.com/mnakagaw/DDPT-TOP/blob/6d2aee5f767515c5b20118ed642f832f21a15151/modules/dashboard-tematico/scripts/verify_theme_analysis.mjs#L69-L89)

| 共通化の対象 | 国別に外へ出す設定・データ |
|---|---|
| 地域ID、親子関係、境界データと値の結合 | `do-reg-* / do-prov-* / do-mun-*`、地域階層名、地域数、行政改編、境界版 |
| 指標・観測・出典・coverageの分離 | 指標体系、単位、定義、出典組織、収集方法、更新頻度、観測時点 |
| 集約方法と比較の条件 | 合計・加重平均・率の分母、対象範囲、重複除去、境界変更時の比較可否 |
| 欠測をゼロと区別し、出典・粒度を表示 | 欠測理由、利用できる階層・期間、適用除外、品質基準 |
| 読込・エラー・任意データの取り扱い | 配信URL、API/静的JSON、認証、公開制限 |
| 計画・草案・承認・資料への導線 | END、PMD/PPD/PRD、CDM/CDP/CDR、OMPP、法律、国家計画との対応 |

現行の検証には「10地域・32県・158診断市町村」や `do-` IDを直接検査する箇所がある。これは世界共通の要件ではない。[verify_theme_analysis.mjs:50–58](https://github.com/mnakagaw/DDPT-TOP/blob/6d2aee5f767515c5b20118ed642f832f21a15151/modules/dashboard-tematico/scripts/verify_theme_analysis.mjs#L50-L58)、[同:73–80](https://github.com/mnakagaw/DDPT-TOP/blob/6d2aee5f767515c5b20118ed642f832f21a15151/modules/dashboard-tematico/scripts/verify_theme_analysis.mjs#L73-L80)

地域診断の読込は多数の分野別JSONとドミ共固有パスを持つ。API/静的配信を分ける入口は再利用できるが、そのまま汎用スキーマとして固定しない。[useDataLoader.js:13–55](https://github.com/mnakagaw/DDPT-TOP/blob/6d2aee5f767515c5b20118ed642f832f21a15151/modules/dashboard-territorial/src/hooks/useDataLoader.js#L13-L55)

## 5. 既存の開発標準を継承する範囲

既存の [AI協働開発標準 v1.0（2026-09-01）](https://github.com/mnakagaw/DDPT-TOP/blob/6d2aee5f767515c5b20118ed642f832f21a15151/docs/AI_ASSISTED_DEVELOPMENT_STANDARD_JA.md) は今回の基準コミットに存在する。

Task Contract→基準版記録→作業分離→受入条件→最小実装→検証→独立レビュー→GitHub→公開計画→適用→公開確認、という工程を継承する。今回の追加点は、入口の契約に**参照画面、保持する操作、許可する国別差分、変更理由、受入シナリオ**を持たせることである。[Task Contract:118–139](https://github.com/mnakagaw/DDPT-TOP/blob/6d2aee5f767515c5b20118ed642f832f21a15151/docs/AI_ASSISTED_DEVELOPMENT_STANDARD_JA.md#L118-L139)、[基準記録:141–167](https://github.com/mnakagaw/DDPT-TOP/blob/6d2aee5f767515c5b20118ed642f832f21a15151/docs/AI_ASSISTED_DEVELOPMENT_STANDARD_JA.md#L141-L167)

観測期間と取得日を分け、欠測・対象外・ゼロを分け、利用者が指定した歴史時点を勝手に最新化しない規則も継承する。[Data dashboard:321–328](https://github.com/mnakagaw/DDPT-TOP/blob/6d2aee5f767515c5b20118ed642f832f21a15151/docs/AI_ASSISTED_DEVELOPMENT_STANDARD_JA.md#L321-L328)

FTPSはDDPTの配備方式であり、全ての国に強制する共通仕様ではない。コミットと公開物の対応、変更パスの限定、競合確認、復旧、公開後の実証を共通要件とし、配備手段は国別に決める。

## 6. 基準版の採用前に残る作業

1. DDPTと対象国の主要操作を、同じ利用目的・画面幅で実際に比較する。
2. 保持する挙動、国の事情で変更する挙動、既知の不具合として除く挙動を明示する。
3. 空・欠測・エラー・地域変更・期間変更・地図選択・戻る操作・印刷を受入シナリオにする。
4. 採用した画面・操作・ソース版を基準として固定する。ソース上の存在だけで利用性検証の合格にしない。

この段階では、既知の不具合、未検証の表示、ドミ共固有の数値・法律・組織を共通テンプレートの必須仕様として採用しない。
