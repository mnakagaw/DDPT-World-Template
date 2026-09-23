# 世界・広域向け国際統計ポートフォリオ（0.11.0）

AreaDataの世界・大陸・広域の地域診断は、国ごとに調査年・設問・母集団が異なるCensusの合計ではなく、別途取得した国際統計を読む。国・国内地域では確認済みの国勢調査と地方統計を残し、国際参考系列と出典を区別する。国別Censusの追加は世界系列を上書きしない。

| 系列 | 今回採用したもの | 地理・年 | 算出の扱い |
|---|---|---|---|
| [UN World Population Prospects 2024 Rev.1](https://population.un.org/wpp/) | 総人口、男女別人口、出生・死亡、純移動、年齢中央値、出生率、平均余命、乳児・5歳未満死亡率、人口増加率、密度。男女・5歳階級別人口 | 世界、元表とコードが一致するM49地域と235/248の国・地域。2000・2023年は推計、2024～2026年は中位将来推計 | M49 Americas（019）は021＋013＋029＋005、独自「中米＋カリブ」は013＋029という重複のない公表地域の同一年**人数**のみをAreaDataが加算。率や年齢中央値は加算・単純平均しない。派生値と構成IDを残す |
| [UN SDG Global Database 2026 Q2.2 archive](https://unstats.un.org/sdgs/indicators/database/archive/) | 国際貧困線、栄養不足、安全な飲料水、電力、インターネット、初等教育修了、妊産婦死亡比の7系列 | 世界、元表のM49地域、国・地域の公表行。2015～2025年のうち観測がある年 | 指標コード、性・年齢・都市農村・教育段階・所得階層などの内訳を固定。各地域の元表行のみ採用。独自広域や欠測地域へ、国値の割合を足す・平均する補完はしない。推計を作った機関は行ごとに記録 |

人口ピラミッドは2000年をグレースケール、選択年を色分けし、**両図を同一の横軸尺度**で並べる。男女構成は円グラフ、割合は0～100%の帯、連続する年は折れ線、地域差は地図と全件表を使う。割合の帯は目標達成率を意味しない。地図と表では欠測をゼロとして着色・順位付けしない。

地域名だけで異なる統計上の範囲を結合しない。UN M49台帳の公式コード、WPPのSDMX/ISO3、SDGのGeoAreaCodeを照合し、独自地域は別IDで管理する。WPPの国・地域行がM49台帳に一致しなかった13件には値を作らない。SDGの各指標も世界・地域・国の公表行と年がそろわなければ欠測のままにする。SDGは国連統計部の配布基盤であり、元の推計・集計機関はFAO、WHO/UNICEF、UNESCO、ITU、World Bank等、系列によって異なる。

原本のXLSX/ZIP（大容量）はGit・公開サイトに含めない。取得元URL、原本SHA-256、版、採用した内訳と公表元は正規化データのsource記録に保持する。公開ブラウザは`data/supranational.json`だけを国際系列として読み、国内の詳細は必要な国のshardを読む。canonicalの`data/dashboard.json`は生成案件ディレクトリに保存し、公開ディレクトリへ全量を複製しない。

再生成コマンドの入力は保存済みの原本と検証済みの世界・アメリカ大陸dataset。新規の出力ディレクトリを指定する。

```sh
python scripts/extract-un-wpp-world.py --demographic <WPP-demographic.xlsx> --age-male <WPP-male.xlsx> --age-female <WPP-female.xlsx> --registry <world-dashboard.json> --out <wpp-normalized.json>
python scripts/extract-un-sdg-world.py --archive <sdg-2026-q2.zip> --registry <world-dashboard.json> --out <sdg-normalized.json>
node scripts/build-world-portfolio.mjs --world <world-dashboard.json> --americas <americas-dashboard.json> --wpp <wpp-normalized.json> --sdg <sdg-normalized.json> --out <new-project-directory>
```

今回採用したのは上表の20指標であり、以前の候補一覧にあるすべてのUN・国際機関テーマの世界収集が完了したという意味ではない。Censusの下位地域データも世界全域では未整備である。収録状況は指標・選択地域・年ごとに表示する。
