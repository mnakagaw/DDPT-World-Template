# ミャンマー国別版・開始シート（AI記入、2026-09-27）

`templates/COUNTRY_START.md`に対応。アジア50件の段階3・東南アジア、国ID `MMR`。独立したignored候補 `generated/myanmar-areadata-20260927`。**DOP 2024国勢調査の州・地域別部分成果・未公開**。[原本監査](myanmar-dop-census2024-source-audit-2026-09-27.md)参照。

| 項目 | 確認した範囲 | 不足・次の行動 |
|---|---|---|
| 納品と場所 | AreaData branch `codex/asia-domestic-20260926` に再現用コード・監査・source所在を保存。原本とsiteはignored候補。 | 独立`ACCEPT`、MMR専用Hosting/Public先、運用者、更新周期は未設定。DDPT先を転用しない。 |
| 仕様と利用者 | 参照実装0.4、dataset schema 0.2。全国と15州・地域等の2024人口内訳を診断・比較する。 | UX v1.0最終採用、現地実務担当、ビルマ語UI、低帯域端末、計画業務の受入は未確認。 |
| 国内統計 | DOP 2024本報告書とExcel原本の全国＋15地域、15指標・240観測。全19 sheetと数値列を棚卸し。 | A-2～A-18の意味監査、他分野Excel、2014との比較条件。推計混在を実測と呼ばない。 |
| 地理・コード | DOP Table A-1の15報告行を出典行IDで保持。State/Region/Nay Pyi Tawを区別。 | 2024の公式コードと適合図形、District/Township階層。2019 geoBoundaries 14図形は不採用。 |
| 計画主体・資料 | FY2026-27 national/local planning coordination公式記事の本文を取得。 | 法的計画主体・義務、現行の選択地域の計画/予算/支出/実施/評価本文・様式は未取得。 |
| 国際共通source | 初期WDI全国系列をDOP国勢調査から分離。 | HDX、UNHCR、DTM、IPC、MICS、DHS、WorldPop、SALB等のMMR・テーマ・年・粒度別availability未確認。 |
| 原本・利用条件 | DOP Excel、本報告PDF、別版の暫定PDF、計画調整HTMLをbytes/hash固定。 | 再配布条件、他表採否、42シナリオ、独立監査。 |

代表確認は全国、Chin（推計92.2%）、Yangon（推計0%）、Bago（推計12.9%）、Nay Pyi Taw（特別型）。帳票5件は原表と照合し、画面ではChin→Yangon→全国の見出し・URL・値、資料の未取得表示、15地域の推計率順位を確認した。狭画面・全印刷ページ・現地利用者の検証は未実施。
