# マレーシア国別候補・開始シート（AI記入、2026-09-27）

`templates/COUNTRY_START.md`に対応。アジア50件の段階3・東南アジア、`MYS`。独立したignored候補 `generated/malaysia-areadata-20260927`。**DOSM地方統計とKLの計画資料の部分成果・未公開**。[原本監査](malaysia-dosm-source-audit-2026-09-27.md)と[Task Contract](malaysia-task-contract-2026-09-27.md)を参照。

| 項目 | 確認した範囲 | 不足・次の行動 |
|---|---|---|
| 納品・作業場所 | AreaData `codex/asia-domestic-20260926` にコード、原本hash台帳、監査、source所在を保存。原本と生成siteはignored候補。参照実装0.4、dataset schema 0.2。 | 独立`ACCEPT`、MYS専用Hosting/Public先、現地運用者・更新担当・回線/言語条件は未設定。UX v1.0最終採用とは区別。 |
| 利用目的・地域 | 全国→16州/連邦直轄領→156統計地区を選び、統計診断・比較・根拠出力を行う。4つの単一州/FT地区重複は統合して数えない。 | 地区とPBT/法定計画主体の一致、公式コード・境界版、Sabah/Sarawak改編は未確認。 |
| 国内統計 | DOSM CSV6本の全列・674,676数値セルを棚卸し。14指標、1,258観測・明示欠測24。人口は2020国勢調査調整値と2024中間推計、HIESは世帯調査。 | MyCensus 2020地区PDFの全表、CSVの他の年齢/民族/歴史、HIES地区162行のコード照合と採否。 |
| 地理・コード・図形 | MyGeoportal UPI XLSXの16州コード・139 land-districtコード行を取得。DOSM出典行IDを保持。 | UPI/DOSM/PBTの時点付き対照がないため公式コード空欄。2017参照図形16件は不採用。 |
| 計画主体 | PLANMalaysiaのAct 172説明/手引き目録と、DBKLのAct 267官報・KL 2040計画Volume 2を確認。KLの採用5 May 2025、効力11 June 2025。 | 半島各PBT、Sabah、Sarawak、他FTの現行法・計画主体/周期/様式/本文は未確認。旧Act/手引き直PDFは404。 |
| 財政・実施・評価 | DBKL 2025演説の収支**見込額**だけをKLに接続。2014–23予算表と2023年報本文は取得。 | 実支出・執行・計画達成・公式評価、年報財務画像の数値、他地域の資料は未抽出/未収集。 |
| 国際source | 初期WDI全国系列は別定義として保持。`SOURCE_PREFLIGHT`はMYS国内未調査で始まり、DOSM等を今回確認。 | HDX/UNHCR/DTM/IPC/MICS/DHS/WorldPop/GHSL/SALB/WaPORのMYS×テーマ×年×粒度availabilityは未確認。 |
| 利用条件 | OpenDOSM CSVカタログのCC BY 4.0表記を保持。原本13件のhashをmanifestへ固定。 | 他のPDF/XLSX/法令の再配布条件、原本のGit同梱可否を個別確認。原本はGitへ入れない。 |

機能採用は地域診断・テーマ比較・計画資料/Markdown/HTML/CSVを**条件付き**。図形未結合時は検索・全件表、資料未取得時は区分ごとの欠測と次の取得先を表示。全国値を地方へ配分せず、親はDOSMの直接値を優先する。内部比較は全国の16州と州内地区の同一指標・同一年の完全台帳で、率を平均しない。比較内の注目は選択地域、他指標、URL、資料、出力先を変えない。Word/PDF、認証変更、法定様式の完成、住民参加・公共投資/評価の成立は採用していない。

代表確認は全国、Selangor/Petaling（親子再選択）、Kuala Lumpur（官報・予算）、Pahang/Cameron Highland（旧名の2020欠測）。5地域の実出力と画面の一部を原本照合済み。スマートフォン、全件印刷、現地担当者、42件全適用試験は未実施。対象commitと検証版は[制作者確認票](malaysia-country-lesson-audit-2026-09-27.md)に記録する。
