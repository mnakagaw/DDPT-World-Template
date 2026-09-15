# 実行テンプレート0.8 検証記録

検証日: 2026-09-15 JST

対象: 中米7か国試作、UN人口比較、国勢調査出典表示、英語・スペイン語・日本語UI

データschema: 0.2（任意拡張）
生成案件: `.work/areadata-ca-v0.8-un-context-i18n-release-2`

## 変更した意味

- 主系列は7か国の採用済み公式国勢調査人口のままにした。中米合計`43,883,591`は、Belize 2022、Guatemala 2018、El Salvador 2024、Honduras 2013、Nicaragua 2005、Costa Rica 2022、Panama 2023の完全・非重複な全国値だけから計算する。
- UN World Population Prospects 2024 Rev.1の人口を国際比較系列として追加した。2023はestimate、2024～2026はmedium projectionである。2026年の7か国合計は`53,870,471`。
- 差`+9,986,880`（国勢調査混合年合計比`+22.8%`）は、基準年と算出方法の違いとして表示し、誤差幅と説明しない。
- 各国比較表の`Census 年`／`Censo 年`／`国勢調査 年`は、その国の最新国勢調査案内ページへリンクする。統計機関名と、実際に値を採用した表・報告書リンクを別に表示する。
- 中米合計の系列リンクは、単一国のCensusと誤認させない`Mixed-year Census series`相当の表示にした。
- ヘッダーにEN／ES／日本語を置いた。URLの`lang`、保存済み選択、ブラウザ言語の順に決定し、未対応言語は英語へ戻す。選択言語は画面内リンクと数値書式に引き継ぐ。出典固有名、原表名、原資料の記述は証拠追跡のため原語を保持する。

## 原資料と正規化

| 項目 | 記録 |
| --- | --- |
| 原資料 | UN WPP 2024 Rev.1 `WPP2024_GEN_F01_DEMOGRAPHIC_INDICATORS_COMPACT.xlsx` |
| 公式URL | `https://population.un.org/wpp/assets/Excel%20Files/1_Indicator%20(Standard)/EXCEL_FILES/1_General/WPP2024_GEN_F01_DEMOGRAPHIC_INDICATORS_COMPACT.xlsx` |
| SHA-256 | `98E34D9B65B53858CD08A57A566E45050B08093AD85BA5714FE6FBD78055AE6D` |
| 原本サイズ | 26,142,942 bytes |
| 正規化版 | `data/international/un-wpp2024-central-america-population.json` |
| 抽出器 | `scripts/extract-un-wpp-central-america.py` |
| 期間 | 2023 estimate、2024・2025・2026 medium projection |
| 被覆 | 7か国 × 4年 = 28観測。各年とも完全被覆のみ地域合計を許可 |

## 機械検証

| 実行 | 結果 |
| --- | --- |
| `npm run check` | 55 JavaScript module／JSONの構文確認に合格 |
| `npm test` | 147／147合格 |
| `node scripts/validate-country.mjs --project .work/areadata-ca-v0.8-un-context-i18n-release-2` | error 0、warning 10 |

warning 10件は、国勢調査9 sourceの再配布条件確認と、国別計画資料未取得である。数値・リンク・言語機能の検証失敗ではなく、公開画面にも取得上の不足として残す。

## 画面検証

ローカルHTTP環境の実画面で次を確認した。

| 操作 | 結果 |
| --- | --- |
| `lang=en` | 英語ナビゲーション、英語系列名、`53,870,471`、`+22.8%` |
| EN → ES | URLが`lang=es`になり、ナビゲーション、Censoリンク、国連中位推計の説明、数値が`53.870.471`／`+22,8%`へ更新 |
| ES → 日本語 | URLが`lang=ja`になり、ナビゲーション、国勢調査リンク、国連比較の説明が日本語へ更新 |
| 基本情報 | 国勢調査合計`43,883,591`とUN 2026合計`53,870,471`をそれぞれの年・系列付きで表示。UNの空欄カードは重複表示しない |
| 7か国Censusリンク | 7／7について表示年と公式Census案内URLが一致。統計機関と採用表リンクも別表示 |
| 上位再選択 | 実画面でLa Ceiba市から県欄の`Whole Atlántida`を選択。URL・見出し・階層選択がAtlántida県へ変わり、市選択が解除された。指標、期間、`lang=en`は保持 |

## 公開

GitHub、FTPS、公開URLの結果は公開作業後に、この節へ対象commit、ファイル数、hash照合結果を追記する。

## 未実施・制約

- 国別計画法・計画資料はこの中米地域入口には未統合で、Planning画面に未取得状態を表示する。
- UI共通語と主要操作は3言語化したが、原資料名、出典説明、データ定義、地名は原語または採用データの名称を保持する。国別版では公式用語の対訳台帳を追加する。
- モバイル実機、読み上げソフト、ログイン後の文書取得は今回の変更範囲では未実施。
