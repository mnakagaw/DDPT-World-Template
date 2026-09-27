# Cambodia Task Contract・差分台帳（AI記入、2026-09-27）

`templates/TASK_AND_CHANGE.md`に対応。作業ID `asia-KHM-20260927`。開始AreaData commitはフィリピン引き継ぎ版 `48945967a2ee2dbb30fd77c7844d1aa617f69f4e`。独立国別候補にNIS 2019最終国勢調査とNCDDコード・計画sourceを調査・部分接続する。納品はPrivate GitHubのコード・台帳。独立`ACCEPT`と国別Hosting/Public先は未取得。

| 契約 | 実施と限界 |
|---|---|
| 版と保護 | dataset schema 0.2。DDPT参照、他国作業、本体テンプレートをKHM固有値で変更しない。原本・候補siteはGitへ入れない。 |
| 原本・再現 | NIS PDF 26,586,966 bytes、NCDD Gazetteer HTML 8,824 bytesをhash固定。新規候補生成→固定原本取得→audit→import→validate/build→actual-output verifier。原本・表形式が変われば監査を停止し既存正常版を保持。 |
| 採用範囲 | Table 2.1.1全人口の全国/25 Province男女・総数、P-01～P-25の通常世帯6列、全国の通常世帯人口・世帯数だけ。全人口と通常世帯人口は別指標。P表の一部誤セルを保留。 |
| 地理比較 | NIS 2/4/6桁報告行。全国→25 Province、Province→District等、District等→Commune等の原表台帳を維持。親値は直接公表値のみで、親子不一致8地点を推計で埋めない。適合polygon0。 |
| 計画 | 地方行政法・計画手引きの公式目録は全国参考リンクのみ。本文、現行適用、地方計画・予算・支出・公式評価は未取得。統計報告範囲から法定権限を推定しない。 |
| UI・出力 | 14例の診断CSV/HTML/Markdown、計画HTML、根拠CSVと全件比較行を照合。ブラウザーで上位再選択と欠測を確認。指標下部の比較と上部対象の分離を維持。 |
| 検証 | Validator 0 errors/warnings、build、14例の実出力verifier。共有check/test、42件全件、Word/PDF、狭画面、独立監査は別記録。 |
| 公開 | source所在だけKitへフィードバック。原本、11,301観測、コード/境界の全面承認、国別採用をKitへ移さない。Hosting/Publicは実施しない。 |

| 差分ID | 変更 | 根拠・影響 |
|---|---|---|
| KHM01 | 初期2017 geoBoundaries図形を外し、2019 NISの報告階層へ置換 | 出典・時点の違う多角形を2019年の法定・統計境界と見せない。地図なしの既存選択・全表代替を使う。 |
| KHM02 | 全人口と通常世帯人口を別指標へ分離 | 15,552,211人と15,184,511人は母集団が異なる。全国WDI推計とも同一化しない。 |
| KHM03 | P表の誤コード・親子不一致と保留値を明示 | `0314`はNCDDと子コードで裏付け。`0302`/`0801`の6列、`2202`の人口関連5列を保留し、子合計を親の直接値へ補填しない。 |
| KHM04 | NCDD法令・手引き目録を全国参考へ接続 | 取得段階 `link_verified` と制度状態 `unverified` を分け、各地方の実計画・採択・実績を主張しない。 |

**判定: local partial / unpublished.** 法定権限や計画の承認を国勢調査行から作らない。
