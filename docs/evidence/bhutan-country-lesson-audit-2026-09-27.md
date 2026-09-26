# Bhutan country lesson audit — producer-side partial check

2026-09-27 JST、branch `codex/asia-domestic-20260926`、ignored候補 `generated/bhutan-areadata-20260927`。dataset SHA-256は候補内 `evidence/BTN_IMPORT_RESULT.json`。Windows/PowerShell、Node preview `127.0.0.1:4185`、Codex in-app browser。`templates/COUNTRY_LESSON_AUDIT.md`の12観点に照らす制作者確認で、独立42シナリオや現地受入ではない。

| ID | 判定 | 根拠と残件 |
|---|---|---|
| UA01 | 制約付き | NSB公式目録の全国＋20地方報告を取得。全20 A2.1の329行×男女・計を数値意味監査し、他641表見出しは機械棚卸しのみで `priority_unassessed`。全国報告の他表も未監査。 |
| UA02 | 制約付き | 23 PDF・２目録snapshotをhash固定。全国Table2.1 p29とHaa A2.1 p41は描画確認。20県表の行・男女・親子計を機械照合。取得済み他数値列と必要資料の探索は続行。 |
| UA03 | 制約付き | 国・20県・64町/Thromde・205農村Gewog部分行を別地理型で維持。2020版BSSGCを2017公式コードと仮定せず、polygon０。法定Gewog全域・Thromde主体との照合が残る。 |
| UA04 | 制約付き | 2017直接値871件。全国727,145と20県、各県のUrban/Rural、町/農村行を男女/計で照合。全国735,553全発見人口は別指標、県へ配分しない。WDI年央推計は独立。 |
| UA05 | 制約付き | 実画面で全国→Haa→Bji、出力で全国・Haa・Thimphuと町/農村行を確認。全診断ページ・幅・全地域型・現地語は未実施。 |
| UA06 | 制約付き | Bji選択後、同じHaa全体を階層selectorで再選択し、Haaの見出し、URL、13,655値、下位解除と資料欄への連動を確認。メモ保持は未確認。 |
| UA07 | 制約付き | 全比較表の20/8/10行、初末・親和・印刷HTMLの全行を出力検査。下部の行注目による上部不変、欠測指標時の画面は未実施。 |
| UA08 | 制約付き | 2017 PHCBと2025 WDIを混ぜず、2020コード・未照合図形も結合しない。比較は同年・同表・非重複構成。別年・率・世界系列は未試験。 |
| UA09 | 制約付き | 2012 rules本文取得、現行力未確認、13th FYP PDFはTLS検証失敗。Haa計画欄は５区分すべて「未収集」で、非存在・未承認と断定しない。実計画/予算/実施/評価は未取得。 |
| UA10 | 未実施 | 現行制度、LG各階層の適用manual/formと実原本の章・欄対応を未監査。汎用出力を公定様式・承認済み計画としない。 |
| UA11 | 制約付き | ６例の診断CSV/HTML/Markdown、計画HTML、根拠CSVを値・2017年・PDF頁・地域名と照合。全比較行を印刷HTMLで検査。PDF/Word作成と全ページ描画、狭画面は未実施。 |
| UA12 | 制約付き | 原本pin→inventory→import→validator→build→verifierを実施。共有check/testも合格。Kit feedback、独立監査、Hosting/Publicは別管理。 |

候補内 `BTN_PHCB2017_ACQUISITION.json`、`BTN_PHCB2017_AUDIT.json`、`BTN_IMPORT_RESULT.json`、`OUTPUT_VERIFICATION.json`が詳細証拠。**42件合格と報告しない。** 残る641表の数値列、全国付表、2017地理・現行制度、実際の計画・財政資料、利用条件、現地利用と独立審査が必要。
