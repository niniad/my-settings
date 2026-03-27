---
name: amazon-competitor-analyze
description: >
  Amazon競合データの取得・整形・8軸クリエイティブ分析スキル。
  SP-API + agent-browser でデータ取得 → CSV整形 → 8軸分析 → competitor-analysis.md 出力。
  トリガー: 「競合分析」「competitor-analyze」「競合データ取得」「8軸分析」「ASIN分析」
  「レビュー取得」「A+取得」「BSR取得」「販売数推定」「競合画像」
allowed-tools: Bash(uv run *), Bash(npx agent-browser:*)
---

# Amazon Competitor Analyze

SP-API + agent-browser でAmazon.co.jp競合データを取得し、8軸クリエイティブ分析まで一括実行する**グローバルスキル**。
どのプロジェクトからでも呼び出し可能。スクリプトは絶対パスで動作。

## データ保存先

### Eagle（元データ保管庫）
JSONはtmp→Eagle登録→tmp削除のパターン。

```
Eagle: Amazon競合データ/
  {product_name}/             ← --product で指定（例: マザーズリュック）
    {子ASIN}/                 ← fetch_catalog.pyに渡されたASIN単位
      catalog_YYYYMMDD.json   ← SP-API生データ（_raw_parent含む）
      reviews_YYYYMMDD.json   ← レビュー生データ
      aplus_YYYYMMDD.json     ← A+コンテンツ生データ
      {ASIN}_APLUS_01.jpg     ← A+画像
```

### ローカル（AI作業用CSV）
build_competitor_csv.py でEagle内JSONをCSV化。Phase 0 の入力データ。

```
ec/products/{slug}/competitor-data/
  catalog.csv   ← 全競合の商品仕様（_raw_parentフラット化。カラム動的）
  reviews.csv   ← 全レビュー（variation付き）
  images.csv    ← 商品画像URL + A+画像パス + テキスト抽出結果
```

**ASIN用語**:
- `child_asin`: Eagleフォルダ名のASIN（fetch_catalog.pyに渡された子ASIN）
- `parent_asin`: 真の親ASIN（_raw_parent.relationships から解決）

## スクリプトパス

```
C:/Users/ninni/.claude/skills/amazon-data/scripts/
  fetch_catalog.py         ← SP-API Catalog Items取得（親ASIN自動解決・全バリエーション展開）
  fetch_reviews.py         ← agent-browserでレビュー取得（バリエーション別情報含む）
  fetch_aplus.py           ← agent-browserでA+コンテンツ取得
  bsr_to_sales.py          ← BSR→販売数変換
  build_competitor_csv.py  ← Eagle内JSON → ローカルCSV参照用ファイル生成
```

---

## 事前確認（agent-browser使用時）

fetch_reviews.py・fetch_aplus.py は agent-browser を使用する。実行前に確認:

1. **Eagleが起動している**こと
2. **agent-browserのAmazonセッションが確立されている**こと
   - 初回またはセッション切れの場合: `npx.cmd agent-browser --session-name amazon-jp open https://www.amazon.co.jp` でブラウザを開き、Amazonにログインしてからスクリプトを実行する
   - セッションは `~/.agent-browser/sessions/amazon-jp-default.json` に自動保存される
   - 一度ログインすれば次回以降は自動再利用

---

## コマンドリファレンス

### fetch_catalog.py — 商品情報・BSR・全バリエーション画像取得

SP-APIを使用。Chromeは不要。

```bash
# 子ASINでも親ASINでも可（自動で親に解決して全子ASIN取得）
uv run C:/Users/ninni/.claude/skills/amazon-data/scripts/fetch_catalog.py \
  --asins B091NQ5WXY B0FB8Z8RZV --product マザーズリュック

# 複数商品（同じ親の子ASINを複数渡しても1回だけ取得）
uv run C:/Users/ninni/.claude/skills/amazon-data/scripts/fetch_catalog.py \
  --asins B000AAA B000BBB B000CCC --product マザーズリュック
```

**取得内容**: 商品名・箇条書き・BSR（カテゴリ別）・全バリエーション（色・サイズ等）・画像・カテゴリ

### fetch_reviews.py — レビュー取得（agent-browser使用）

