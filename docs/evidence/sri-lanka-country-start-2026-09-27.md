# スリランカ国別版・開始シート（AI記入、2026-09-27）

`templates/COUNTRY_START.md`に対応。アジア50件の段階2南アジア、`LKA`。新規ignored候補は`generated/sri-lanka-areadata-20260927`。**部分成果・未公開**。[原本監査](sri-lanka-cph2024-source-audit-2026-09-27.md)を参照。

| 項目 | 採用・確認 | 不足・次の行動 |
|---|---|---|
| 納品と場所 | AreaData branch `codex/asia-domestic-20260926`にコード・台帳・公開可能な公式source所在を保存。原本とsiteは別のignored国別ディレクトリ。 | 独立`ACCEPT`、国別Hosting/Public先、現地担当者と更新頻度。DDPT公開先は転用しない。 |
| 仕様 | 共通実装0.12.1、dataset schema 0.2。既存の地域診断・テーマ診断・DB・計画資料を保持。 | UX v1.0最終採用、現地語と運用者による受入。 |
| 国内統計 | DCS 2024 CPH確報のA5/A14/A16の30直接指標、10,989直接観測。全国・9州・25郡・340 DS。全国人口21,781,800。WDI全国系列は別。 | 取得済み残り20番号表・9 GN表・報告書残りの数値列/意味監査、優先テーマ。GN暫定年齢値は8 DSで確報と差。 |
| 地理・コード | 公式コードとGN原本14,008キー一致。340 DSは人口/男女値と郡で一意に対応、うち16名称差。 | 同版の公式polygon、コード台帳の境界時点、地方政府areaとの対応。DSを自治体と扱わない。 |
| 計画主体 | Municipal/Urban Councils、Pradeshiya SabhasとDS統計地域の区別を明示。自治体予算規則のGazette所在のみ確認。 | 現行法・適用範囲、対象自治体の採択計画、予算本体、支出、実施と公式評価、様式。Colombo市資料をColombo DSへ付けない。 |
| 国際共通source | WDI全国系列は初期生成で取得。 | 他国際sourceの国・テーマ・年・粒度別availabilityと国内地理対応を未確認。所在・取得・照合・採用を別管理。 |
| 利用条件と公開 | DCS公開XLSX/PDFのURL・bytes・hash、採用セル/頁を台帳化。 | 再配布条件、全42シナリオ、独立監査、Hosting/Public先。候補未公開。 |

代表確認は全国、Western州、Colombo郡、Colombo DS、Kesbewa DS。実画面で同じ上位郡の選び直しと郡/DS値切替、8実出力例を確認。Word/PDF描画、狭画面、全地域型、現地利用は未実施。
