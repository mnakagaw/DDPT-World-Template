# Afghanistan Task Contract・差分台帳（AI記入、2026-09-27）

`templates/TASK_AND_CHANGE.md`に対応。作業ID `asia-AFG-20260927`、開始commit `b4a470a037481a2954cc6e37655ed477125391d0`。アジア50国内版の段階2として、公式地方統計・地理・計画sourceを調査し、独立新規ディレクトリに国別候補を作る。ローカル部分候補とPrivate GitHubのコード・監査まで。独立`ACCEPT`と国別Hosting/Public先は未取得。

| 契約 | 実施と限界 |
|---|---|
| 版と保護 | 共通実装0.4候補、schema 0.2。DDPT参照・他国・テンプレート本体を国固有に改変しない。 |
| 原本 | NSIA PDF 18,549,385 bytes/hash固定、76表の見出し・数値列群を棚卸し。Table 4の1404人口3列を採用し、75表と歴史列は`priority_unassessed`。Table 76の世帯不一致を保持。TLSの相手認証未確認。 |
| 範囲 | 国の3指標は遊牧人口150万を含む。別節点の定住範囲と34州に3指標×35対象=105直接観測。全国3＋105=108。全国・定住・WDIを混ぜない。 |
| 地理比較 | 全国→定住範囲の1件は部分被覆と明示。定住範囲→34州は同年・同定義・算術一致の完全集合。公式コードやpolygonなし。 |
| 計画 | 都市法令/計画とMUDH Herat市発表、MoF予算の所在地を参考表示。計画・予算・実施・評価の地域本文は0件。Herat州統計にHerat市計画を適用しない。 |
| UI/出力 | 地域選択で見出し・全指標・資料・URL/出力を同期。Herat→定住範囲再選択をブラウザーで確認。7件の実CSV/HTML/Markdown/計画HTML/根拠CSVを原本locatorと照合。 |
| 検証 | Validatorは0 errors/warnings、build、実出力verifier。共有check/testと42シナリオは別記録。現地実務者確認・独立監査なし。 |
| 再実行 | `create-country`は新規ディレクトリのみ。hash固定PDFを`raw/`へ配置→inventory→import→validate/build→actual-output verifier。原本hashや不整合が変わったら採用を止め再監査。 |

## 差分台帳

| ID | 変更 | 根拠・影響 |
|---|---|---|
| AFG01 | 2007 provider ADM1図形を除外し、定住範囲と34州を追加 | NSIA 1404公式コード・同版図形との照合不可。位置図は未取得代替。 |
| AFG02 | 6人数指標、108直接値、2比較集合 | 国全体と34州の被覆差を維持。親自身の原表値優先、子合計で国値を補完しない。 |
| AFG03 | 都市計画等を所在地の参考として表示 | Kabul市とHerat市を各州の承認済み計画とみなさない。 |
| AFG04 | 初期指標をWDI人口に設定 | 全国根の初期表示に現存する全国指標を使用し、NSIAは別系列で併記。 |

**判定: local partial / unpublished.** Kitへ渡すのは公開公式source所在地のみで、原本・観測・計画状態の採用ではない。
