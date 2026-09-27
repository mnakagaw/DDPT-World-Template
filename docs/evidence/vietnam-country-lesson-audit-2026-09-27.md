# Viet Nam country lesson audit — producer-side partial check

2026-09-27 JST、branch `codex/asia-domestic-20260926`、ignored候補 `generated/vietnam-areadata-20260927`、dataset SHA-256 `8a6709c517ac891d7f707bb5038a8b87a810a54b0fa0e4f84fa79b843020810c`。5例の出力hash・初末行は候補の `evidence/VNM_IMPORT_RESULT.json`、`OUTPUT_VERIFICATION.json` に保存。Windows/PowerShell、Node preview `127.0.0.1:4271`、Codex in-app browserで確認。`templates/COUNTRY_LESSON_AUDIT.md`の12観点に照らす制作者確認であり、独立監査や42シナリオ完了ではない。

| ID | 判定 | 根拠と残件 |
|---|---|---|
| UA01 | 制約付き | UNFPA公式HTML/PDFをhash固定。GSO/UNFPA表1の70行×9列630数値セルと60詳細表の見出しを棚卸し。2～60表の各数値列・意味は `priority_unassessed`、NSO別冊26表の本文は未取得。 |
| UA02 | 制約付き | 表1の9列で男女・都市農村の行内等式と63省・6広域の全国一致を検査。全国値をNSO発表で再確認。9%標本の他分野は全数のラベルで採用しない。 |
| UA03 | 制約付き | 2019年63省・市行を時点付き仮IDとして保持。公式コード・適合図形・2025年34省と3,321社級単位への対照は未確認。旧provider64図形を除去。 |
| UA04 | 制約付き | 64地域×9列の576直接観測。WDI年央推計と国勢調査の時点人口は別指標。親全国は原表の直接値で、63省の完全和でも照合。6広域の重複加算をしない。 |
| UA05 | 制約付き | 全国、Ha Noi、Ha Giang、Ho Chi Minh City、Ca Mauの出力を原値照合。ブラウザーで国→Ha Noi→国、計画資料の地域/全国分離、境界なし代替を確認。テーマ診断全域・狭画面は未実施。 |
| UA06 | 制約付き | ブラウザーでHa Noi後に階層のViet Namを再選択。見出し・URL・指標が全国96,208,984へ即時復帰。地域メモ保持は未確認。 |
| UA07 | 制約付き | 全国の63件比較で初行P01、末行P63、値、CSV/印刷HTML全行を照合。下位比較行への注目が上部対象を保持する実操作は未実施。 |
| UA08 | 制約付き | 2019年国勢調査63省、6広域、2025年現行34省、WDI系列を分離。地域の2019年人口以外の現行テーマは欠測とし、全国値を補填しない。 |
| UA09 | 制約付き | 2025年法令・再編・コードを全国参考、現行Hà Nội/ Kiến Hưng計画は未検証の所在例に限定。Ha Noi 2019の計画/予算/実績/評価区分は未収集と表示。 |
| UA10 | 未実施 | 2025年の権限、現行の地域別様式・章、実計画本文・採択・支出を未取得。汎用計画基礎資料を承認済み計画にしない。 |
| UA11 | 制約付き | 5例の診断CSV/HTML/Markdown、計画HTML、根拠CSVで地域・年・値・PDF頁/URLを照合。Word/PDFと実プリンターでの長表全行・狭画面は未実施。 |
| UA12 | 制約付き | 固定原本hash→audit→import→validator/build→actual-output verifierで再生成。Validator 0 errors/warnings、`npm run check` 159 JavaScript/JSON、`npm test` 218/218。Kit転記、独立監査、Hosting/Publicは別ゲート。 |

**42件合格とは報告しない。** 59詳細表の数値列と別冊地区26表、公式コード/図形、現行計画・財政本文、利用条件、現地確認、独立`ACCEPT`が残る。
