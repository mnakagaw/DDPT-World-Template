# Malaysia Task Contract・差分台帳（AI記入、2026-09-27）

`templates/TASK_AND_CHANGE.md`に対応。作業ID `asia-MYS-20260927`。開始AreaData版はMyanmar引き継ぎ後のbranch `codex/asia-domestic-20260926`。独立候補へDOSM統計、公式地理・計画sourceを調査して部分接続する。納品はPrivate GitHubの再現コード・根拠台帳。独立`ACCEPT`とMYS専用Hosting/Public先は未取得。

| 契約 | 実施・境界 |
|---|---|
| 原本・再実行 | 13公式原本をbytes/SHA-256固定。新ディレクトリ生成→原本取得→audit/import→validate/build→actual-output verifier。原本や更新失敗があれば最後の正常候補を上書きしない。 |
| 統計採用 | 人口2020/24のsex総数だけを国/州/地区へ。HIES 2022/24の5指標と世帯amenities3指標は州だけ。WDIは別全国系列。1,258観測と24欠測、14新指標。2024中間推計を2024国勢調査と呼ばない。 |
| 地理・比較 | DOSMの16州/FTと156細分地区を出典行IDで区別。4単一州/FT地区重複を除外、2020改名4行を保留。UPI/PBT/2017図形と未照合のため公式code・polygonを割り当てない。親の直接値を子から再集計しない。 |
| 計画・財政 | KLだけ官報の計画採用・効力を確認。DBKL予算演説の収入/支出は2025**見込額**で、実績と区別。Volume 2、旧予算表、年報の未監査数値を採用しない。他地区にKL資料を継承しない。 |
| UI・出力 | 全国、Selangor、Petaling、KL、Cameron Highlandの診断CSV/HTML/Markdown・計画HTML・根拠CSVを原表照合。選択→親へ戻る、計画資料残留防止、16州比較注目をブラウザー確認。 |
| 検証・公開 | Validator、build、共有check/test、実出力verifierを実行。42件全件、Word/PDF、全印刷、狭幅/現地端末、独立監査は別記録。Kitへは公式source所在と注意だけを渡す。Hosting/Publicなし。 |

| 差分ID | 変更 | 根拠・影響 |
|---|---|---|
| MYS01 | 初期2017図形を外し、DOSM 2024報告行を全国/州/地区の選択台帳へ採用 | 2020/24統計境界との公式対応が未確認。地図代替として検索と全件表を表示。 |
| MYS02 | 2020国勢調査調整人口と2024中間推計、国際WDIを別指標・単位/期間で保持 | 異なる母集団や年の値を自動同一化しない。 |
| MYS03 | 2024 amenities空欄24個、2020改名4地区、HIES地区を保留 | 欠測を0や親全国値で埋めず、コード照合待ちとして追跡。 |
| MYS04 | KLの官報と計画Volume 2・DBKL予算見込額をKLだけへ接続 | DOSM地区をPBTと一般化しない。計画効力、予算見込、実支出、公式評価を別状態にする。 |

**判定: 地方統計とKL資料のlocal partial / unpublished。** 国勢調査PDF全表、公式code/境界、全地域の法定計画/財政、独立監査が別ゲート。
