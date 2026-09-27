# Brunei Darussalam 国別候補・開始シート（AI記入、2026-09-27）

`templates/COUNTRY_START.md`に対応。アジア50件の段階3・東南アジア、`BRN`。独立・ignored候補 `generated/brunei-areadata-20260927`。**2021年国勢調査の地方統計を一部接続した未公開候補**。[原本監査](brunei-bpp2021-source-audit-2026-09-27.md)と[Task Contract](brunei-task-contract-2026-09-27.md)を参照。参照実装0.4、dataset schema 0.2であり、UX仕様v1.0の最終採用ではない。

| 項目 | 確認した範囲 | 不足・次の行動 |
|---|---|---|
| 作業・納品 | AreaData `codex/asia-domestic-20260926`に再実行コード、公式source台帳、監査・検証記録を保存。原本とbuildはignored候補。 | 独立`ACCEPT`、BRN専用Hosting/Public先、現地実務・更新担当、再配布条件は未設定。 |
| 地域・統計 | DEPS BPP 2021の全国、4 District、39 Mukimの報告行を接続。11指標・367地方国勢調査観測（352公表セル、15年齢群算出）。全国B1人口440,715人。 | Kampung行、残り23付表と本報告の数値列・意味は未審査。2011年欄を2021年と時系列比較しない。 |
| 公式地理 | 統計表の親子関係・全件数を照合。Districtを計画の対象名、Mukimを内部診断の粒度と区別。 | 公式コード、2021年対応図形、現行版と村の対照未取得。初期の2011年geoBoundaries図形を除外し、統計表の名称に基づく暫定IDのみ使用。 |
| 制度・資料 | [Cap.248 Town and Country Planning Act改訂2022](https://www.agc.gov.bn/documents/town-and-country-planning-act/)本文、[MOF RKN12](https://www.mof.gov.bn/ndpo_general-information/)本文を取得。[JPBD目録](https://www.jpbd.gov.bn/buku-garispanduan-dan-master-plan/)で4 District Planの所在を確認。Planning AuthorityとMinisterの役割を分け、Mukim独自の法定計画を推定しない。 | District Plan本文・図面・版・告示・承認、地域別の予算見込・実支出・実施・評価は未取得。RKN12の2026–2045計画プロジェクト欄は完成の証明ではない。 |
| 国際source | 初期WDI全国系列は年央推計などの別系列として保持。2021国勢調査人口をWDI 2021/2025年推計と接合しない。 | HAPI/UNHCR/DTM/IPC/MICS/DHS/WorldPop/GHSL/SALB/WaPORのBRN×テーマ×年×地方粒度のavailabilityは未調査。 |
| 利用条件 | 公式PDF6件のbyte長・SHA-256を固定。Gitに原本PDFを入れない。公開サイトは作らない。 | 各機関の二次利用・再配布条件を確認する。 |

代表確認は全国、Brunei Muara（18 Mukim）、Belait、Temburong（小規模District）、Kianggeh（年齢群欠測）、Melilas（人口29・一時居住者0）。6地域の診断CSV/HTML/Markdown、計画HTML、根拠CSVを原PDFの転記値と照合。ブラウザーでDistrict→Mukim→同じDistrict全体の再選択、URL・見出し・主値、親計画目録の地域限定を確認した。狭幅、全頁印刷、現地利用者、42シナリオ全件と独立監査は未実施。
