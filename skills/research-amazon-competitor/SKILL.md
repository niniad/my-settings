---
name: research-amazon-competitor
description: >
  新商品開発の競合調査スキル。SP-API + agent-browser で競合データを取得し、
  8軸分析・スペックマスタ定義・NocoDB登録まで一気通貫で実行する。
  トリガー: 「競合調査」「スペックマスタ」「競合データ取得」「レビュー分析」
  「どんな商品を作るか」「競合のスペック」「Amazon競合」「新商品の競合」
---

# research-amazon-competitor

新商品開発フローの競合調査モジュール。NocoDB の Amazon競合商品・スペックマスタテーブルを更新する。
**いつでも呼べる。** 前後のスキル（research-profit / research-1688）と非線形に連携する。

## 前提確認（Step 0）

1. NocoDB の企画プロセス管理テーブルで対象カテゴリのフェーズ・ステータスを確認
2. 対象カテゴリの BASE が未存在なら新規作成（BASE + 全テーブルを一括作成）
3. 現在の NocoDB 状態（スペックマスタ・利益シミュレーション等）を読み込み、ユーザーに提示

NocoDB テーブル定義: [references/tools-and-tables.md](references/tools-and-tables.md)

---

## Phase 1: 競合データ取得（SP-API + agent-browser）

> **前提**: Eagleが起動していること。agent-browser の Amazon.co.jp セッションが確立していること。
> セッション切れの場合: `npx.cmd agent-browser --session-name amazon-jp open https://www.amazon.co.jp` でログイン。

| # | タスク | 担当 | コマンド |
|---|--------|-----|---------|
| 1.1 | 競合ASIN一覧を用意（上位10-20商品） | 👤 | ASINリストをメモ |
| 1.2 | 商品情報・BSR・全バリエーション取得 | 🤖 | `fetch_catalog.py --asins ... --product {slug}` |
| 1.3 | レビュー取得（親ASIN） | 🤖 | `fetch_reviews.py --asins ... --product {slug}` |
| 1.4 | A+コンテンツ取得 | 🤖 | `fetch_aplus.py --asins ... --product {slug}` |
| 1.5 | CSV生成 | 🤖 | `build_competitor_csv.py --product {slug} --output ec/products/{slug}/competitor-data` |
| 1.6 | NocoDB: Amazon競合商品テーブルに登録 | 🤖 | catalog.csv の固定列を登録 |
| 1.7 | BSR → 推定販売数変換 | 🤖 | `bsr_to_sales.py estimate --bsr {bsr} --category {cat}` → NocoDB更新 |

スクリプトパス: `C:/Users/ninni/.claude/skills/amazon-data/scripts/`

**catalog.csv の NocoDB 登録方針:**
- 固定列（title, brand, bsr_rank_1, bullet_1〜8 等）→ Amazon競合商品テーブルに直接登録
- 動的列（color, size 等の variation_attrs）→ Phase 3 でスペックマスタ経由で登録

---

## Phase 2: 8軸クリエイティブ分析

Agent tool（Evaluator パターン）で別エージェントを起動し、8軸分析を実行する。

**Evaluator に渡すデータ:**
- `ec/products/{slug}/competitor-data/catalog.csv`
- `ec/products/{slug}/competitor-data/reviews.csv`
- `ec/products/{slug}/competitor-data/images.csv`

**8軸:**

| # | 軸 | 観察内容 |
|---|-----|---------|
| ① | メッセージング | タイトル・箇条書きのKW頻度。誰も言っていない訴求軸 |
| ② | ビジュアル戦略 | 画像構成パターン・枚数・MAINスタイル |
| ③ | 購買心理フロー | 画像の並び順から読み取れる訴求順序 |
| ④ | レビュー・VOC | 5★内の不満・改善要望。頻出KW |
| ⑤ | サムネイル戦場 | 検索結果でどう見えるか |
| ⑥ | 価格帯ポジション | 価格帯別の訴求スタイル分布 |
| ⑦ | A+ベンチマーク | A+構成パターン・注力モジュール |
| ⑧ | 多品番戦略 | 同一ブランドの複数出品パターン |

**出力（事実観察のみ。差別化方針は listing-appeal-map で）:**
→ `ec/products/{slug}/competitor-data/competitor-analysis.md`

---

## Phase 3: スペックマスタ定義

| # | タスク | 担当 | 詳細 |
|---|--------|-----|------|
| 3.1 | レビュー分析 | 🤖 | 不満・要望を頻度順抽出 → スペック優先度に反映 |
| 3.2 | スペックマスタ提案 | 🤖 | 項目名・優先度・判定基準を提案 |
| 3.3 | スペックマスタ確認 | 👤 | AI提案を確認、必要に応じ修正 |
| 3.4 | NocoDB登録 | 🤖 | 商品スペックマスタ + 競合商品スペック値を登録 |

**スペックマスタは research-1688 で以下に使われる:**
- Phase 4: Stage 2 AI支援スクリーニングのキーワード定義
- Phase 5: 1688商品スペックと Amazon競合スペックの横断対比表作成

---

## 次工程

→ **`/research-profit`**（現時点の競合価格帯・推定販売数で利益を試算。仕入コストは推定値）
→ **`/research-1688`**（スペックマスタを使って仕入先を絞り込む）

スペックを見直す場合はこのスキルを再実行（Phase 3 のみでも可）。

---

## AI支援の依頼パターン

| 依頼 | AIの動作 |
|------|---------|
| 「競合データを取得して」 | Phase 1 実行 → CSV生成 → NocoDB登録 |
| 「レビューを分析して」 | reviews.csv 読込 → 不満・要望抽出 → スペックマスタ反映 |
| 「8軸分析して」 | Phase 2 実行 → competitor-analysis.md 生成 |
| 「スペックマスタを作って」 | Phase 3 実行 → NocoDB登録 |
| 「競合のスペック比較を見たい」 | NocoDB から商品スペック一覧を取得して表示 |
| 「進捗を教えて」 | 企画プロセス管理テーブル → 現在フェーズ・次タスク |
