# タイ国別版・開始シート（AI記入、2026-09-27）

`templates/COUNTRY_START.md`に対応。アジア50件の段階3・東南アジア、国ID `THA`。独立したignored候補は `generated/thailand-areadata-20260927`。**2024年暫定GPPの省別部分成果・未公開**。[原本監査](thailand-nesdc-gpp2024-source-audit-2026-09-27.md)を参照。

| 項目 | 採用・確認 | 不足・次の行動 |
|---|---|---|
| 納品と場所 | AreaData branch `codex/asia-domestic-20260926` に再現用コード、公式source所在、監査・検証台帳を保存。原本とsiteはignored候補。 | 独立`ACCEPT`、THA固有のHosting/Public先、運用者、更新周期は未設定。DDPT先を転用しない。 |
| 仕様・利用者 | 共通0.4参照実装、dataset schema 0.2。省別経済診断と現行計画資料の収集を想定。 | UX v1.0最終採用、タイの実務担当、タイ語UI・端末/回線条件、法定業務での受入は未確認。 |
| 国内統計 | NESDC 2024p公式Excelから全国＋77省のGPP、GPP人口分母、1人当たりGPP、21産業指標、計24指標・1,872直接観測。全国＋7経済地域＋77省の2,210セルを照合。 | 1995–2023年、CVM、cluster等は意味監査待ち。NSO 2025国勢調査確報とBORA登録人口の原本未取得。Kam Phaeng Phet詳細表人口の矛盾は保留。 |
| 地理・コード | 原表77省の経済報告行をNESDC時点付きIDで保持。7経済地域は監査専用。 | DOPA公式行政コード・境界版・適合図形と法定計画管轄の照合。旧2017年provider図形は不採用。 |
| 計画主体・資料 | NESDC省/省cluster計画資料目録と6頁の草案表示付きガイドを取得。Chiang Mai計画・進捗の公式所在を確認。 | 現行法的効力・発行主体、現地計画本文、予算・支出・実施・評価の取得。Chiang Mai PDFはtimeoutし、地域資料としては未採用。 |
| 国際共通source | 初期WDI全国系列を国内NESDC各指標と分離。取得失敗はfailedとして保持。 | HDX、UNHCR、DTM、IPC、MICS、DHS、WorldPop等のTHA年・テーマ・粒度別availability未確認。 |
| 原本・利用条件 | NESDC Excel 2,220,131 bytesをhash固定。4つのNESDC原本/目録receiptを保存。 | 公的統計の再配布条件、未採用表の採否、42シナリオ、独立監査。 |

代表確認は全国、Khon Kaen、Chiang Mai、Phuket、Bangkok。画面でChiang Mai→全国→Chiang Mai→全国の見出し・URL・GPP値切替と省内下位行なしを確認。全国の24指標×77件は出力で初末行・値・出典を照合。狭画面、低性能端末、Word/PDF、タイ語と現地利用者確認は未実施。
