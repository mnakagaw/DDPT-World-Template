# カンボジア国別版・開始シート（AI記入、2026-09-27）

`templates/COUNTRY_START.md`に対応。アジア50件の段階3・東南アジア、国ID `KHM`。独立したignored候補は `generated/cambodia-areadata-20260927`。**部分成果・未公開**。[原本監査](cambodia-census2019-source-audit-2026-09-27.md)を参照。

| 項目 | 採用・確認 | 不足・次の行動 |
|---|---|---|
| 納品と場所 | AreaData branch `codex/asia-domestic-20260926` にアダプター、公開可能なsource所在、監査・検証台帳を保存。原本・siteは国別ignored候補。 | 独立`ACCEPT`、KHM固有のHosting/Public先、運用者、更新周期は未設定。DDPT先を転用しない。 |
| 仕様・利用者 | 共通0.4参照実装、dataset schema 0.2を保持。地域の国勢調査診断と地方計画基礎資料の探索を想定。 | UX v1.0最終採用、現地実務担当、クメール語・端末・回線条件、法定計画業務への受入は未確認。 |
| 国内統計 | NIS 2019年最終国勢調査PDFのTable 2.1.1全人口と25 Provinceの男女・総数、別系列のP-01～P-25通常世帯人口・男女・世帯数・公表比率を採用。全国＋25 Province＋202 District等＋1,646 Commune等、計1,874報告地域。 | 2019年後の更新、他の国勢調査分野、地方別CDBの実数、報告書の未監査表。通常世帯と全人口の定義を混ぜない。 |
| 地理・コード | NIS原表の2/4/6桁報告コードを保持。P-03のSrei Santhor印刷コード `211` はNCDD Gazetteerの `0314` と下位14コードで確認。 | 報告書概要204対P表202中間行の差、全コードの現行公式版・法的地域型、2019対応polygon。2017 geoBoundaries図形は接続しない。 |
| 計画主体・資料 | NCDDの2008年地方行政法、2013年Capital/Province計画手引き、2007年Commune/Sangkat手引きの公式目録を特定。 | PDF本文取得が403、現行改正・適用主体・実計画/投資/予算/支出/評価・採択状態は未確認。NISの統計行を法定計画主体と同一視しない。 |
| 国際共通source | 初期生成のWDI全国系列はNIS 2019国勢調査と別ID・定義。 | `SOURCE_PREFLIGHT` のHDX、UNHCR、DTM、IPC、MICS、DHS、WorldPop等はKHMの年・テーマ・粒度別availability未確認。所在だけで採用しない。 |
| 原本・利用条件 | NIS 304頁PDFとNCDD Gazetteer HTMLをURL/bytes/SHA-256で固定。選定表の数値列467エントリ、全P表11,532数値セルを記録。 | 原本再配布条件、他表の全列・意味監査、42シナリオ、独立監査。 |

代表確認は全国、Banteay Meanchey、Mongkol Borei、下位Commune、Kampong Chamの印刷誤り行、Srei Santhor、Kandal、Phnom Penh、Prey Veng、Otdar Meanchey等。14例の実出力を原値照合した。ブラウザーで全国→Banteay Meanchey→Mongkol Borei→同じBanteay Meanchey全体への切替と、郡の全人口欠測を確認。計画本文、テーマ診断の全域、狭画面、Word/PDF、現地利用者確認は未実施。
