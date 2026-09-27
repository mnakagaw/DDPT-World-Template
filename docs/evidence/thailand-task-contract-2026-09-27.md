# Thailand Task Contract・差分台帳（AI記入、2026-09-27）

`templates/TASK_AND_CHANGE.md`に対応。作業ID `asia-THA-20260927`。開始AreaData commitはVNM引き継ぎ版 `b50330d6acc432a74821ebae0d182b5bb737e182`。独立国別候補でNESDC 2024p GPPとNSO/BORA、計画sourceを調査・部分接続する。納品はPrivate GitHubのコード・台帳。独立`ACCEPT`とTHA固有Hosting/Public先は未取得。

| 契約 | 実施と限界 |
|---|---|
| 版と保護 | dataset schema 0.2。DDPT参照、他国作業、本体テンプレートをTHA固有値で変更しない。原本・候補siteはGitへ入れない。 |
| 原本・再現 | NESDC Excel、GPP/計画目録、6頁PDFをbytes/hash固定。新規候補生成→固定原本取得→audit→import→validate/build→actual-output verifier。失敗時は旧正常版を保持。 |
| 採用範囲 | `PER CAPITA!C:E`の国＋77省、current-price 2024p `AE`の21固有産業行。全国＋7地域＋77省の数値を検算。重複別名/小計、過去年、CVM、clusterは採用しない。 |
| 矛盾処理 | `NO!AE691` Kam Phaeng Phet人口は`PER CAPITA!D47`と1.53195298千人違う。GPP/1人当たり整合と77省完全和を満たす`D47`だけを採用し、矛盾値は監査JSONに残す。 |
| 地理比較 | NESDC経済地域コードはDOPA法定コードと認定しない。77省原表行を非重複比較し、7経済地域は監査のみ。適合polygon0。親は原表直接値、子から補填しない。 |
| 計画 | NESDC草案表示付きガイドと公式目録は全国参考。Chiang Mai計画所在は本文timeoutのため全国の未検証参考例に限定。省別計画承認・予算・実績・評価として帰属させない。 |
| UI・出力 | 5例の診断CSV/HTML/Markdown、計画HTML、根拠CSVで24原値とlocatorを照合。全国比較77件×24指標の印刷HTML全件を検査。ブラウザーで選択連動と資料の地域/全国分離を確認。 |
| 検証 | Validator 0 errors/warnings、build、5例の実出力verifier、共有check/test。42件全件、Word/PDF、狭画面/低性能、タイ語、独立監査は別記録。 |
| 公開 | 公開可能な公式source所在だけKitへ渡す。原本、観測値、コード/境界の認定、地域資料の承認や国別採用をKitへ移さない。Hosting/Publicは実施しない。 |

| 差分ID | 変更 | 根拠・影響 |
|---|---|---|
| THA01 | 初期provider図形77件を外し、NESDCの77省統計報告行へ置換 | 2017年図形とNESDC 2024pのコード・版が一致する保証がない。境界なしの既存選択・全表代替を使う。 |
| THA02 | GPP3項目と2024p current-price21産業を専用指標へ分離 | 初期WDI全国、NSO常住国勢調査、BORA登録人口を自動同一化しない。産業の親/詳細を全件加算しない。 |
| THA03 | 詳細表人口の矛盾値を保留 | 誤った分母を利用者へ出さず、同一原本内の差を再現可能に残す。 |
| THA04 | NESDC計画ガイドとChiang Mai計画所在を全国参考へ接続 | 草案表示・本文timeoutのため現行法的効力や選択省の計画承認を作らない。 |

**判定: 2024p経済統計のlocal partial / unpublished。** 法定行政コード、国勢調査、計画・予算・実績は別の証拠が必要。
