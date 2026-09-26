# Sri Lanka country lesson audit — producer-side partial check

2026-09-27 JST、branch `codex/asia-domestic-20260926`、開始commit `40ef465d26e18a79596139114b8027fc700effbc`、ignored候補 `generated/sri-lanka-areadata-20260927`。dataset SHA-256は候補内 `evidence/LKA_IMPORT_RESULT.json`。Windows/PowerShell、Node preview `127.0.0.1:4184`、Codex in-app browser。`templates/COUNTRY_LESSON_AUDIT.md`の12観点に照合した制作者確認。独立42シナリオや現地受入ではない。

| ID | 判定 | 根拠と残件 |
|---|---|---|
| UA01 | 制約付き | DCS目録の23番号A表、9 GN表、コードXLSX、最終PDFを取得。A5/A14/A16の全366行・採用数値列と重複分母を監査。残る20番号表・他GN表はsheet extentのみで数値セル・意味は`priority_unassessed`。 |
| UA02 | 制約付き | 34原本と目録HTMLをhash固定。最終PDF p68のTable 3.2を視認。A5人口・A14水源・A16トイレの男女/年齢/カテゴリー計、国→郡→DS算術を確認。他表と報告書残りは未意味監査。 |
| UA03 | 制約付き | 全国・9州・25郡・340 DSを統計単位として区別。公式コード/GN 14,008キー一致、DSの16名称差を値と郡で対応。2024合法境界時点・自治体対照・公式polygonは未確認。 |
| UA04 | 制約付き | 30指標・10,989直接値。人口21,781,800人と全国6,111,315世帯を別単位として扱う。州人口のみ直接報告値、州世帯/年齢は欠測。GN暫定年齢の8 DS差を採用しない。WDI年央推計と合算しない。 |
| UA05 | 制約付き | 全国→Western→Colombo郡→Colombo DSを実画面で選択し、人口・世帯・水源・トイレ、URLと見出しを確認。別条件の遠隔州/欠測と狭画面は未確認。 |
| UA06 | 制約付き | Colombo DS後に同じColombo郡全体を階層selectorで選び直し、URL/主値が292,089人・72,479世帯から2,375,415人・661,822世帯へ切替。地域別メモの保存継続は未実施。 |
| UA07 | 制約付き | WDI全国値はDSに補完されない。9州・Western3郡・Colombo13 DSの比較出力全行/初末/和を確認。画面内検索・行注目と他指標の不変性は未実施。 |
| UA08 | 制約付き | 不適合の初期provider図形を除外し、地図なし代替。州世帯など親の直接値なしは欠測に保持。旧年、対応polygon、他年度境界は未取得。 |
| UA09 | 制約付き | Gazette所在とColombo市資料所在を調査したが本文・効力・jurisdiction未採用。Colombo郡計画画面で資料0件。法令所在を計画採択・予算執行・評価へ昇格しない。 |
| UA10 | 未実施 | Municipal/Urban Councils/Pradeshiya Sabhasの適用法、計画・予算様式、発行者とjurisdictionを未照合。一般HTMLを公的様式としない。 |
| UA11 | 制約付き | 8例の診断CSV/HTML/Markdown、計画HTML、根拠CSVの地域・2024年・値・セル/頁出典を照合。全比較行を印刷HTMLで検査。PDF/Word作成・描画と狭画面は未実施。 |
| UA12 | 制約付き | 原本pin→inventory→import→validator→build→verifierを再現。共有check/test完了。Kit feedback、独立監査、Hosting/Publicは別管理。 |

候補内 `LKA_CPH2024_AUDIT.json`、`LKA_IMPORT_RESULT.json`、`OUTPUT_VERIFICATION.json`を参照。**42件合格と報告しない。** 残る数値列の意味・出典定義、対応境界・自治体、計画・予算本文、利用条件、現地利用と独立監査が残る。
