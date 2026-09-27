# Brunei Darussalam Task Contract・差分台帳（AI記入、2026-09-27）

`templates/TASK_AND_CHANGE.md`に対応。作業ID `asia-BRN-20260927`、branch `codex/asia-domestic-20260926`。Brunei国別候補へ確認した地方統計と計画source所在を接続し、Private GitHubへ再現コードと監査記録を納品する。既存テンプレート、他国候補、DDPT参照リポジトリは改変しない。BRN専用の公開先は未設定、独立`ACCEPT`は未取得。

| 契約 | 実施・境界 |
|---|---|
| 原本と停止条件 | 公式PDF6件をbyte長とSHA-256で固定。新規ディレクトリ→公式原本取得→import→validate/build→原表対出力照合。版・hashが違えば停止し、旧正常候補を置換しない。 |
| 統計 | DEPS BPP 2021 Annex B1/B2の2021総人口、男女、世帯、居住住宅、A1/C1の居住資格別人数、A2の5歳階級Personsを足した0–14/15–64/65+。前8指標は出典公表セル、後3指標はAreaData算出と表示。WDI全国推計を地方へ流用しない。 |
| 表の保留 | Annex A1–A12、B1–B6、C1–C10の28表を台帳化。A1/A2/B1/B2/C1の選定列だけ採用。残り23表とMain Reportの全表は`priority_unassessed`。B1/B2の2011年欄は境界対照未確認につき採用しない。 |
| 地理・比較 | 全国→4 District→39 Mukim。公式コードと同版図形なし。2011年geoBoundariesを外す。District/Mukimの直接セルを使い、親値を子の部分和で埋めない。全国比較4件、各DistrictのMukim全件を同一2021年定義で比較。Mukimで細分停止。 |
| 制度 | Cap.248 §8, §13–15、§17–19を確認。Planning Authorityがdraftを作成し、Ministerが承認に関与する。JPBD目録のDistrict Planはリンク所在だけ。Mukimには親Districtの目録情報として明示し、Mukim計画、承認、予算支出を作らない。 |
| UI/出力 | 上部で分析地域を選ぶと見出し、全指標、資料、URL、出力先が同時に切り替わる。比較表への注目は対象を変更しない。図形欠測時も全件表と取得済み値・資料を残す。6代表地域の診断CSV/HTML/Markdown、計画HTML、根拠CSVを照合。 |
| 公開ゲート | `validate-country`/build/check/test/実画面は制作者確認。42シナリオと別担当の独立完成監査は別。Kitへは公式公開URLと注意だけ返し、原本・観測・採用判定は渡さない。Hosting/Publicなし。 |

| 差分ID | 判断と理由 |
|---|---|
| BRN01 | 初期取得の2011年ADM1参照図形を候補から除外。2021年の公式コード・境界との結合根拠がない。 |
| BRN02 | A1/A2/B1/B2/C1の選定列から11指標・367観測を追加。年齢群の加算15件だけ`calculated`とし、ゼロを欠測に変えない。 |
| BRN03 | Cap.248とRKN12を全国参考、JPBDの4計画目録を各DistrictとそのMukimの親計画文脈に限定。本文取得・公式承認・執行を推定しない。 |

**判定: local partial / unpublished。** 全原表の意味監査、公式コード・図形、計画本文・承認・実績、利用条件、42シナリオと独立`ACCEPT`を次の閉鎖条件とする。
