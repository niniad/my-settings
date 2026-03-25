---
name: amazon-data
description: >
  Amazon競合データの自動取得スキル。SP-API + agent-browser で商品情報・BSR・
  画像・レビュー・A+コンテンツを取得。全データをEagle（Amazon競合データ）に保存。
  トリガー: 「競合データ取得」「ASINデータ」「amazon-data」「レビュー取得」
  「A+取得」「BSR取得」「販売数推定」「競合画像」「競合分析データ」「競合のデータを取得」
allowed-tools: Bash(uv run *), Bash(npx agent-browser:*)
---

# Amazon Data スキル

SP-API（無料）+ agent-browser でAmazon.co.jp競合データを取得する**グローバルスキル**。
ec・ec-listings どのプロジェクトからでも呼び出し可能。スクリプトは絶対パスで動作。

## データ保存先（Eagle一元管理）

全データはEagleのみに保存。JSONはtmp→Eagle登録→tmp削除のパターン。

```
Eagle: Amazon競合データ/
  {product_name}/             ← --product で指定（例: マザーズリュック）
    {親ASIN}/                 ← 親ASIN単位
      catalog_YYYYMMDD.json   ← タグ: type:catalog, parent_asin:XXX, bsr:NNN, node:カテゴリ
      reviews_YYYYMMDD.json   ← タグ: type:reviews, parent_asin:XXX
      aplus_YYYYMMDD.json     ← タグ: type:aplus, parent_asin:XXX
      {子ASIN}_MAIN.jpg       ← タグ: type:image, variant:MAIN, child_asin:XXX
      {子ASIN}_PT01.jpg
      {親ASIN}_APLUS_01.jpg   ← タグ: type:image, variant:APLUS_01（A+画像は親ASIN単位）
```

## スクリプトパス

```
C:/Users/ninni/.claude/skills/amazon-data/scripts/
  fetch_catalog.py     ← SP-API Catalog Items取得（親ASIN自動解決・全バリエーション展開）
  fetch_reviews.py     ← agent-browserでレビュー取得（バリエーション別情報含む）
  fetch_aplus.py       ← agent-browserでA+コンテンツ取得
  bsr_to_sales.py      ← BSR→販売数変換
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

## Eagle画像の利用方法

「競合のメイン画像を比較して」等の指示では:

```python
from lib.eagle_integration import list_parent_items, eagle_available

images = list_parent_items(product_name="マザーズリュック", parent_asin="B000XXX", data_type="image")
# → [{"file_path": "C:/...Eagle.../B000XXX_MAIN.jpg", "tags": [...], ...}, ...]
# file_path を Read ツールで読み込んでマルチモーダル分析
```

---

## タグ活用例

| やりたいこと | Eagle検索条件 |
|------------|--------------|
| 特定ASINの全データ | `parent_asin:B000XXX` |
| 全商品のメイン画像 | `variant:MAIN` + フォルダ: マザーズリュック |
| 今月取得したデータ | `captured:202603` |
| カタログJSONだけ | `type:catalog` |
| レビューJSONだけ | `type:reviews` |
| A+画像だけ | `variant:APLUS_01` |

---

## トリガー例

| ユーザーの依頼 | 実行コマンド |
|--------------|------------|
| 「マザーズリュックの競合データを取得して」 | `fetch_catalog.py --asins ... --product マザーズリュック` |
| 「このASINのレビューを取得して」 | `fetch_reviews.py --asins {親ASIN} --product ...` |
| 「A+コンテンツを取得して」 | `fetch_aplus.py --asins {親ASIN} --product ...` |
| 「BSR 500 のベビー用品の月間販売数を推定して」 | `bsr_to_sales.py estimate --bsr 500 --category baby_products` |
| 「競合のメイン画像を比較して」 | Eagle `list_parent_items` → Read で画像一括読み込み |

---

## 注意事項

- **SP-API**: 無料。レート制限 2 TPS（自動管理）
- **agent-browserスクレイピング**: 20商品以下・月2回まで。自動定期実行禁止
- **セッション切れの症状**: 0件取得・ログインページにリダイレクト → 上記「事前確認」を実行
- **セラスプ月額契約**: 新カテゴリ市場規模・キーワード逆引きはSP-APIでは代替不可 → 必要時のみ
