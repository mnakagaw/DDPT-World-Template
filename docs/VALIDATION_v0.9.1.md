# 実行テンプレート0.9.1 検証記録

## 対象

- Codexタスク `01a0a2b1-7628-74d1-94ca-1c0d8b67066d` のラオス・バングラデシュ国別制作工程
- Public [Census Dashboard Kit](https://github.com/mnakagaw/Census-Dashboard-Kit) commit `88de64677d2691fa8ec83acbf71449943ac04374`
- ラオス、バングラデシュの国別成果に残された `HANDOFF`、資料・表・地理・分野・Word・delivery・公開検証記録
- AreaDataの国別作業手順、開始文、AI依頼文、12観点確認票、共通source台帳への適用

## 確認した制作実績

- ラオス：167地域、42指標、1,896観測、ADM1 18/18・ADM2 148/148境界、18ページWord、公開18ファイルのremote hash一致。
- バングラデシュ：公式64県workbookを64/64取得・hash・統合、580地域、28指標、9,255地方観測、ADM3 483/507境界、原表空欄9セルの維持、18ページWord、公開18ファイルのremote hash一致。
- 上記件数は各国成果の `HANDOFF.md`、`DELIVERY.json`、`VALIDATION.md`、`GEOGRAPHY_REVIEW.md`、`WORD_RENDER_CHECK.md`を照合した。別国へ同じ指標・階層・法制度を転用する根拠にはしない。

## 反映した規則

- 公式catalogueの期待資料を全件列挙し、各資料の処置を閉じる。
- 取得原本の全sheet・table・fieldと採否・非採用理由を残す。
- 6分野、地域コード・境界、計画制度、実出力を完成判定へ含める。
- 国別通常診断は指標別最新確認値と年、テーマ比較は一指標・一地域型・一比較集合・一共通年を使う。
- 世界・広域・研究用databaseでは期間・履歴を保持し、国別の簡潔な表示方針を一律適用しない。
- Word／PDF採用時は隔離rendererで全ページを確認し、画面・CSV・文書を照合する。
- 公開時はupload成功だけでなく、remote read-back、hash、公開画面の代表操作を同じ版で確認する。

## 外部source preflight

`config/external-source-registries.json`へ、Public Kitの次のファイルを上流commit、件数、SHA-256付きで登録した。

| 上流ファイル | 件数 | SHA-256 |
|---|---:|---|
| `jica-priority-country-registry.json` | 142 | `8198e57434b192a7571cf4ee0b38e52e8db78d38543673283ed93fd6215fd516` |
| `jica-priority-source-preflight.json` | 142 | `0ff4f2cb5243f5712599a0477b9c20d2f8f129947cde313fd0d9d8e86aeb42a0` |
| `country-source-registry.json` | 4 | `2be58c3e99bd5ff89a1d23ef5d3c5bb8b130674f79bb9d734236f394ad7e5577` |

142か国はJICA対象国の発見用台帳で、AreaDataのUN M49世界台帳や本リポジトリの22か国詳細調査件数へ加算しない。所在、取得、本文確認、地理照合、指標採用を別の状態として維持する。

## 検証結果

- Public GitHubの `main` とローカル参照cloneのHEADが `88de64677d2691fa8ec83acbf71449943ac04374` で一致した。
- 外部台帳JSONをparseし、3ファイルの件数とSHA-256をローカル上流cloneから再計算した。
- `git diff --check`：空白エラーなし。
- `npm run check`：58 JavaScript modules／JSON templatesの構文検査に合格。
- `npm test`：150件合格、失敗0件。

## この版で実装していないこと

- Public Kitの `verify-delivery` 自動ゲート、国別Word生成、142か国preflightの自動取込はこのリポジトリへ移植していない。
- AreaData公開サイト、FTP配置、国別datasetは変更していない。
- ラオス・バングラデシュの画面をAreaDataの固定デザインとして採用していない。
- 現地自治体職員・研究者による実利用試験は実施していない。

したがって0.9.1は、国別制作の完成工程、証拠契約、外部preflight参照をテンプレートへ取り込んだ文書・運用版である。
