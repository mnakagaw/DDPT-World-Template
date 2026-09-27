# Philippines country lesson audit — producer-side partial check

2026-09-27 JST、branch `codex/asia-domestic-20260926`、ignored候補 `generated/philippines-areadata-20260927`。dataset SHA-256は候補の `evidence/PHL_IMPORT_RESULT.json`、原本hashはtracked `config/philippines-*-source-manifest.json`。Windows/PowerShell、Node preview `127.0.0.1:49800`、Codex in-app browser。`templates/COUNTRY_LESSON_AUDIT.md`の12観点に照らす制作者確認であり、独立42シナリオや現地受入ではない。

| ID | 判定 | 根拠と残件 |
|---|---|---|
| UA01 | 制約付き | PSA POPCEN22＋PSGC8原本、計画6 PDFを取得。26 XLSX・161 sheets、329数値列エントリを記録。Table A/Bの2024人口のみ採用。Table Cの119一次sheet・43,750 D列数値セルは `priority_unassessed`。他国勢調査テーマの公式目録と全表は未完。 |
| UA02 | 制約付き | URL/bytes/hash固定、Table A national I7と注記B172、Table B全1,743行・8列、Table C一次/重複を確認。国勢調査全分野・計画全文は意味監査未完。 |
| UA03 | 制約付き | Q2 PSGC 18/82/149/1,493/42,004とTable Bコードを対照。10差分を記録し、SGAコードなしを保持。Q4は後版。2024対応公式polygonは0。 |
| UA04 | 制約付き | 1,744直接観測、101親子合計、全国と国内地域和の差1,708を原表照合。WDI推計・過去年・PGR・実績値を混ぜない。他指標未監査。 |
| UA05 | 制約付き | 全国、NCR、Quezon City、Makati/Taguig、NIR、BARMM、Maguindanao del Norte、Sulu、SGAの出力を確認。ブラウザー地域診断・計画資料を確認。テーマ診断の全地域と狭画面は未実施。 |
| UA06 | 制約付き | 画面で全国→NCR→Quezon City→同じNCR全体を階層selectorで再選択。見出し・URL・指標対象が即時切替、計画ページでもQC文書が消える。メモ保持は未確認。 |
| UA07 | 制約付き | 実出力で全国18、NCR17、NIR4、BARMM7、Maguindanao del Norte13、Sulu19、SGA8の全比較行と印刷HTMLを照合。下部注目操作と狭画面は未確認。 |
| UA08 | 制約付き | 2024同表の直接人数のみ比較。親は直接公表値。全国・18地域の差は在外1,708人を明記。Table B過去年の遡及境界とQ2 PSGC過去年値は一致扱いにしない。 |
| UA09 | 制約付き | RA7160 §106/109/114、DILG 502頁、QC CDP720頁、LDIP497頁、AIP/予算条例と市議会採択目録を確認。QC資料は同市のみ。支出・評価なし、全文と現行法は未監査。 |
| UA10 | 未実施 | LGU別の最新法令・手引き・公式様式から章/欄/出力への対応は未監査。汎用計画基礎出力を公式承認済み計画としない。 |
| UA11 | 制約付き | 10例の診断CSV/HTML/Markdown、計画HTML、根拠CSVで地域・2024年・値・URL/locator・全比較行を照合。Word/PDF、長表印刷の実プリンター確認は未実施。 |
| UA12 | 制約付き | 原本hash→全数値列inventory→import→validator/build→actual-output verifierを実施。共有 `npm run check` 157、`npm test` 218/218合格。Kit feedback、独立監査、Hosting/Publicは別ゲート。 |

候補内に原本、全列inventory、全1,743行の監査、数値差分、import result、出力hashを残す。**42件合格とは報告しない。** Table Cコード、他テーマ、公式図形、法令/計画全文、財政実績、利用条件、独立`ACCEPT`が残る。
