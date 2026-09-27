# Singapore Task Contract・差分台帳（AI記入、2026-09-27）

`templates/TASK_AND_CHANGE.md`に対応。作業ID `asia-SGP-20260927`、branch `codex/asia-domestic-20260926`。新規候補に公式資料を収集し、統計と計画制度の**確認できた範囲だけ**接続。納品はPrivate GitHubの再現コード・source台帳・検証記録。SGP専用Hosting/Public先と独立`ACCEPT`は未取得。

| 契約 | 実施・境界 |
|---|---|
| 原本・再実行 | 7原本のbytes/SHA-256固定。新ディレクトリ生成→原本取得→import/audit→validate/build→実出力照合。原本変化や失敗時に前回正常版を上書きしない。 |
| 統計 | 2026住民人口の男女計/男子/女子、HDB/condo/landedだけを原表セルで採用。2,328 slots中1,489数値・839 `-`欠測。2020 CensusとWDIは別版・別母集団。 |
| 地理・比較 | MP2025区域55件は出典名＋URAコード・図形一致。Subzone 332件は親区域付き原表キー、図形なし。2020 MP2019図形は現行2026値に使わない。親値は直接観測を優先し、子の丸め和を代入しない。 |
| 計画 | URA MP2025は国の法定Master Plan。Planning Area/Subzoneを地方自治体にしない。予算、実支出、実施、評価は未取得状態を分ける。 |
| UI/出力 | 全国、Tampines/同東部、Ang Mo Kio、Changi Bayの診断CSV/HTML/Markdown、計画HTML、根拠CSVを原表照合。ブラウザーで区域選択・親へ戻る・比較注目・資料分離を確認。 |
| 完了・公開 | Validator、build、共有check/test、出力verifierは制作者確認。42件全件と独立監査は別。Kitへは公式所在と注意だけ渡し、原本・数値・結合採用を移さない。Hosting/Publicなし。 |

| 差分ID | 変更・理由 |
|---|---|
| SGP01 | 初期2016年5 Region図形を外し、URA MP2025の55 Planning Area参考図形へ。2026統計と同版の区域名55件を照合。 |
| SGP02 | 全国・55区域・332 Subzoneの6直接指標。`-`は欠測、2020 MP2019値は歴史原本のまま保留。丸め和やWDI総人口で親を補わない。 |
| SGP03 | 国のMP2025本文と官報状態だけを全国に接続。区域別の計画承認、予算、支出・評価を作り込まない。 |

**判定: 地方人口統計と全国計画のlocal partial / unpublished。** 全原表の意味、Subzone図形/コード、地域別計画・財政、42シナリオ、独立監査が別ゲート。
