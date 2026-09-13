# DDPT World Template

**国名を指定すると、取得可能なデータを収集してDDPT型の国別ダッシュボードを作るためのPrivateテンプレートです。**

実行テンプレート：0.2.1。共通UX仕様：0.2（改善後のv1.0採用は別途検証）。

地域診断では、市・県の選択後に同じ所属先のRegion／Subregionを選び直すと、下位選択を解除して上位全体へ切り替える。指標・年を保持し、親の値が未取得なら親の欠測を示す。階層は国別の地域台帳から構成する。[操作契約](docs/02_COMMON_SPEC.md)に、所属表示と上位全体の選択を区別する規則を記載した。

## 新しいAIプロジェクトへの依頼

```text
https://github.com/mnakagaw/DDPT-World-Template を参照して、ウガンダ版を作って。
START_HERE.mdから読み、取得可能な公式データの収集から、動作するサイトと出力の検証まで進めてください。
```

国名を替えて利用できます。AIが開始シート、資料台帳、機能の採用判断を作ります。Privateリポジトリを読めるGitHub接続が必要です。

**[START_HERE.md](START_HERE.md)から開始してください。** 初期生成の後、現地統計局・国勢調査・公式行政区分・計画・予算資料の収集と統合を続ける手順です。

## 実行できること

| 段階 | 実装・手順 |
|---|---|
| 国の特定 | 英語名・ISOコード・日本語名等を解決。曖昧な入力と地域集計グループを国として採用しない |
| 初期自動収集 | World Bank WDIの12指標の全国系列、geoBoundariesの取得可能なADM1参照境界 |
| 記録 | 原資料、取得日時、SHA-256、出典、期間、境界の出所・版・利用条件、取得失敗と不足項目 |
| サイト生成 | 地域診断・テーマ比較・計画資料の独立ページ、地域保持URL、検索、地図、図表、出典・欠測 |
| 出力 | 数値CSV、出典付きの編集可能なMarkdown基礎資料、印刷用HTML。国別公式様式への適応は後続工程 |
| 国別の仕上げ | AIが国内公式資料を収集し、再実行できるアダプターを追加して地方値・資料を統合、再生成・検証 |

全国値を地方へ配分しません。geoBoundariesのIDは公式行政コードではなく、古い境界や行政・統計分類の違いを含む場合があります。公式コード・現行区分との対応は国別に確認します。

初期収集だけの状態は、地方統計・承認済み計画が揃った完成版ではありません。取得可能な国内資料を調べた結果と、未取得・未照合・未検証を残すことを作業手順で必須にしています。

## コマンドで初期生成

Node.js 22以降。実行時の外部npm依存やAPIキーは不要です。実データの取得にはネット接続が必要です。

```sh
gh repo clone mnakagaw/DDPT-World-Template ./DDPT-World-Template
node ./DDPT-World-Template/scripts/create-country.mjs --country "ウガンダ" --out ./uganda-dashboard
node ./DDPT-World-Template/scripts/serve.mjs --dir ./uganda-dashboard/site --port 4173
```

`http://127.0.0.1:4173/`を開きます。作成先が既にある場合は上書きせず終了します。失敗時も取得済みの証拠を残します。ネットワーク障害で一部を取得できなかった場合は不足を記録し、取得できた情報で生成します。数値を１件も取得できなければ成功終了しません。

地方データと資料を`data/dashboard.json`へ統合した後は、テンプレートから次を実行します。

```sh
node scripts/validate-country.mjs --project ../uganda-dashboard
node scripts/build-country.mjs --project ../uganda-dashboard
```

生成器が管理する`site/`のコードを直接編集する場合、再構築で戻ることに注意してください。恒久的な国別変更は、国別アダプター・設定と、案件用に管理した生成コードへ反映します。テンプレート本体に一国のデータを混ぜません。

## GitHub Actionsでの生成

`Build country baseline`を手動実行し、`country`に国名またはISOコードを入力すると、初期収集・サイト・証拠をArtifactとして保存します。自動のWeb公開や、AIによる国内資料調査までは行いません。国内公式資料の調査は、新しいAI案件が[国別作業手順](docs/COUNTRY_AGENT_WORKFLOW.md)に沿って続けます。

Artifactは７日間保存します。必要な成果は案件側へ取得してください。取得先の障害や対象国のデータ状況によって収集範囲は変わります。

## 構成と検証

```text
START_HERE.md             新しいAI案件の入口
lib/                     収集、検証、生成、CLI共通処理
scripts/                 初期生成、再構築、検証、ローカル配信
scaffold/site/           DDPT型画面の共通実装
prompts/                 国名だけで始める依頼文
docs/                    共通仕様、国別適応、公式資料収集手順
templates/               記入様式、受入試験、設計用設定一覧
references/              元のユーザビリティレビュー
tests/                   欠測、地域状態、出典、出力、取得障害等の回帰検査
.github/workflows/       Windows/LinuxのCIと国別初期生成
```

```sh
npm run check
npm test
```

CIはWindows/Linux、Node 22/24で検証します。初期収集の結果は[0.2検証記録](docs/VALIDATION_v0.2.md)、上位再選択等の変更は[0.2.1検証記録](docs/VALIDATION_v0.2.1.md)に保存します。

## 維持するモデル

共通化するのは「地域から総合的に読む」「テーマから地域間を比べる」の役割、地域選択の連動、出典・対象範囲・取得操作です。国別制度、指標、言語、粒度、頻度、図表・提供機能は根拠に応じて適応します。

- [共通デザイン・機能仕様C01～C07](docs/02_COMMON_SPEC.md)
- [国別設定とデータ条件](docs/03_COUNTRY_AND_DATA.md)
- [公式資料のアダプター追加](docs/SOURCE_ADAPTER_GUIDE.md)
- [DDPT参照版](docs/01_DDPT_REFERENCE.md)・[ウガンダの教訓](docs/UGANDA_LESSONS.md)
- [添付レビュー９所見](docs/REVIEW_TRACEABILITY.md)・[26の受入シナリオ](templates/ACCEPTANCE.md)

既知のF01～F03（地域引き継ぎ、文書取得、集計定義・基準日）の解消を確認してから、改善後の共通UX v1.0を採用します。テンプレート0.2の初期生成と、その採用判断・各国の実利用者による受入は分けて扱います。

このリポジトリはPrivateの再利用テンプレートです。取得データ・境界・第三者資料には、それぞれの出典に記録した利用条件が適用されます。
