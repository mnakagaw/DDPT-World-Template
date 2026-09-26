# Indonesia Task Contract・差分台帳（AI記入、2026-09-27）

`templates/TASK_AND_CHANGE.md`に対応。作業ID `asia-IDN-20260927`。開始AreaData commitはモルディブ引き継ぎ `728fbc2c0671033048671d517992b5d0046bcd09`。独立ディレクトリでBPS国勢調査、歴史地理、計画制度を調べる。納品はPrivate GitHubのコード・台帳。独立`ACCEPT`と国別Hosting/Public先は未取得。

| 契約 | 実施と限界 |
|---|---|
| 版と保護 | 共通実装0.4候補、schema 0.2。DDPT参照、他国、テンプレート本体を変更しない。原本・候補siteをGitへ含めない。 |
| 原本 | BPS Table 1 HTML 35、BPS目録、Surabaya JDIH法令ページ/PDF、Jawa Barat公式計画目録の計39原本を取得・hash固定。 |
| 採用範囲 | 2020 Table 1男女・総数3列から549統計地域・1,647直接値。原表1,749セル中102は州ページの重複合計。残り4人口表の本文は `priority_unassessed`。 |
| 地理比較 | 国→34州、各州→計514 kabupaten/kota。2020統計行は現在の州/県市法定管轄と別。日付対応の公式polygonなし。 |
| 計画 | 内務省令86/2017は全国の制度参照。Jawa Barat RPJMD 2025–2029は所在のみ、PDF本文未取得なので州文書へ接続しない。計画・予算・実施・評価を独立に調査。 |
| UI/出力 | 全国・Aceh・DKI・Jawa Barat・Bogor `3201`/`3271`・PapuaのCSV/HTML/Markdown、計画HTML、根拠CSV、比較34/23/6/27/29行を確認。ブラウザーで上位再選択を確認。 |
| 検証 | Validator 0 errors/warnings、build、check 155、test 218/218、7例の実出力verifier。42件全件・Word/PDF・狭画面・独立監査は別。 |
| 再実行 | `create-country`新規→BPS・計画原本取得→Table 1全列audit/inventory→import→validate/build→output verifier。原本・行・意味対応が変われば停止・再監査し、正常候補を維持。 |

| 差分ID | 変更 | 根拠・影響 |
|---|---|---|
| IDN01 | provider ADM1図形を除外、2020統計区分を549地域で追加 | 2017 provider図形と2020 BPS/現在の法定境界が未照合。境界なし代替。 |
| IDN02 | BPS国勢調査値をWDI全国年央推計から独立 | 定義と年が異なり、WDIを地方値へ割り当てない。 |
| IDN03 | 同名地域をBPS原コードで保持、州ページTOTAL重複を除く | 同名Bogor等の統合と親合計二重計上を防ぐ。 |
| IDN04 | 2017省令を全国制度参照に限定、Jawa Barat計画は所在のみ | 法本文の一部確認と地方計画の本文・管轄確認を分ける。 |

**判定: local partial / unpublished.** Kitへは公式source所在のみ渡す。
