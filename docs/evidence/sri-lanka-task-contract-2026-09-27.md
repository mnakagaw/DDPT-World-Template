# Sri Lanka Task Contract・差分台帳（AI記入、2026-09-27）

`templates/TASK_AND_CHANGE.md`に対応。作業ID `asia-LKA-20260927`、開始AreaData commit `40ef465d26e18a79596139114b8027fc700effbc`。アジア50国内版の段階2として、DCS原本・地域コード・計画制度所在を調査し、独立ディレクトリに国別候補を作る。Private GitHubのコード・台帳まで。独立`ACCEPT`と国別Hosting/Public先は未取得。

| 契約 | 実施と限界 |
|---|---|
| 版と保護 | 共通実装0.12.1、schema 0.2。DDPT参照・他国・テンプレート本体を国固有に書き換えない。 |
| 原本 | 公式34点取得：7 Population A、16 Housing A、9 GN、コードXLSX、最終PDF。3番号表の採用数値列と366行、報告書Table 3.2の9州値を監査。残りは所在・sheet extent、GN人口/コードの限定照合で、全意味監査ではない。 |
| 範囲 | 全国・9州・25郡・340 DSの375対象。30指標、10,989直接観測。GN暫定値やWDI全国推計と確報を合成しない。 |
| 地理比較 | 全国9州、Western3郡、Colombo13 DSを実出力で全行照合。州人口は確報PDF直接値。州世帯等は親観測欠測、未設定の子集計で補わない。公式適合polygon 0。 |
| 計画 | 市議会等とDSを別主体にする。2020年Gazetteは所在のみ、本文・現行性未監査。Colombo市の公開資料所在をDS/郡に付けない。 |
| UI/出力 | DS→同じ郡再選択で対象・URL・人口/世帯を切替。8例のCSV/HTML/Markdown/計画HTML/根拠CSVを原セル・PDF頁と照合。 |
| 検証 | Validator 0 errors/1 planning warning、build、共有check 153モジュール/テンプレート、test 218/218、実出力verifier。42シナリオ・Word/PDF・独立監査は別。 |
| 再実行 | `create-country`新規→hash固定原本取得→inventory→import→validate/build→output verifier。hash、表構造、コード衝突、暫定/確報差が変われば停止して再監査する。 |

## 差分台帳

| ID | 変更 | 根拠・影響 |
|---|---|
| LKA01 | Provider ADM1図形を除外し、DCS全国・州・郡・DSの統計階層を採用 | 2024確報と適合する公式図形は未取得。境界なし代替を表示。 |
| LKA02 | A5/A14/A16の30直接指標、報告書州人口、全国・郡・DS直接値 | 州の未取得項目は欠測。WDI・GN暫定系列や率と混合しない。 |
| LKA03 | 公式コードとのDS照合、16名称差と8暫定GN年齢差を保存 | 数値合致を同版法定境界やGN確報と断定しない。 |
| LKA04 | 計画資料0件と法制度所在の限定記載 | 法定自治体の資料を統計DSへ誤付与しない。 |

**判定: local partial / unpublished.** Kitには公開可能な公式source所在地のみ渡し、Kitの独立監査・採用は代行しない。
