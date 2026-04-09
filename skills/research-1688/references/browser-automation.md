# 1688 ブラウザ自動化リファレンス

## 概要

AliPrice TXT（手動エクスポート）を土台に、agent-browser で商品ページの深堀りデータを補完する。

### 役割分担

| 作業 | ツール | 取得データ |
|------|--------|-----------|
| 検索・一覧取得 | 👤 Chrome + AliPrice TXT | 24項目（タイトル・価格・年間販売数・工場名・再購入率等） |
| 工場全商品リスト | 👤 Chrome + AliPrice TXT | 同上 |
| TXT→NocoDB登録 | 🤖 AI（TXTパース） | — |
| 商品ページ深堀り | 🤖 agent-browser | 产品参数・SKU詳細・price_min/max・OEM指標・認証・详情テキスト |
| スクリーンショット | 🤖 agent-browser | ページ全体画像（OCR用） |

### 制約

- **検索ページ**: agent-browser ではCAPTCHAでブロックされる（AliPriceで手動取得）
- **商品詳細ページ**: URL直接指定で閲覧可能（ログイン不要で基本情報取得可）
- **ログイン時**: 数量別価格テーブル等の追加情報が表示される場合あり

---

## agent-browser セッション管理

### 初回セッション確立

```bash
# 1688セッション作成（headed モードでログイン）
npx.cmd agent-browser --headed --session 1688 open https://www.1688.com

# ユーザーがログイン + CAPTCHA解決

# セッション状態を保存
npx.cmd agent-browser --session 1688 state save tmp/1688-auth.json
```

### セッション復元

```bash
npx.cmd agent-browser --session 1688 state load tmp/1688-auth.json
```

### ログイン不要の場合（商品ページ直接アクセス）

```bash
# URLを直接指定して商品ページを開く
npx.cmd agent-browser --session 1688 open "https://detail.1688.com/offer/{product_id}.html"
```

---

## 商品ページデータ抽出

### eval による構造化データ抽出

```bash
npx.cmd agent-browser --session 1688 open "https://detail.1688.com/offer/{product_id}.html"
npx.cmd agent-browser --session 1688 wait --load networkidle
npx.cmd agent-browser --session 1688 eval --stdin < .claude/skills/research-1688/scripts/1688_extract.js
```

### 抽出データ（AliPrice TXT の補完項目）

| 項目 | フィールド名 | 説明 |
|------|-------------|------|
| 価格レンジ | price_min, price_max | SKU全体の最低・最高価格 |
| 商品属性 | product_attrs | 产品参数セクションの全項目（素材・対象年齢・規格等） |
| SKU画像 | sku_images | バリエーション画像URL一覧 |
| 工場追加情報 | factory_extra | 入驻年数・主営・回头率・服務分・出荷率・好評率 |
| OEM指標 | oem_indicators | 加工定制・贴牌・OEM/ODM・打样 等のキーワード検出 |
| 認証 | certifications | CE・FDA・SGS・ISO・GB・A类 等の検出 |
| 详情テキスト | description_text | 商品説明の全テキスト（画像内テキストは除く） |
| 商品画像 | images | ギャラリー画像URL一覧 |

### スクリーンショット取得

```bash
# ページ全体（OCR分析用）
npx.cmd agent-browser --session 1688 screenshot tmp/1688-{product_id}.png --full

# 表示領域のみ
npx.cmd agent-browser --session 1688 screenshot tmp/1688-{product_id}-top.png
```

---

## 複数商品の自動巡回

AliPrice TXT から取得した商品URL一覧を使い、agent-browser で順次アクセス:

```
1. TXT から商品URLリストを抽出（AI処理）
2. 各URLに対して:
   a. agent-browser open {url}
   b. wait 3000（レート制限対策）
   c. eval --stdin < 1688_extract.js → JSON取得
   d. screenshot --full → 画像保存
   e. JSON + 画像を NocoDB に登録
3. 全商品完了後、スペックマスタとの照合スコアを算出
```

### レート制限ガイドライン

- リクエスト間隔: **3〜5秒**
- 連続アクセス上限: 1セッションあたり **30〜50ページ**
- CAPTCHAが出た場合: `--headed` モードでユーザーに手動解決を依頼 → `wait` で待機

---

## CAPTCHA 対応フロー

```
1. ページアクセス後、タイトルまたは本文に「验证」「滑块」を検出
2. headed モードでブラウザを表示
3. ユーザーに CAPTCHA 解決を依頼
4. agent-browser wait --fn "!document.body.innerText.includes('验证')" で解決を待機
5. 解決後、セッション状態を再保存
```

---

## AliPrice TXT 入力仕様

### ファイル形式
- TSV（タブ区切り）、ヘッダーなし
- ファイル名: `AliPriceExportProductList-1688-{date}.txt`

### カラム順序（24項目）

| # | カラム名 | 用途 |
|---|---------|------|
| 0 | タイトル | 商品テーブル登録 |
| 1 | 商品ID | 一意キー |
| 2 | 商品リンク | agent-browser でページ遷移 |
| 3 | 画像リンク | サムネイル |
| 4 | 価格 | price フィールド（AliPrice値） |
| 5 | 送料 | shipping |
| 6 | 最低注文数 | moq |
| 7 | 注文価格 | order_price |
| 8 | 出荷時間 | ship_time |
| 9 | 48時間出荷率 | ship_48h_rate |
| 10 | ドロップシッピング | dropship |
| 11 | 再購入率 | repeat_rate |
| 12 | 年間販売数 | annual_sales |
| 13 | 年間売上高 | annual_revenue |
| 14 | サービス総合評価 | service_score |
| 15 | 販売者属性 | seller_badge |
| 16 | 店舗名 | factory_name → 工場テーブル |
| 17 | 店舗ID | shop_id |
| 18 | 店舗リンク | shop_url → 工場テーブル |
| 19 | 開設時間 | shop_since |
| 20 | 出品日時 | listed_date |
| 21 | 年間販売数シェア | sales_share |
| 22 | 年間売上高シェア | revenue_share |
| 23 | 広告商品 | is_ad |

### SKU CSV（補助）
- ファイル名: `{商品名}_{商品ID}_sku_list.csv`
- ヘッダーあり（9カラム）: SKUイメージ, SKU名, SKU ID, 価格, 送料, 価格+送料, 最小注文数, 在庫数, 計算後の価格
