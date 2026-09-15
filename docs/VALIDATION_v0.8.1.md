# 実行テンプレート0.8.1 検証記録

検証日: 2026-09-15 JST

対象: AreaData共通ヘッダー

データschema: 0.2（変更なし）

生成案件: `.work/areadata-ca-v0.8.1-header-release-5`

## 変更

- WorldCountryRiskの横一列の情報配置、小型ピル型切替、選択状態の明確さを参照し、AreaDataの明るい本文と既存色に合わせてヘッダーを再設計した。
- デスクトップではブランド、主要5画面、言語切替を一列に配置した。選択中の画面と言語だけを緑と淡い水色で強調する。
- 1100px以下では主要ナビを2段目へ移し、700px以下では横方向に操作できる。390px幅ではブランドと言語を上段に保持し、本文を圧迫しない。
- 言語を画面内で切り替えた場合も、ブランド説明、言語グループ、各ボタンの読み上げ用ラベルを新しい言語へ更新する。
- 生成HTMLのCSSと起点module URLへテンプレート版を付け、ホスティング側の長期キャッシュに旧ヘッダーが残らないようにする。
- 地域、指標、期間、URL、統計値、出典、出力の機能は変更していない。

## ローカル検証

| 確認 | 結果 |
| --- | --- |
| デスクトップ実画面 | ブランド、5ナビ、言語が一列に収まり、選択状態と余白を確認 |
| 390 × 844px | ブランドと言語が上段、主要ナビが下段。本文との重なりなし |
| 日本語 → スペイン語 | URL、ナビ、ブランド説明、言語グループと3ボタンの読み上げ用ラベルがスペイン語へ更新 |
| `npm run check` | 55 JavaScript module／JSONの構文確認に合格 |
| `npm test` | 147／147合格 |
| `validate-country` | error 0。利用条件確認待ちのsource 9件と国別計画資料未取得をwarningとして維持 |

## 公開

- 公開URL: <https://areadata.net/?country=CAM&territory=CUSTOM%3ACA7&metric=CENSUS_POP_TOTAL&period=latest-available&lang=ja>
- 実装commit: `ec5cee68f78fe4197f0bc21ceaced1a41cca3a52`
- GitHub Actions: `34918410666`、`34918721469`の全jobが成功。
- FTPS: 17ファイルを`/domains/areadata.net/public_html`へ限定して更新し、更新前の17ファイルを`.work/ftp-backups/areadata.net-before-v0.8.1-header-final-2026-09-15`へ保存した。サーバー既存の`cgi-bin/.htaccess`は変更していない。
- 公開照合: HTTPで取得可能な16／16ファイルが生成物とbyte数・SHA-256とも一致した。`.htaccess`はHTTP照合対象外。
- 公開実画面: デスクトップでブランド、主要5画面、言語切替が横一列に表示された。生成HTMLが`styles.css?v=0.8.1`と`app.mjs?v=0.8.1`を参照し、旧CSSの長期キャッシュを回避した。
- 公開言語切替: 日本語からスペイン語へ切り替え、5ナビ、ブランド説明、言語グループ、3ボタンの読み上げ名とURLの`lang`が一致した。確認後は日本語表示へ戻した。
- FTPS receipt: `.work/ftp-deployment-areadata-v0.8.1-header-final-2026-09-15.json`
- 公開照合receipt: `.work/public-verification-areadata-v0.8.1-header-final-2026-09-15.json`
