# Pakistan AreaData continuation — 2026-09-27 JST

Branch`codex/asia-domestic-20260926`。Ignored候補`generated/pakistan-areadata-20260927`。**Partial, local, unpublished; independent `ACCEPT`なし。** 原本・採否は[源泉監査](../../evidence/pakistan-pbs2023-source-audit-2026-09-27.md)、契約は[開始シート](../../evidence/pakistan-country-start-2026-09-27.md)と[Task Contract](../../evidence/pakistan-task-contract-2026-09-27.md)、制作者確認は[Lesson Audit](../../evidence/pakistan-country-lesson-audit-2026-09-27.md)。dataset hashはignored候補`evidence/PAK_IMPORT_RESULT.json`と`OUTPUT_VERIFICATION.json`を参照。

## 再実行と確認済み成果

初期生成直後に`evidence/SOURCE_PREFLIGHT.md`とJSONを読み、Pakistan個別の事前所在がないことを確認。PBS公式Excel目録とTable 1の6 XLSXを取得し、7原本のhash・receiptを保存した。33番号付き表・305リンクを棚卸しし、取得済みTable 1の11数値列・737報告単位・19,899数値セルを走査。Table 10 KP誤リンクとTopi Tehsil C474の矛盾を記録。Table 1の4州＋ICTという対象をPakistan根と区別し、4州・136地区へ6直接指標846観測を採用。Table 1全体241,499,431人、WDI 2023年央247,504,495人は別系列。AJK/GB、Tehsil下位値、2019 provider形状を国別値へ結合しない。

```powershell
node scripts/create-country.mjs --country Pakistan --out generated/pakistan-areadata-NEW
# 原本監査にある7つのhash固定原本を raw/ に配置。既存出力へcreate-countryを上書き実行しない。
python scripts/inventory-pakistan-pbs2023.py --project generated/pakistan-areadata-NEW
python scripts/import-pakistan-pbs2023.py --project generated/pakistan-areadata-NEW
node scripts/validate-country.mjs --project generated/pakistan-areadata-NEW
node scripts/build-country.mjs --project generated/pakistan-areadata-NEW
node scripts/verify-pakistan-pbs2023-output.mjs generated/pakistan-areadata-NEW
node scripts/serve.mjs --dir generated/pakistan-areadata-NEW/site --port 4204
```

2026-09-27 Windowsローカルでvalidator 0 errors/warnings、build、9実出力事例、共有check150、test218/218。ブラウザーでWDI初期値、Table 1対象、Bajaur都市0と原表C25、KP州再選択→6,131,296/C7を確認。計画ページにKP法令所在2件が参考として表示され、地域計画・予算・実施・評価は未取得と表示。法令PDFのローカル原本取得は完了していない。

## 残件・次の優先国

1. PBS目録の残り32番号付き表を原表ごとに取得・意味/対象人口を監査し、Table 4以降の母集団をTable 1と混同しない。Tehsil等の下位行はTopiの誤セルを含め、全表で検証する。
2. 2023行政地区とCensus District codeの公式対応、PBS2023コード付きpolygon、現行地方政府境界を取得する。地区の内部行番号は公式コードではない。
3. Punjab/KP/Sindh/Balochistan/ICTごとに現行法令改正、法定計画主体、地域別の承認済み計画・予算・実績・公式評価を原本で確認する。国PSDPを地区計画へ転用しない。
4. 原本再配布条件、残り42シナリオ、モバイル/印刷、現地実務受入と独立`ACCEPT`後に公開判断。国別Hosting/Public先は未指定。
5. AreaData新規確認の公開公式所在をKitに`official_location_identified`のみでfeedbackする。Kitは独立に原本/地理/意味/利用条件を確認する。

Pakistanは南アジアの部分候補に追加するが、**中東段階1の18部分/1調査も全件未完成**。次の未着手国は段階2のAfghanistan。既存Bangladesh候補は独立監査待ちであり、南アジア完成に計上しない。Local、GitHub、Hosting、Publicの状態は別記録とする。

## GitHubとKitへの引き継ぎ

AreaDataのimporter・監査・17件の公式source選定は`c7d2678c0907a2be5c6605f4146376c4a87bd93b`へcommitした。`evidence/KIT_SOURCE_FEEDBACK.json`は同commitをoriginとする177件・24か国のbundleで、Pakistanの17件はいずれも`official_location_identified`。Kitの取込commitは`3af46382fda7941fc88722727f9a82ba321d7fa2`で、Kit側17件はすべて`not_acquired_by_kit_preflight`。Kit branchのremote head一致を確認した。AreaData bundleとこの引き継ぎは同じbranchの後続commitに保存する。[取込台帳](KIT_FEEDBACK_HANDOFF.md)を参照。
