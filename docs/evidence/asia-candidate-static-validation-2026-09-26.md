# アジア全域候補の検証（2026-09-26）

- 対象：`.work/areadata-asia-20260926-remediation-final`。公開版ではない。出力dataset SHA-256 `da6c624f3d8ef667da6dfb27cddeab50a28570d844d9a57de68eddd7383be695`。
- 入力：世界ポートフォリオの`data/dashboard.json`、SHA-256 `77c41cbaaae633b096916b704ae8c3e0ed4cb77e15440618c3f7b266abde2a9b`、edition `2026-09-23T14:27:10.704940Z`。追加統計を発見した版ではない。
- 地理：現行UN M49原典と50 country/area、5 subregionのID・コード・所属を全件照合。56選択地域、50表示用参照図形のうち国・地域図形と結合できたのは44件。図形未結合の6件は台帳と数値表に残る。
- 指標：31指標、10,668観測、27国際ポートフォリオ指標、WDI 4指標。国内Censusデータ枝は0/50。各指標の国別被覆と最新年は候補の`ASIA_COVERAGE.json`とCSVに記録。
- WPPの範囲差：Eastern Asiaの2026年直接値とM49掲載7件合計は23,011,292人、Asia全体と掲載50件合計は23,011,294人異なる。WPP台湾行が公表値に含まれることを原本で確認し、画面・診断CSV/Markdown/HTMLに説明を追加した。公表値を掲載行の合計へ変更していない。
- 出典：WPP、SDG、UNSD AMA、IMFとM49、WDI、Natural Earthの原本18ファイルをprivate候補に保持し、ソース台帳のURL・SHA-256・サイズと照合。Gitと公開サイトには原本を含めない。
- 4国際系列の採用9,524観測を、原本から再抽出した値・状態と全件照合して一致。WDI 4指標の原本は保存・ハッシュ照合済みだが、この再抽出照合の対象外。
- `npm run check`：132 JavaScript modulesとJSON templatesで成功。`npm test`：216/216成功。`git diff --check`成功。`verify:asia`は元世界datasetとの全件照合、地理、選択値、WPP範囲差、診断CSV、静的資産を確認して成功。候補dataset validationはエラー0、警告5。4出典に原本がないというschema警告はprivate原本manifestで別途照合したが、国別計画資料は未取得。
- ローカルHTTPで`/`、地域診断のAsia直接URL、テーマ診断、計画、データベース、`data/dashboard.json`、`assets/app.mjs`の200応答とContent-Typeを確認。

初回候補の独立監査は`REJECT`。この修正候補についても、実ブラウザーへの接続が作業環境で拒否されたため、地域クリック、地図描画、年切替、3言語、戻る／進む、CSV/診断出力の実取得は**未実施**。HTTP 200とユニットテストをこれらの代わりに合格扱いしない。`ACCEPTANCE.md`の該当条件と`DELIVERY.json`はpendingで、公開ゲートを通していない。
