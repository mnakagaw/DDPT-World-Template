# India Task Contract・差分台帳（AI記入、2026-09-27）

`templates/TASK_AND_CHANGE.md`に対応。作業ID `asia-IND-20260927`、担当 Codex、国 `IND`。利用者のアジア50国内版依頼に対し、インドの公式地方統計・地理・計画sourceを確認し、実出力可能な国別候補を新ディレクトリに作る。現時点の納品状態はローカル部分候補とPrivate GitHub保存まで。Hosting/Public先・国別提供範囲は未指定。公開を自動転用しない。

| 契約項目 | 対象・判断 |
|---|---|
| branch・開始点・保護 | `codex/asia-domestic-20260926`、開始 `da0e0bdd243a31261c37a86d1c3ab40fe6b9beb5`。他国候補とDDPT参照実装を改変しない。Kitはsource所在の別branchだけ。 |
| 版 | 共通実装0.4 candidate、UX v1.0未最終採用、schema 0.2。設計profileをruntimeに誤読せず、実際の`dataset.planning`/`analysis`を明示。データSHA-256 `f811a882ff2371dbe9c2b599078ea93d96d8472db7a66157c6b18930e6b30dfc`。 |
| 出典・定義 | ORGI 2011 PCA原本、全国・35州/UT・640地区の人数・世帯直接値。WDI年央推計と2027告示は別系列/状態。全85列と255列・TRU組の採否台帳、source hash・セルlocatorを保持。 |
| 地理・比較 | 2011州/UT・地区の公式コードと親子構成を使う。国→35州/UT、州→640地区の35集合。地区をこの取得版のterminalに設定。原表の同年・同概念だけ比較し、都市農村0を保持。2011公式polygon、現行LGD、Panchayatとの対応は未確認。 |
| 計画 | 憲法243G/243WとMoPR 2026–27手引き2点が全国枠組み。eGramSwarajは所在地のみ。`dataset.planning`のreferenceに取得済み原本を表示し、地域別plan/budget/implementation/evaluationは0件と明示。州別法・計画権限を推定しない。 |
| 操作・出力 | 上部の対象選択を主対象とし、地区→同じ所属州の再選択で地区値を解除。比較行への注目で主対象を変えない。診断CSV/HTML/Markdownと計画HTML/根拠CSVに対象・2011年・人/世帯・出典を保持。Word/PDFのインド固有出力は未採用。 |
| 成功条件と現在の実施 | 代表7例で実出力の値・地域・出典と比較初末行を照合。ブラウザーではNew Delhi農村0→Delhi州419,042への切替、全国資料の別表示を確認。Validator 0 errors/warnings、build、check149、test218/218。42シナリオ全合格や独立監査ではない。 |
| 失敗・再実行 | 原本hash変更時は取込停止。既存候補を残し、`scripts/inventory-india-census2011.py`と`import-india-orgi-pca2011.py`で再監査。`build-country`は失敗時に正常なsiteを置き換えない。取得停止・更新責任者/頻度は未設定。 |
| 完了に必要な追加判断 | 国の担当・利用対象・公開先、州/都市法、2011公式境界/current crosswalk、地域別計画/予算/実施/評価、再配布条件、現地実務受入、独立`ACCEPT`。現時点の不足は独立作業の停止理由ではない。 |

## 差分台帳

| ID | 対応契約 | 今回の変更 | 根拠・影響 | 判断・受入 |
|---|---|---|---|---|
| IND01 | 国別schema 0.2、地域選択 | 新ディレクトリへ2011コード付き州・地区676件を追加。生成時の36 provider ADM1図形を国別候補から除外。 | ORGI原表の2011地理とprovider形状の対応未確認。2011境界を描画済みと誤認させない。 | 既存の国別適応規則内。UA03、A35以降を部分確認。 |
| IND02 | 指標と内部比較 | 24直接指標、16,224観測、36比較集合。WDIは別IDのまま。 | 同一source・年・コード親子で全被覆、値の合計は監査済み。未評価231組は表示採用しない。 | 国別適応規則内。UA01/02/04/07/08/11を部分確認。 |
| IND03 | 計画と資料 | 憲法・MoPR手引き・eGramSwaraj所在地を全国参照として追加。 | 2011地区をDistrict Panchayatと推定せず、地域固有の承認/予算/達成を示さない。既存ページ導線は維持。 | 国別適応規則内。UA09部分、UA10未実施。 |
| IND04 | 保存・認証・主要ページ | 変更なし。 | 共通仕様の意味・保存互換を変える範囲外の実装を行わない。 | 既存指示内。完全な回帰試験は未実施。 |

独立完成監査・公開確認欄は未実施。国別候補の現状は**partial / unpublished**であり、Kitへ渡すのは公開source所在のみ。
