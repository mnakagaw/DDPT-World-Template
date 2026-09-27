# Kazakhstan 国別候補・開始シート（AI記入、2026-09-27）

`templates/COUNTRY_START.md`対応。アジア50件の段階4・中央アジア、`KAZ`。独立・ignored保存先 `generated/kazakhstan-areadata-20260927`、参照実装0.4／dataset schema 0.2。UX v1.0の最終採用や公開ではない。[原本監査](kazakhstan-bns2026-source-audit-2026-09-27.md)と[Task Contract](kazakhstan-task-contract-2026-09-27.md)を参照。

| 項目 | 今回の範囲 | 不足・次の行動 |
|---|---|---|
| 納品と公開 | AreaData branch `codex/asia-domestic-20260926` に再実行コード、hash台帳、監査を保存。原本とサイトは候補内。 | KAZ専用Hosting/Public先、更新責任者、独立`ACCEPT`未設定。公開しない。 |
| 地方統計 | BNS 2026年7月人口の全国＋20第一階層＋228第二階層、9指標2,241値。8月全国＋20第一階層4指標84値。2021国勢調査全国5値。 | 7月sheet 3、8月の他列、行政単位の数値列、2021国勢調査地方表と他巻の意味監査。 |
| 地理 | BNS KATO 2026-09-18の親子コードを7月人口全249行と照合。 | KATOは参照日後。NSDI WFS属性は不完全・重複。適合する公式図形と同日コード版、2021歴史版を確認。 |
| 計画・予算 | 2026改正の計画制度、Ulytau・Burabay本文、Burabay承認記載を確認。Akmola・Almaty oblast計画、Akmola予算報告の公式所在を表示。 | 他地域の本文・承認・手引き・投資、予算と支出・評価は未取得。link-onlyを採用済みにしない。 |
| 国際共通source | 初期WDI全国系列を別定義で保持。 | HAPI/UNHCR/DTM/IPC/MICS/DHS/WorldPop/GHSL/SALB/WaPOR等のKAZ×テーマ×年×地方粒度は未確認。 |
| 利用条件 | 9公式原本をhash固定し、大きい原本・図形をGitに入れない。 | 各原本・NSDI図形の再配布・商用利用条件を資料別に確認。 |

代表11地域は全国、Abay oblast／Abai district、Akmola oblast／Burabay district、Ulytau oblast、Almaty oblast／Almaty city、Astana city／そのAlmaty district、Shymkent city。診断CSV/HTML/Markdown、計画HTML、根拠CSVと元値を照合。ブラウザー操作は全国・Akmola／Burabay・Ulytau・Almatyの主要選択を確認。全頁印刷、狭幅、現地担当、42シナリオ全件、独立監査は未実施。
