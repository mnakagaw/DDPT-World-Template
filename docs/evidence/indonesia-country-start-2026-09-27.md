# インドネシア国別版・開始シート（AI記入、2026-09-27）

`templates/COUNTRY_START.md`に対応。アジア50件の段階3東南アジア、`IDN`。独立したignored候補 `generated/indonesia-areadata-20260927`。**部分成果・未公開**。[原本監査](indonesia-sp2020-source-audit-2026-09-27.md)を参照。

| 項目 | 採用・確認 | 不足・次の行動 |
|---|---|---|
| 納品と場所 | AreaData branch `codex/asia-domestic-20260926`にコード、台帳、公式source所在を保存。原本とsiteは国別ignored候補。 | 独立`ACCEPT`、Indonesia固有のHosting/Public先、運用者・更新周期。既存DDPT公開先を転用しない。 |
| 仕様 | 共通実装0.4候補、dataset schema 0.2。地域診断・テーマ比較・DB・計画資料・既存出力を保持。 | UX v1.0最終採用、インドネシア語の表示と現地受入。 |
| 国内統計 | BPS SP2020 Table 1の全国＋34州別HTML計35原本、3数値列・1,749セルを棚卸し。549統計地域・3指標・1,647直接観測。全国人口270,203,917。 | 同目録の残り4表、他のSP2020分野、さらに新しい地方統計、利用条件。 |
| 地理・コード | BPS 2020の34州・514 kabupaten/kota行は全3列で親子一致。同名Bogor 2件を別コードで保持。provider図形は除外。 | 対応年の公式図形、現在のKemendagriコード/法定型との対照、Papua分割。 |
| 計画主体・資料 | Permendagri 86/2017の644頁本文を取得し、RPJPD/RPJMD/RKPD定義等の選択箇所を確認。Jawa Barat 2025–2029 RPJMDの公式所在と制定メタデータを確認。 | 現行改正・手引き、RPJMD本文、地域別RKPD/APBD/支出/評価。本文未取得の州計画は文書表示へ接続しない。 |
| 国際共通source | 初期生成のWDI全国系列は国勢調査と別指標。 | 他共通sourceの国・テーマ・年・粒度別availabilityと採否。 |
| 利用条件と公開 | 35 BPS HTMLと4関連原本をURL/bytes/hashで固定。候補は未公開。 | 再配布条件、42シナリオ、独立監査、Hosting/Public先。 |

代表確認は全国、Aceh、DKI Jakarta、Jawa Barat、同名Bogor 2行、Papua。画面でJawa Barat→Bogor `3201`→同じJawa Barat全体の再選択を確認。7例の実出力を照合。Word/PDF、狭画面、全514地域、現地利用者確認は未実施。