```bash
uv run C:/Users/ninni/.claude/skills/amazon-data/scripts/fetch_reviews.py \
  --asins B000PARENT1 B000PARENT2 --product マザーズリュック

# 取得件数を増やす場合
uv run C:/Users/ninni/.claude/skills/amazon-data/scripts/fetch_reviews.py \
  --asins B000PARENT --product マザーズリュック --max-reviews 100
```

**注意**: 親ASINを渡すこと（全バリエーションのレビューを一括取得）。

**レビューJSON**: 各レビューに `variation` フィールド（例: `"色: ブラック"` / `null`）を含む。

### fetch_aplus.py — A+コンテンツ取得（agent-browser使用）

```bash
uv run C:/Users/ninni/.claude/skills/amazon-data/scripts/fetch_aplus.py \
  --asins B000PARENT1 B000PARENT2 --product マザーズリュック
```

**注意**: 親ASINを推奨（Amazonが自動的にデフォルトバリエーションにリダイレクト）。

### bsr_to_sales.py — BSR→販売数推定

```bash
uv run C:/Users/ninni/.claude/skills/amazon-data/scripts/bsr_to_sales.py \
  estimate --bsr 500 --category baby_products

uv run C:/Users/ninni/.claude/skills/amazon-data/scripts/bsr_to_sales.py \
  estimate --bsr 500 --category baby_products/diaper_bags
```

---

## build_competitor_csv.py — Eagle → ローカルCSV変換

Eagle内の元データ（JSON）を読み取り、3つのCSVファイルをローカルに出力する。

```bash
# 基本（CSV生成のみ）
uv run C:/Users/ninni/.claude/skills/amazon-data/scripts/build_competitor_csv.py \
  --product マザーズリュック \
  --output C:/Users/ninni/projects/ec/products/mothers-backpack/competitor-data

# テキスト抽出付き（Gemini Vision で商品サブ画像をOCR。API課金あり）
uv run C:/Users/ninni/.claude/skills/amazon-data/scripts/build_competitor_csv.py \
  --product マザーズリュック \
  --output C:/Users/ninni/projects/ec/products/mothers-backpack/competitor-data \
  --extract-text
```

**出力ファイル（3つ）**:

| CSV | 内容 | 主なカラム |
|-----|------|-----------|
| `catalog.csv` | 商品仕様一覧（_raw_parentフラット化。カラムは動的） | child_asin, parent_asin, title, brand, color, size, bsr_rank_1, bsr_category_1, bullet_1-N, has_reviews, has_aplus |
| `reviews.csv` | 全レビュー | child_asin, parent_asin, variation, star, title, body, date |
| `images.csv` | 商品画像URL + A+画像パス + テキスト | child_asin, parent_asin, source, variant, url, eagle_path, text |

**catalog.csv の特徴**:
- SP-APIの `_raw_parent` を完全フラット化。カラムは商品・カテゴリにより動的に変わる
- BSR、寸法、重量、バリエーション情報も含む
- `has_reviews` / `has_aplus` でデータ有無を確認可能

**images.csv の特徴**:
- `source=product`: 商品画像URL（MAIN/PT01〜PT08）。`--extract-text` でサブ画像のテキストをOCR
- `source=aplus`: A+画像（eagle_path付き）。A+テキストデータをtext列に紐付け

**reviews.csv のクリーンアップ**:
- `variation`: "Amazonで購入" → 空欄に自動補正。"色: ブラック" 等は保持
- `title`: スクレイパーバグで星評価が入っている場合 → 空欄に自動補正

### データ取得後の自動実行

fetch_catalog / fetch_reviews / fetch_aplus でデータ取得が完了したら、
**必ず build_competitor_csv.py を実行**してローカルCSVを最新化すること。

---

## Phase 0: 競合クリエイティブ分析（8軸）

CSVデータ + Eagle画像を入力として、商品ページのクリエイティブ戦略を分析する。
**出力**: `ec/products/{slug}/competitor-data/competitor-analysis.md`

### データ参照方法

| やりたいこと | 方法 |
|------------|------|
| 競合の商品仕様を比較 | `catalog.csv` を Read |
| レビュー分析 | `reviews.csv` を Read |
| 競合画像のテキスト分析 | `images.csv` の `text` 列を Read |
| 競合画像を視覚的に分析 | `images.csv` の `url`（商品画像）または `eagle_path`（A+画像）を Read |

