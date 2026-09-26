# パキスタン国別版・開始シート（AI記入、2026-09-27）

`templates/COUNTRY_START.md`に対応する案件判断。利用者のアジア50件依頼から国名・優先順を解決した。新規のignored候補は`generated/pakistan-areadata-20260927`、状態は**部分成果・未公開**。根拠の詳細は[原本監査](pakistan-pbs2023-source-audit-2026-09-27.md)。

| 項目 | 確認済み・採用 | 未確認・次の対応 |
|---|---|---|
| 案件・納品 | Pakistan `PAK`、段階2南アジア。AreaData branch `codex/asia-domestic-20260926`の独立新規ディレクトリ。コード・公開可能なsource所在地・監査はPrivate GitHub、原本と候補siteはローカルignored。 | 国別Hosting/Public先、提供範囲、現地利用者・運用責任者・更新頻度。既存DDPT公開先を転用しない。 |
| 参照仕様 | 共通実装0.4 candidate、schema 0.2。地域診断、テーマ比較、計画資料、データベースの既存ページを維持。 | UX v1.0最終採用、現地実務受入、Urdu等現地語対応。 |
| 統計対象 | PBS 2023 Census Table 1の4州＋ICTという原表の対象を別節点にし、4州と136地区、6直接指標846観測を採用。全国WDI年央推計はPakistan根節点に別系列で残す。 | AJK・GBの対応する統計と対象関係、他32番号付き表の意味監査。Table 4以降は詳細人口の母集団注記を別に確認。 |
| 公式地理 | Table 1の州・地区名と親子順、136地区を検証。PBS GISと2023行政地区一覧、FOP Census District code表の所在を確認。 | Table 1行に公式行政コードがない。Census Districtと行政Districtの対応、2023の公式polygon、現行地方政府境界。2019 provider形状は不採用。 |
| 地方制度 | Punjab 2025年法、KP法と2022 Tehsil規則、Sindh 2013年法、Balochistan 2010年法、ICT 2015年法の公式所在を州・ICT別に確認。 | 改正を反映した現行条文、実際の法定計画主体・周期・対象、当該地域の計画本文・承認。国勢調査地区を地方議会と同一視しない。 |
| 計画・財政資料 | 連邦PSDP 2026–27と執行資料の公式目録を全国参考として確認。計画ページは法令所在と国勢調査原表、地域別計画0件を区別。 | 地方議会ごとの承認済み計画、予算、執行、評価原本。連邦PSDPを地区計画へ転記しない。 |
| 国際共通source | WDI全国系列は初期生成で取得済み。 | HAPI、UNHCR、MICS、DHS、WorldPop、GHSL、SALB等はパキスタン・テーマ・年・粒度別availability未確認。自動採用しない。 |
| 原本・利用 | PBS公式目録HTMLとTable 1の6 XLSXを取得し、7原本のhash・receiptを保持。 | 原本再配布条件、法令PDF本体取得、他表の利用条件。 |

代表確認はPBS Table 1全体、KP/Bajaur、Punjab/Lahore、Sindh、Balochistan/Gwadar、ICTを選んだ。Bajaur都市とLahore農村の実測0、KP Topi Tehsil原表の矛盾、都市偏重と農村地域、全国対象範囲の差を含む。原表と9例のCSV/HTML/Markdown、計画HTML/根拠CSVを照合し、ブラウザーで地域切替と0・出典・未取得資料を確認した。42シナリオの完了や外部受入ではない。市民提案、AI文章診断、Pakistan固有Word/PDF様式は根拠未取得で採用していない。保存・認証・共通主要操作は変更しない。
