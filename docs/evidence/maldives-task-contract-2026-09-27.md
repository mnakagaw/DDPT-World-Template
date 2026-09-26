# Maldives Task Contract・差分台帳（AI記入、2026-09-27）

`templates/TASK_AND_CHANGE.md`に対応。作業ID `asia-MDV-20260927`。開始AreaData commitは直前のブータン成果 `78c50f248cab26b694c4bbafbeda2f5d33f83d45`。独立ディレクトリでMBS国勢調査・地理・計画資料を調べる。納品はPrivate GitHubのコード・台帳。独立`ACCEPT`と国別Hosting/Public先は未取得。

| 契約 | 実施と限界 |
|---|---|
| 版と保護 | 共通実装0.4候補、schema 0.2。DDPT参照、他国、テンプレート本体を変更しない。原本をGitへ含めない。 |
| 原本 | MBS 2022 CPHの52番号表＋6補助XLSX、Fonadhoo計画PDF、Council公表ページ、大統領府発表2頁を取得・hash固定。 |
| 採用範囲 | P4/P5/H2/H7/EC3/ED16の選定列から23指標、218地域・3,626直接値。その他52 XLSXと選定表の残り列は `priority_unassessed`。 |
| 地理比較 | 国→Maale/20環礁相当/非行政島集計、Maale→9部分行、環礁相当→186行政島。2022統計区分は現行Council権限と別。日付対応の公式polygonなし。 |
| 計画 | Fonadhoo Council計画PDFをL Fonadhooのみへ表示。承認・全文・実施未監査。2026大統領府発表は制度参照、実計画/財政決定の代わりにしない。 |
| UI/出力 | 全国・Maale・HA・L・Fonadhoo・非行政島集計のCSV/HTML/Markdown、計画HTMLと根拠CSV、比較22/9/14/11行を確認。ブラウザーで上位再選択による資料消去を確認。 |
| 検証 | Validator 0 errors/warnings、build、check 155、test 218/218、6例の実出力verifier。42件全件・Word/PDF・狭画面・独立監査は別。 |
| 再実行 | `create-country`新規→取得原本hash固定→全冊inventory→選定表audit→import→validate/build→output verifier。原本、行、意味対応が変われば停止・再監査し、正常な候補を維持。 |

| 差分ID | 変更 | 根拠・影響 |
|---|---|---|
| MDV01 | provider ADM1図形を除外、2022統計区分を218地域で追加 | 公式の同年図形・2026管轄対応がない。境界なし代替。 |
| MDV02 | CPH直接値をWDI全国年央推計から独立させる | 対象・定義・年が異なり、国内島値へのWDI割当は不可。 |
| MDV03 | P5 G17空欄とEC3/ED16の２島名差を保留 | 推定ゼロ・名前類推の無根拠採用を防ぐ。 |
| MDV04 | 2022環礁統計行を現行atoll councilへ読み替えず、Fonadhoo計画を同島だけに接続 | 2026年廃止後の制度と計画管轄を分ける。 |

**判定: local partial / unpublished.** Kitへは公式source所在のみ渡す。
