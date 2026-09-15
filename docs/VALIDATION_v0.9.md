# 実行テンプレート0.9.0 検証記録

## 対象

- 中米7か国のCensus採用データ年、直近約3回の調査年、公式リンクの再利用台帳
- 出典欄最上部の世界位置図、採用年による鮮度色、10年以上前の薄赤表示
- マウスオーバーとキーボードフォーカスによる国別履歴表示
- トップページの一覧見出しで「中米7か国」を強調

## 判定規則

- 色はAreaDataに統合済みの採用データ年を基準とする。
- 調査の実施・準備情報と、結果の確認・統合を分ける。
- 2026年時点で10年以上前の採用データを薄赤にする。
- 実施間隔は年の差として表示し、遅延・未実施の原因は断定しない。

## 検証結果

- `npm run check`: 58 JavaScript modules／JSON templatesの構文検査に合格。
- `npm test`: 150件合格、失敗0件。Census履歴台帳、採用年との照合、10年閾値、実施間隔、生成物への新module同梱を回帰検査へ追加した。
- 生成案件: `.work/areadata-ca-v0.9.0-census-history-published`。保存済みの世界取得原本、国勢調査人口v0.7、UN WPP系列、Census履歴v0.9から再生成した。`TEMPLATE_REFERENCE.json`はcommit `804745e`、source state `clean`を記録した。公開dataset SHA-256は`619478355252369271ba7ea3998d9d9a78dd8a4ba7152a08542263b6beb103a3`。
- `node scripts/validate-country.mjs --project .work/areadata-ca-v0.9.0-census-history-published`: errors 0。既存のsource terms reviewと国別計画資料未収集はwarningとして維持した。
- ブラウザ: 日本語・スペイン語切替、世界位置図、中米7か国拡大図、凡例、7か国の表、公式リンクを確認した。
- 操作: 地図上の7か国だけをフォーカス対象とし、マウス操作でニカラグアの「採用2005／2024未統合／直近3回／間隔」を表示。Tab移動でも次国の履歴へ更新されることを確認した。
- トップページ: 「中米7か国から選ぶ」の対象語をアクセント色で強調した。
- GitHub: commit `804745e`を`origin/main`へpushした。
- FTPS: `.work/ftp-deployment-areadata-v0.9.0-census-history-published-2026-09-15.json`。生成サイト18ファイルを`/domains/areadata.net/public_html`へ配置し、18ファイルを退避した。既存の`cgi-bin/.htaccess`は変更していない。
- 公開HTTP: `.work/public-verification-areadata-v0.9.0-census-history-published-2026-09-15.json`。`.htaccess`を除く17ファイルを`https://areadata.net/`から取得し、17/17で公開内容と生成物のbyte一致を確認した。
- 公開ブラウザ: `https://areadata.net/?lang=ja&release=0.9.0`で「中米7か国」のアクセント表示、世界地図と中米拡大図、鮮度色、7か国の調査履歴と公式リンクを目視確認した。
