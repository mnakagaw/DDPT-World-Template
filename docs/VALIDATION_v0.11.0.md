# AreaData 世界・国際統計 0.11.0 検証記録

- 対象コード: `000ba713890f14fdf08e3701bfae095d1f996534`（GitHub main）
- 対象dataset SHA-256: `8c1a92f68661fa4f3d7f6e7a5bf24caf4ff8cda3653bff534242769bddfd2d08`
- 生成案件: `.work/areadata-world-v0.11.0-release`
- 検証環境・日付: Windows / Node 22以降、ローカルHTTP、2026-09-23

## 採用データと区分

UN M49台帳の248 country/area、世界と5大陸、探索用広域を保持。既存のアメリカ大陸国内詳細を引き継ぎ、世界版datasetは20,773地域・268,870観測。UN WPP 2024 Rev.1の13指標は16,960観測、2000年および選択年の男女・5歳階級別人口は1,310地域・年プロファイル。M49に厳密対応する国・地域は235/248であり、残りを国別合計で補間しない。

UN SDG Global Database 2026 Q2.2から7指標・11,188観測を採用。国際貧困、水、栄養、電力、Internet、初等教育、妊産婦死亡について、元表の地域コードと性・年齢・都市農村・教育段階・所得階層等を固定した行だけを採用した。SDGの割合を国別値から大陸へ単純平均しない。元の推計機関は観測行の`source_publisher`に保存した。

原本は公開サイト・Gitに置かず、正規化版のsourceにURL、容量、SHA-256を保存した。WPP人口原本のSHA-256は`98e34d9b65b53858cd08a57a566e45050b08093ad85ba5714fe6fbd78055ae6d`、男性年齢表は`7b696713be2f229933a55b5d2f825e9ba695a7b9dab3a6fadfd06eb29a8d1205`、女性年齢表は`5c7d015f2431a07cbedf3ec9d196ae9071401e906c8392fe3019bfe4cfba4977`。SDG archiveのSHA-256は`5aad401a0e5412984e3b6b0437a7fd0e1d5d7001f1530e617f6a6a6d4f4e8c99`。

## 受入確認

| 確認 | 結果 |
|---|---|
| `npm run check` | 116 JavaScript modules・JSON templatesの構文確認通過 |
| `npm test` | 203/203通過。旧国別・地域版の挙動と、新しい広域系列・図表を含む |
| dataset検証 | errors 0 / warnings 0。上記dataset SHAと結合 |
| 世界の地域診断 | 2026年の国連中位推計総人口8,300,678,395人。2000年灰色と2026年色分けの人口ピラミッド2面、男女構成の円グラフを実画面で確認。2図は同一尺度 |
| 経年表示 | 2000年と2023年の間に観測がない場合、年次の線をつながず2区間に分けることを実画面と単体テストで確認 |
| アメリカ大陸の貧困指標 | SDG公表行2024年3.1%。割合図はSVGの全幅100に対し3.1を塗り、元推計機関World Bankを表示。CSPで無効になるinline CSSを排除 |
| 広域Census分離 | 世界は20指標、Americasは公表行のある10指標、独自Central America + Caribbeanは加算可能な6人口指標。広域CSVにCensus混在年の部分合計は含まれない |
| 国内詳細との接続 | Brazilの国別shardを遅延読込し、2022年Census人口203,080,756人と27州の地域選択を実画面で確認 |
| 公開用の初回転送 | `data/dashboard.json`約3.1 MB、別の`data/supranational.json`約6.0 MB。国別詳細は選択時のみ読み込む。Apache系では`.htaccess`でHTML・JS・CSS・JSONの圧縮を要求 |

実画面検証はローカルの生成サイトで行った。モバイルの手動操作、全20指標すべての国・地域別目視、国別出力文書の内容再点検、国際機関に存在する全テーマの収集はこの版の受入範囲外。独自広域でSDG割合の直接公表行がない場合は欠測のままとする。世界データの下位Census整備はアメリカ大陸の既存成果を保持し、他国は今後の国別収集で増やす。

## 公開照合

2026-09-23に`areadata.net`の既存0.10.5版と、変更対象125ファイルをFTPで事前照合した。変更対象が既知の旧SHA-256または再開済みの新SHA-256と一致する場合だけ転送し、データ→実行アセット→HTMLの順で反映。各転送ファイルはサーバー上で読み直し、SHA-256と容量の一致を確認した。127ファイルの公開版に対し変更125件、FTP receiptは`.work/ftp-deployment-areadata-v0.11.0-world-2026-09-23.json`。旧版の未使用`data/dashboard-full.json`は今回の公開処理で削除せず残したが、新しい画面はこれを読み込まない。

HTTPSでは5ページ、主要JS/CSS、初回JSON、別国際統計JSON、Brazil・Belizeの国別shard、Mexico境界shardの計15ファイルをローカル生成物と**バイト・SHA-256一致**で確認した。receiptは`.work/public-verification-areadata-v0.11.0-world-2026-09-23.json`。圧縮リクエストでは約6.0 MBの`supranational.json`がgzipで504,391 bytesになり、`Content-Encoding: gzip`を確認した。

公開ブラウザーでも世界人口8,300,678,395人、ピラミッド2面と男女比円グラフ、2000年から2023年の折れ線分断、AmericasのSDG貧困率3.1%と幅3.1のSVG、独自「中米＋カリブ」の人口系6指標とCensus混入なし、Belizeの国別Census・下位地域の表示を確認した。コンソールerrorは0件。これは制作担当による受入検証であり、別担当の独立監査としては記録しない。
