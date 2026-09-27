# Philippines Task Contract・差分台帳（AI記入、2026-09-27）

`templates/TASK_AND_CHANGE.md`に対応。作業ID `asia-PHL-20260927`。開始AreaData commitはインドネシア引き継ぎ版 `8ba39f628564745515f8fdfaadcdabf0fc05b5a3`。独立国別候補にPSA POPCEN、Q2 PSGC、地方計画・予算を調査・接続する。納品はPrivate GitHubのコード・台帳であり、独立`ACCEPT`と国別Hosting/Public先は未取得。

| 契約 | 実施と限界 |
|---|---|
| 版と保護 | dataset schema 0.2。DDPT参照、他国作業、本体テンプレートをフィリピン固有値で変更しない。原本・候補siteはGitへ入れない。 |
| 原本 | PSA 30原本（POPCEN22、PSGC Q2/Q4各4）、Quezon City/DILG計画6 PDFを取得・hash固定。法令・市議会の公開ページは所在と表示内容を確認。 |
| 採用範囲 | Table A全国 I7とTable Bの2024 F列全1,743行だけ。1,744地域・1指標・1,744直接値。26 XLSXの329数値列エントリを棚卸し、Table C・過去年・PGRは `priority_unassessed`。 |
| 地理比較 | 全国→18地域、地域→県/HUC/SGA、県→市町、SGA→8町。全国と地域和の差1,708は外交施設在外者。親には直接観測を採用し、子合計で埋めない。公式対応polygonは0。 |
| 計画 | 法定計画主体はLGU（県・市・町・barangay）。統計RegionとSGAはLGUではない。Quezon CityのCDP/LDIP/AIP/予算のみ市に表示。取得・採択、事業実施、支出、公式評価を別扱い。 |
| UI/出力 | 全国/NCR/QC/Makati/Taguig/NIR/BARMM/Maguindanao del Norte/Sulu/SGAの診断CSV/HTML/Markdown、計画HTML、根拠CSVを原表照合。上位再選択はブラウザーで確認。 |
| 検証 | Validator 0 errors/warnings、build、10例の実出力verifier。共有check/test、42件全件、Word/PDF、狭画面、独立監査は別記録。 |
| 再実行 | `create-country`新規→PSAブラウザー原本取得→archive→planning取得→audit→import→validate/build→output verifier。原本hash・行数・数値または制度状態が変われば再監査し、既存正常候補を保持。 |

| 差分ID | 変更 | 根拠・影響 |
|---|---|---|
| PHL01 | 2020 geoBoundaries 17参考図形を外し、PSGC Q2の18地域・下位報告行を接続 | ARMM/NIRと2024 POPCENの時点・階層が合わず、誤形状で地域を選択させない。 |
| PHL02 | 2024国勢調査人口をWDI年央推計から分離 | 2024全国112,729,484人と2025年等の推計は年・方法・対象が異なる。 |
| PHL03 | 10地理差分とSGAコードなしを保持、101親子合計と在外1,708を検証 | Makati/Taguig、NIR、BARMM、Imelda/Payao等を名称・過去年だけで自動統合しない。 |
| PHL04 | Quezon City4資料だけ市ノードへ接続、市議会採択根拠を別登録 | AIPと予算、本文取得と制度状態、支出・評価を混同しない。 |

**判定: local partial / unpublished.** Kitへは公開可能な公式source所在のみ渡し、値・原本・独立採用を移さない。
