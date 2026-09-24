# AreaData 0.12.1 — 地域別の最新年表示と選択地域見出し

- 確認日：2026-09-24（JST）
- 対象コード：`9d7375e`
- データ版：`.work/areadata-world-v0.12.1-latest-regions/data/dashboard.json`、SHA-256 `77c41cbaaae633b096916b704ae8c3e0ed4cb77e15440618c3f7b266abde2a9b`（0.12.0と同一）
- 環境：Windows、Node.js、headless Chrome、areadata.net HTTPS／FTPS

## 動作

地域診断の11テーマ見出しで選択中の「中米＋カリブ」を太字のラベルとして表示した。期間の既定値 `latest-available` は画面上で「指標ごとの最新年」と表示する。選択地域そのものの採用可能な観測を先に選び、それがない広域指標では同じ年に比較可能な構成国・地域の最新年を選ぶ。地域全体の公式値や承認済み集計値がない割合・平均系の指標については、国別の最小・最大・対象件数・年を示し、広域全体の単一値と誤認されないよう明記する。明示的に年を選んだ場合はその年だけを使う。国別の率を単純平均しない。

公開候補の中米＋カリブでは27指標のうち21指標に国別比較要約が出た。例：栄養不足率は2024年の比較可能な13／36か国・地域、3～51.4％（Dominica～Haiti）。年を2023年に固定すると14／36、2.8～52.6％（Cuba～Haiti）となり、「指標ごとの最新年」に戻すと2024年表示へ復帰した。失業率は2025年の1／36地域（Puerto Rico、5.6％）であり、出典欄も2025年と表示された。これは地域全体の失業率ではない。人口のように完全被覆の承認済み集計値がある指標は、その地域値と年を維持した。

診断CSV、Markdown、HTMLの採用年を画面と同じ選択地域別の解決規則に揃えた。中米＋カリブの「各指標の最新年」診断CSVは見出しを除く999行で、最初の全体人口行は2026年、国別比較行にも各指標の採用年と出典が入る。画面とCSVで地域全体の率を作らない。

## 検証

`npm run check`成功、`npm test` 211件成功・失敗0。候補サイトのデータ検証はエラー0件。今回の配信用プロジェクトは0.12.0の正規化データだけを複製し、原本 `raw/` は含めていないため、ビルド時の原本所在チェックには166件の警告が出る。原本の取得・照合証拠は元の収集案件に残り、正規化データのハッシュは0.12.0と同一である。この表示変更を新しい資料収集や出典監査の合格とは扱わない。

ローカルChromeでは11テーマに太字の選択地域、27指標、21件の国別要約、年の往復切替、CSV出力を確認し、JavaScriptエラーは0件だった。検証記録は候補の`evidence/qa-latest-region.json`と`qa-latest-export.json`、画面は`qa-latest-theme.png`に保存した。公開URLのChromeでも同じ操作と出力を再確認し、`qa-public-latest-region.json`と`qa-public-latest-export.json`に保存した。

## 公開

GitHub `main`へコードをpush。FTPSでは旧版ファイルのハッシュを照合してバックアップした後、変更12ファイルだけを転送し、サーバーから再取得して容量・SHA-256の一致を確認した。データ本体と国別shardは変更していない。更新時刻のみを含む`data/update-status.json`は公開側と旧版ローカルの時刻が異なったため転送対象から外し、公開側を維持した。FTPS受領記録は`.work/ftp-deployment-areadata-v0.12.1-latest-regions-2026-09-24-retry.json`。

公開HTTPSでは変更12ファイルに加え`data/dashboard.json`と`data/supranational.json`の計14ファイルのハッシュ・容量・JavaScript MIMEを確認した。記録は`.work/public-verification-areadata-v0.12.1-latest-regions-2026-09-24.json`。公開画面 `https://areadata.net/territorial/?country=WLD&territory=CUSTOM%3ACAM-CAR&metric=UN_WPP_POP_TOTAL&period=latest-available&lang=ja` で操作・表示・CSVを確認した。

## 未実施

モバイル実機、全42受入シナリオ、全地域・全言語の目視確認は未実施。211件の自動テストを42シナリオの全合格とは扱わない。独自地域の率・平均に公式の同一範囲値がない限り、国別比較の範囲を示し、広域全体の単一値は表示しない。