### 8軸分析

| # | 軸 | 見つけるもの |
|---|-----|-------------|
| ① | メッセージング | 競合が言っていない訴求軸。「誰も言っていないが顧客が求めていること」 |
| ② | ビジュアル戦略 | 視覚的に違う見せ方。構図・背景・モデル・撮影スタイルの差 |
| ③ | 購買心理フロー | 画像の並び順から読み取れる意図。最も効果的な訴求順序 |
| ④ | レビュー・VOC | 顧客が本当に重視すること。星3-4のレビューに差別化ヒントあり |
| ⑤ | サムネイル戦場 | 検索結果で目を引く方法。「自社が埋もれないか」 |
| ⑥ | 価格帯別ポジショニング | 価格帯に合う訴求スタイル。安すぎると品質を疑われる |
| ⑦ | A+ベンチマーク | 商品説明欄の構成パターン。競合が力を入れているモジュール |
| ⑧ | 時系列変化 | 画像変更とBSR変動の因果。「変えたら売れた」パターン |

### 分析の実行方法

**別エージェント（Evaluator パターン）で実行する。**
メインの会話コンテキストとは別に Agent tool で起動し、
CSVデータ + Eagle画像を渡して分析結果を出力させる。

1. Agent tool で `subagent_type=general-purpose` を起動
2. Evaluator に渡す:
   - `ec/products/{slug}/competitor-data/catalog.csv`
   - `ec/products/{slug}/competitor-data/reviews.csv`
   - `ec/products/{slug}/competitor-data/images.csv`
   - Eagle 内の競合商品画像（images.csv の url/eagle_path 参照）
3. 8軸分析を実行
4. 出力: `ec/products/{slug}/competitor-data/competitor-analysis.md`

### competitor-analysis.md フォーマット

```markdown
# Phase 0: 競合クリエイティブ分析

対象: {ASIN}（{商品名}）
分析日: YYYY-MM-DD
データソース: amazon-data CSV + Eagle画像

## 自社現状
- BSR / 価格 / 月間販売数 / 評価数 / A+有無

## 分析対象（競合Top10-20）
| ASIN | ブランド | BSR | 価格 | 評価数 | A+有無 |

## 8軸分析
### ① メッセージング
### ② ビジュアル戦略
...

## 差別化方針
- 訴求すべきポイント
- 避けるべきポイント（競合と同じになる表現）
- 優先度付き行動リスト
```

---

## トリガー例

| ユーザーの依頼 | 実行コマンド |
|--------------|------------|
| 「マザーズリュックの競合データを取得して」 | `fetch_catalog.py` → `build_competitor_csv.py` |
| 「このASINのレビューを取得して」 | `fetch_reviews.py` → `build_competitor_csv.py` |
| 「A+コンテンツを取得して」 | `fetch_aplus.py` → `build_competitor_csv.py` |
| 「BSR 500 のベビー用品の月間販売数を推定して」 | `bsr_to_sales.py estimate --bsr 500 --category baby_products` |
| 「競合データをCSVに更新して」 | `build_competitor_csv.py` |
| 「競合画像のテキストも抽出して」 | `build_competitor_csv.py --extract-text` |
| 「競合分析して」「8軸分析して」 | CSV + Eagle画像 → 8軸分析 → `competitor-analysis.md` |
| 「competitor-analysis を更新して」 | 最新CSV + Eagle画像で再分析 |

---

## 注意事項

- **SP-API**: 無料。レート制限 2 TPS（自動管理）
- **agent-browserスクレイピング**: 20商品以下・月2回まで。自動定期実行禁止
- **セッション切れの症状**: 0件取得・ログインページにリダイレクト → 上記「事前確認」を実行
- **セラスプ月額契約**: 新カテゴリ市場規模・キーワード逆引きはSP-APIでは代替不可 → 必要時のみ

## 関連スキル

| 状況 | スキル | 説明 |
|------|--------|------|
| 取得した画像・JSONをEagleで整理・検索したいとき | `/eagle` | Eagle APIで画像管理・フォルダ整理 |
