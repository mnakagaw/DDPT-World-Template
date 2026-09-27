# Kazakhstan country lesson audit — 制作者側の部分確認

2026-09-27 JST、branch `codex/asia-domestic-20260926`、ignored候補 `generated/kazakhstan-areadata-20260927`、dataset SHA-256 `343084b4737934eeb3bc1e2fb3329ca5c4f6c871cbd2265d53b77be3307dff85`。Windows/PowerShell、Node、Python/openpyxl、Poppler、`127.0.0.1:8767`のローカルpreviewとCodex in-app browserで確認。`templates/COUNTRY_LESSON_AUDIT.md`の12観点に対する制作者側の部分確認。対象コードcommitはhandoffに記録。現地担当者・独立監査は未実施。

| ID | 判定 | 根拠・不足 |
|---|---|---|
| UA01 | 制約付き | 初期preflightは国内source未調査。公式9原本のhash、3 workbookの34 sheet・8,671数値風セルと数値列、計画12表・1,627数字含有欄、国勢調査目次18表を棚卸し。採用列は限定。他の本文・数値列と国際共通source availabilityは未監査。 |
| UA02 | 制約付き | 7月sheet 2だけで人口全体の不存在とせず、sheet 3・8月表・2021国勢調査を取得。国勢調査印刷p.5/29を画像照合。2021地方表は地理が違うため保留。 |
| UA03 | 制約付き | 2026人口249行をKATO全20＋228コードへ親・行順・名称で照合。KATO版は人口参照日後。NSDI属性254 featureで37候補ID欠落・重複あり、公式図形未採用。 |
| UA04 | 制約付き | 18国内指標・2,330直接値。7月の男女・都市農村・親子・全国、8月の構成値を検算。7月・8月・2021国勢調査・WDIを別時点／方法とし、親の公表値を使用。 |
| UA05 | 制約付き | 11代表地域の診断CSV/HTML/Markdown、計画HTML、根拠CSVを生成・照合。ブラウザーで全国・Akmola／Burabay・Ulytau・Almaty oblast／cityを確認。DDPT全主要操作対照、狭幅・現地利用者は未実施。 |
| UA06 | 制約付き | Burabay 69,977人→同じ親Akmola全体793,020人を上位選択で再選択し、見出し・値・URLを確認。計画資料の地域残留も確認。メモ・保存・全指標同時の回帰は未実施。 |
| UA07 | 制約付き | 全国20/20、Abay12/12、Akmola20/20、Astana6/6の7月人口比較を確認。図形0でも全件表と出典がある。地区級8月・2021地方は欠測で、全国WDIを地方へコピーしない。注目・全頁印刷は未実施。 |
| UA08 | 制約付き | 2021国勢調査の地方値を2026年KATOへ自動結合しない。BNS7月／8月とWDIはindicatorを分ける。全テーマ比較、歴史版の完全照合は未実施。 |
| UA09 | 制約付き | Adilet法令、Burabay承認記載、Ulytau本文、Akmola／Almaty oblastのlink-only計画、Akmola予算報告link-onlyを分ける。Burabayの計画は他地域に残らない。支出・公式評価は未取得。 |
| UA10 | 未実施 | 個別計画の承認原本、適用manual/form、投資 annex、各階層の法定提出様式を網羅していない。汎用HTML/Markdownを法定提出物としない。 |
| UA11 | 制約付き | 11地域の診断・根拠CSVから401値／欠測セルを原Excel等へ照合。2021全国5値、比較初行・末行・件数、資料の地域限定を確認。Word/PDF未採用。全頁印刷、狭幅、多言語の切れは未実施。 |
| UA12 | 制約付き | 9 hash→import（2回同一dataset SHA）→validator 0 errors/warnings→build→実出力照合。`npm run check` 167件、`npm test` 219/219。Kit取込、Hosting/Public、独立`ACCEPT`は別。 |

[原本と採否](kazakhstan-bns2026-source-audit-2026-09-27.md)、[表・列台帳](kazakhstan-bns2026-table-audit-2026-09-27.json)、[manifest](../../config/kazakhstan-2026-source-manifest.json)を参照。**42件合格とは報告しない。独立`ACCEPT`前に公開しない。**
