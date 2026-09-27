# Thailand country lesson audit — producer-side partial check

2026-09-27 JST、branch `codex/asia-domestic-20260926`、ignored候補 `generated/thailand-areadata-20260927`、dataset SHA-256 `c2cb0894b0070f68636dc8d502e6ad6e0de3669db8487b7508cbe253b4b9615c`。5例の出力hash・初末行は候補の `evidence/THA_IMPORT_RESULT.json`、`OUTPUT_VERIFICATION.json` に保存。Windows/PowerShell、Node preview `127.0.0.1:4272`、Codex in-app browserで確認。`templates/COUNTRY_LESSON_AUDIT.md`の12観点に照らす制作者確認であり、独立監査や42シナリオ完了ではない。

| ID | 判定 | 根拠と残件 |
|---|---|---|
| UA01 | 制約付き | NESDC公式Excel/目録・計画目録・ガイドをhash固定。12 sheetsの全数値列と表ブロックを機械的棚卸し。2024p `C:E`とcurrent-price `AE`の2,210セルを照合。過去年、CVM、`Regions to GDP`、`CLUSTERS`の意味監査は `priority_unassessed`。 |
| UA02 | 制約付き | 77省・7経済地域→全国のGPP、人口分母、23産業/小計行の一致と1人当たり式を確認。詳細表`NO!AE691`人口と`PER CAPITA!D47`の矛盾を保留。残りの国勢調査・登録人口は未取得。 |
| UA03 | 制約付き | 77省原表行をNESDC provider IDで保持。DOPA法定コード・適合図形・計画管轄との対照未確認。旧provider77図形を除去。 |
| UA04 | 制約付き | 全国＋77省×24指標＝1,872直接観測。親全国は原表直接値で、77省の完全和でも照合。7経済地域を重複加算せず、1人当たり値は平均しない。WDI・NSO・BORAと混ぜない。 |
| UA05 | 制約付き | 全国、Khon Kaen、Chiang Mai、Phuket、Bangkokの出力を原値照合。ブラウザーで省→全国→省→全国、境界なし代替を確認。全テーマ、狭画面/低性能端末は未実施。 |
| UA06 | 制約付き | Chiang Mai後のThailand上位選択で見出し・URL・全国1人当たりGPPに復帰。省再選択も直ちに切替。地域メモ保持は未確認。 |
| UA07 | 制約付き | 全国の77件比較で初行`0101`、末行`0706`、全24指標のCSV/印刷HTML全行、値・原表locatorを照合。比較行注目が上部対象を保持する実操作は未実施。 |
| UA08 | 制約付き | NESDC 2024p GPP分母とNSO 2025常住国勢調査、BORA登録人口、WDI全国を分離。取得失敗WDIは`failed`とし、地方欠測を全国値やゼロで補填しない。 |
| UA09 | 制約付き | NESDC計画ガイド・目録は全国参考、Chiang Mai計画所在は未検証例。Chiang Maiの計画/予算/実績/評価欄は未収集と表示。 |
| UA10 | 未実施 | 現行法的権限、県計画とcluster・地方自治体計画の関係、現行本文・承認・予算執行・公式評価未取得。草案表示のガイドを施行中の法律としない。 |
| UA11 | 制約付き | 5例の診断CSV/HTML/Markdown、計画HTML、根拠CSVで地域・年・値・出典を照合。Word/PDFと実プリンター・狭画面・低性能での長表確認は未実施。全国画面は24指標・1,848比較行のため負荷検証が必要。 |
| UA12 | 制約付き | 固定原本hash→audit→import→validator/build→actual-output verifierで再生成。Validator 0 errors/warnings、`npm run check` 160 JavaScript/JSON、`npm test` 218/218。Kit転記、独立監査、Hosting/Publicは別ゲート。 |

**42件合格とは報告しない。** NSO/BORA/DOPAの原本とコード/図形、NESDC未採用系列、現行計画・財政本文、利用条件、タイ語/現地確認、独立`ACCEPT`が残る。
