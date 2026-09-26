# アフガニスタン国別版・開始シート（AI記入、2026-09-27）

`templates/COUNTRY_START.md`に対応。アジア50件の段階2南アジア、`AFG`。新規のignored候補は`generated/afghanistan-areadata-20260927`。**部分成果・未公開**。詳細は[原本監査](afghanistan-nsia1404-source-audit-2026-09-27.md)。

| 項目 | 採用・確認 | 不足・次の行動 |
|---|---|---|
| 納品と場所 | AreaData branch `codex/asia-domestic-20260926`へコード・監査・公開可能なsource所在を保存。原本PDFとsiteはignoredの独立ディレクトリ。 | 独立ACCEPT、国別Hosting/Public先、現地運用者と更新頻度。DDPT公開先を転用しない。 |
| 仕様 | 共通実装0.4候補、dataset schema 0.2。既存の地域診断・テーマ診断・データベース・計画資料の目的と選択連動を使用。 | UX v1.0最終採用、現地語と利用者受入。 |
| 統計 | NSIA 1404推計の全国（遊牧人口含む）3値と、34州の定住人口3値を別指標へ108直接観測。WDI全国推計は独立保持。 | ほか75表とTable 4旧年の意味監査。新国勢調査とは呼ばない。 |
| 行政・境界 | Table 4の34州名・行番号、女性＋男性・親子算術、Table 76人口照合。 | 行番号は公式コードではない。公式1404境界、municipalityとprovinceの接続、法定計画単位。2007 provider形状は不採用。 |
| 計画・財政 | Kabul MunicipalityとMUDHの都市計画所在、MoF国予算目録のみ。Heratの発表はHerat**市**の資料所在。 | 各州・市の現行権限、計画本文・法的状態、予算・実績・評価。歴史目録を現行承認としない。 |
| 国際共通source | WDI全国系列を初期生成で取得。 | HAPI、UNHCR、MICS、DHS、WorldPop、GHSL、SALB等はAFGの年・テーマ・地理粒度別availability未確認。自動採用しない。 |
| 原本と利用 | NSIA 168頁PDFをhash固定、76番号付き表を見出し/列群単位で棚卸し。EUAAが同じ公式URLを掲載。 | 取得時TLS証明書名不一致。正しいTLS/公式mirrorで再取得。再配布条件も未確認。 |

代表確認は全国、定住範囲、Kabul、Badakhshan、Kandahar、Herat、Nimroz。異なる列・頁・州規模を含めた実出力7事例と画面上のHerat→定住範囲再選択を確認。42シナリオと独立監査は未完了。市民提案、公式計画Word/PDF形式、承認機能は根拠未取得で採用しない。
