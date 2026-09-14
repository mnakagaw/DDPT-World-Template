# Good Governmentのサービス構成とデータ共有

長期構成は**一つのブランド、二つの公開アプリ、一つの計画モジュール、共通API**とする。利用者の目的が異なるAtlasとData Commonsは画面を分け、地域選択の続きで使うPlanningはAtlas内に置く。

| 公開先案 | 役割 | 主な利用者 |
|---|---|---|
| `goodgovernment.org` | 共通入口、国・地域・データセット検索、事業説明 | 全利用者 |
| `atlas.goodgovernment.org` | 世界から国内地域・自治体までの診断とテーマ比較 | 行政官、援助関係者、市民 |
| Atlas内の`/planning` | 選択地域の計画制度、計画、予算、実施、評価、策定材料 | 自治体・計画担当者 |
| `data.goodgovernment.org` | 国勢調査・地域統計・変数・境界・原資料・抽出・引用 | 研究者、統計担当者、開発者 |
| `api.goodgovernment.org` | Data Commonsの検索・抽出とAtlas用bundle | 各公開アプリ、外部利用者 |

国別の`uganda.goodgovernment.org`等は、共通Atlas内の確認済み国ページへ接続する入口にできる。国別に別のコードベースや独自データ定義を複製しない。認証付き共同編集、住民参加、内部草案、承認フローが必要になった段階で`workspace.goodgovernment.org`を追加し、公開済み資料と根拠はAtlasに残す。

## データの流れ

```text
国際共通source ─┐
国内国勢調査   ─┼─> immutable raw ─> Data Commons正規化・版管理 ─> country bundle ─> Atlas
法令・計画資料 ─┘                                      └──────────────> Planning
                                                        └──────────────> Data Portal/API
```

世界の国際統計、各国の国内統計、法令・計画文書は別datasetとして保存する。確認済みの国ID、地域コード、地域型、境界版、指標定義、期間、母集団の対応だけを接続する。

Atlasは読みやすい診断と計画作業に必要な範囲を受け取る。Data Commonsは細かな地域、全変数、複数年、調査票、境界履歴、抽出条件と再現情報を保持する。Atlasに表示しないデータもData Commonsでは保存できる。

## コードの目標配置

```text
apps/
  atlas/
  data-portal/
packages/
  planning/
  maps/
  indicators/
  geography/
services/
  api/
adapters/
  <country-or-source>/
```

現在のリポジトリは、この構成へ移る前の国別Atlas生成テンプレートである。`scaffold/site/`がAtlasの共通画面、`dataset.planning`とplanning実装がPlanningの基礎、`lib/`とsource台帳が将来の共有adapter/APIの基礎に相当する。Data Portal、公開API、共通オブジェクト保管、サブドメイン配備はまだ実装していない。

## 名称と意味

- **Good Government Atlas**：世界から自治体まで、根拠のある地域診断と比較を行う。
- **Good Government Data Commons**：公開可能な国勢調査・地域統計を、原資料、定義、境界、版とともに再利用するOSS基盤。
- **Good Government Planning**：選択地域の計画制度と根拠資料を確認し、計画策定材料を作る。

「Good Government」は政府の優劣を格付けする意味ではなく、根拠に基づく地域診断と計画策定を支援する基盤だと共通入口で明記する。
