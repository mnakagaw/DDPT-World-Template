# Pakistan Task Contract・差分台帳（AI記入、2026-09-27）

`templates/TASK_AND_CHANGE.md`に対応。作業ID`asia-PAK-20260927`、担当Codex、開始commit`1c1596265601bdce5f9f66617c5740de21931ee5`。アジア50国内版の段階2案件として、公式地方統計・地理・計画sourceを検証して国別候補を新ディレクトリに作る。現在の納品状態はローカル部分候補とPrivate GitHubへの手順・監査保存まで。Hosting/Publicの国別先は未指定、独立`ACCEPT`未実施。

| 契約項目 | 実施と限界 |
|---|---|
| 版・保護 | 共通実装0.4 candidate、schema 0.2、UX v1.0未最終採用。DDPT参照実装と他国候補を変更しない。Kitには公式source所在地のみ。 |
| 出典 | PBS Table 1公式目録と6 XLSXをhash固定。33番号付き表・305リンクを棚卸しし、取得済み11数値列・737報告単位・19,899セルの採否を記録。Table 10 KPの誤リンクとTopi Tehsil C474の矛盾を原文どおり残す。 |
| 対象・境界 | Pakistan根節点はWDI年央系列。別のTable 1対象節点は4州＋ICTの241,499,431人。4州・136地区の直接行のみ6指標846観測。AJK/GB、コード未照合、provider図形未採用、現在の地方行政への推定結合なし。 |
| 比較 | Table 1対象→4州＋ICT地区、4州→各35/36/30/34地区の5集合。同一年・同じTable 1定義・親子の完全被覆を算術照合。ICTを州として複製せず、Table 1対象の地区節点に置く。率の単純平均・不完全小計なし。 |
| 計画 | 5行政範囲の法令・KP規則所在と連邦PSDP目録を参考資料として表示。`dataset.planning`へ国固有の目的・区分を明示。地方計画・予算・実績・評価本文は未取得、制度状態は未確認。 |
| 操作・出力 | 上部選択が地図・見出し・指標・資料・CSV/HTML/Markdownを連動。地区→州再選択で地区の値を解除。比較表への注目で主対象は変えない。Bajaur都市0とLahore農村0は欠測としない。 |
| 現在の確認 | 9例の実出力で値、年、source cell、比較全行と初末行、対象名を照合。ブラウザーでWDI初期表示、2023 Table 1対象、Bajaur0、KP州への再選択、法令参考と地方資料未取得を確認。Validator 0 errors/warnings、build。共有check/testと独立42シナリオは別記録。 |
| 再実行・中断 | `create-country`は新規ディレクトリのみ。原本を`raw/`へ再取得し、`inventory-pakistan-pbs2023.py`→`import-pakistan-pbs2023.py`→validator/build/actual-output verifierの順。hash・原表異常が変わったら停止して再監査。正常なsiteを更新失敗で置換しない。 |

## 差分台帳

| ID | 変更 | 根拠・影響 | 判断 |
|---|---|---|---|
| PAK01 | 2019 provider ADM1を除外し、Table 1対象節点＋4州＋136地区を追加 | PBS2023行と2019 provider図形の公式コード・境界版対応は不明 | 既存の国別適応規則内。境界は未取得と表示。 |
| PAK02 | 6直接人数指標と5比較集合 | 2023原表セルを採用。Topi Tehsil誤セルや下位単位・派生値は保留 | 既存の比較契約内。WDIは別母集団。 |
| PAK03 | 州・ICT法令と連邦PSDPの所在地を計画参考に追加 | 各法令の現行改正・実計画が未取得。国のPSDPと地区計画を分離 | 共通計画ページを維持。法的承認を推定しない。 |
| PAK04 | 初期表示の既定指標をWDI人口に設定 | Pakistan根節点にTable 1対象範囲の観測は置かないため | 国の初期画面で正しい根節点値を表示。地域・指標の明示選択は保持。 |

独立完成監査・公開確認は未実施。国別候補は**partial / unpublished**。Kitへのsource feedbackは受入・採用ではなく所在地候補。
