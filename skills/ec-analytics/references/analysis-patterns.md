# 分析パターン集

## 目次

0. [データ鮮度確認（毎回最初に実行）](#0-データ鮮度確認)
1. [月次KPIレビュー](#1-月次kpiレビュー)
2. [利益変動分解](#2-利益変動分解)
3. [経費内訳P&L](#3-経費内訳pl)
4. [SKU別P&L](#4-sku別pl)
5. [商品別収益性（BCGマトリクス）](#5-商品別収益性bcgマトリクス)
6. [市場トレンド分析](#6-市場トレンド分析)
7. [広告キャンペーン分析](#7-広告キャンペーン分析)
8. [キーワード効率分析](#8-キーワード効率分析)
9. [広告クロス購入分析](#9-広告クロス購入分析)
10. [週次ASIN＋市場データ](#10-週次asin市場データ)
11. [在庫健全性分析](#11-在庫健全性分析)
12. [リピート購入分析](#12-リピート購入分析)

> 全SQLは `analytics` データセットのReport層VIEWを直接参照する。
> **重要**: 分析開始時は必ずパターン0（データ鮮度確認）を実行し、不完全データで判断しないこと。

---

## データ量と判断の限界

この事業の月間データ量（2025年7月〜2026年2月の実績）:

| 指標 | 月間規模 |
|---|---|
| 全商品合計注文 | 150〜350件 |
| 個別ASIN注文 | 5〜39件（最多商品でも日平均1件程度）|
| 広告クリック | 170〜1,900件 |
| 広告経由注文 | 13〜228件 |
| セッション | 3,300〜7,100件 |

### 判断基準

| 分析粒度 | 信頼性 | 使い方 |
|---|---|---|
| **事業全体×月次** | 大きな変動（±30%以上）は検出可能 | KPI監視、損益判断 |
| **商品カテゴリ×月次** | 傾向の参考値 | ポートフォリオ判断（エプロン全体、リュック全体） |
| **個別ASIN×月次** | 統計的判断は**不可能** | 在庫管理の参考のみ |
| **任意の粒度×週次** | ほぼノイズ | 深掘り判断の材料としない |

### 分析時の注意

- 月間±15-20%の変動は**ノイズ**として扱う。単月の変動で施策を変更しない
- **3ヶ月以上同方向**に動いて初めて「トレンド」と判断する
- 個別ASINのCVR変動（例: 5%→3%）は注文数10件→6件の差に過ぎず、偶然の範囲
- 施策の効果測定は**施策前1ヶ月 vs 施策後1ヶ月**、**カテゴリ単位**で行う
- 「データ不足で判断できない」は正しい結論。無理にアクションを導出しない

---

## 0. データ鮮度確認

**毎回の分析開始時に必ず実行する。**

```sql
SELECT * FROM `main-project-477501.analytics.rpt_data_freshness`
```

**確認事項:**
- `status` が「異常（要確認）」のソースがあれば、Cloud Runジョブの停止等を疑う
- `safe_analysis_date` = 全日次データが揃っている最終日。この日以降のデータは不完全
- `rpt_kpi_monthly` の `data_quality` 列も同様に確認（`complete` / `current_month_partial` / `incomplete_ad_data`）

**不完全データへの対応:**
- `data_quality = 'incomplete_ad_data'` の月: TACOS・広告CVR・estimated_profit は信頼できない
- `data_quality = 'current_month_partial'` の月: 月途中なので絶対値ではなく日平均で比較
- 前月以前で `complete` の月のみ、意思決定の根拠として使用する

---

## 1. 月次KPIレビュー

```sql
-- 当月 + 3ヶ月推移
SELECT *
FROM `main-project-477501.analytics.rpt_kpi_monthly`
WHERE year_month >= FORMAT_DATE('%Y-%m', DATE_SUB(CURRENT_DATE(), INTERVAL 3 MONTH))
ORDER BY year_month DESC
```

**閾値判定カラム（VIEW内蔵）:**
- `sales_status`: 売上 ≥42万→OK / ≥25万→注意 / <25万→警告
- `profit_status`: Settlement営業利益 ≥5万→OK / ≥0→注意 / <0→警告 / 当月→集計中
- `tacos_status`: TACOS ≤5%→OK / ≤10%→注意 / >10%→警告
- `cvr_status`: CVR ≥5%→OK / ≥3%→注意 / <3%→警告
- `data_quality`: `complete` / `current_month_partial` / `incomplete_ad_data`

**2系統の売上・利益:**
- `total_sales` / `estimated_profit`: Traffic系（リアルタイム、手数料控除前の概算粗利）
- `settlement_sales` / `settlement_profit`: Settlement系（正確な営業利益、当月はNULL）
- 意思決定には `settlement_profit` を使用する。`estimated_profit` はトレンド観察用

## 2. 利益変動分解

**KPI確認後、利益が変動していたら必ず実行。** 前月比のウォーターフォール分解。

```sql
SELECT * FROM `main-project-477501.analytics.rpt_profit_variance_monthly`
WHERE year_month >= FORMAT_DATE('%Y-%m', DATE_SUB(CURRENT_DATE(), INTERVAL 3 MONTH))
  AND data_quality = 'complete'
ORDER BY year_month DESC
```

**主要カラム:**
- `profit_change`: 前月比の利益変動額
- `primary_driver`: 最大の変動要因（`売上変動` / `原価変動` / `Amazon手数料変動` / `広告費変動`）
- `volume_effect` / `price_effect`: 売上変動を数量効果と単価効果に分解
- `delta_*`: 各費用項目の変動額（正=利益改善、負=利益悪化）
- `data_quality`: completeの月のみ意思決定に使用すること

**primary_driverに応じた次のアクション:**
- `売上変動` → パターン6（市場トレンド）で市場要因 vs 自社要因を判別
- `Amazon手数料変動` → パターン3（経費内訳P&L）で手数料種別を特定
- `広告費変動` → パターン7（広告キャンペーン）でキャンペーン別効率を確認
- `原価変動` → stg_cost_standard で原価改定の有無を確認

## 3. 経費内訳P&L

**変動分解でAmazon手数料や固定費が主因のときに使用。**

```sql
-- 月次の経費サマリー
SELECT year_month,
  SUM(sales_principal) AS sales,
  SUM(cogs) AS cogs,
  SUM(fee_commission) AS commissions,
  SUM(fee_fba_fulfillment) AS fba_fees,
  SUM(fee_misc) AS other_fees,
  SUM(ad_cost_allocated) AS ad_cost,
  SUM(sku_net_profit) AS sku_profit,
  MAX(storage_fee) AS storage,
  MAX(subscription_fee) AS subscription,
  MAX(vine_fee) AS vine,
  MAX(inbound_transport_fee) AS inbound,
  MAX(total_overhead) AS total_overhead
FROM `main-project-477501.analytics.rpt_pnl_monthly_detail`
WHERE year_month >= FORMAT_DATE('%Y-%m', DATE_SUB(CURRENT_DATE(), INTERVAL 3 MONTH))
GROUP BY 1 ORDER BY 1 DESC
```

```sql
-- SKU別の手数料内訳
SELECT year_month, sku, product_name, qty, sales_principal,
  fee_commission, fee_fba_fulfillment, fee_misc, ad_cost_allocated, sku_net_profit
FROM `main-project-477501.analytics.rpt_pnl_monthly_detail`
WHERE year_month = FORMAT_DATE('%Y-%m', DATE_SUB(CURRENT_DATE(), INTERVAL 1 MONTH))
ORDER BY sales_principal DESC
```

**固定費（overhead）の内訳:**
- `storage_fee`: FBA保管手数料（季節変動あり）
- `subscription_fee`: 月額登録料 ¥5,390
- `vine_fee`: Vine登録費用（新商品時のみ）
- `inbound_transport_fee`: FBA納品送料
- `deal_fee`: タイムセール参加費

## 4. SKU別P&L

```sql
-- 直近3ヶ月のSKU別損益
SELECT *
FROM `main-project-477501.analytics.rpt_pnl_monthly_sku`
WHERE year_month >= FORMAT_DATE('%Y-%m', DATE_SUB(CURRENT_DATE(), INTERVAL 3 MONTH))
ORDER BY year_month DESC, settlement_sales DESC
```

**P&L 5段階:**
```
1. 売上総利益 = 売上 - 原価(standard_cogs)
2. 手数料控除後 = 売上総利益 + Amazon手数料(amazon_fees: 負値)
3. 営業利益(net_profit) = 手数料控除後 + ポイント + プロモ - 広告費(ad_cost_allocated)
4. 返品後利益 = 営業利益 + 返品(refund_total: 負値)
```

## 5. 商品別収益性（BCGマトリクス）

```sql
-- 直近月の商品別 + BCG分類（6ヶ月ベース）
SELECT child_asin, product_name, year_month,
  total_sales, settlement_sales, settlement_profit,
  profit_margin, cvr, tacos,
  bcg_category, sales_growth_rate, profit_margin_6m
FROM `main-project-477501.analytics.rpt_product_profitability`
WHERE year_month = FORMAT_DATE('%Y-%m', DATE_SUB(CURRENT_DATE(), INTERVAL 1 MONTH))
ORDER BY total_sales DESC
```

**主要カラム:**
- `total_sales`: Traffic系売上（リアルタイム）
- `settlement_sales` / `settlement_profit`: Settlement系（全費用込み実利益）
- `profit_margin`: Settlement基準の利益率（settlement_profit / settlement_sales）
- `cvr` / `tacos`: Traffic系の行動指標
- `profit_margin_6m` / `sales_growth_rate`: BCG分類の入力値（6ヶ月Settlement基準）

**BCG分類ロジック（VIEW内蔵、Settlement利益率基準）:**
- Star: 成長率>0 かつ 利益率>15%
- Cash Cow: 成長率≤0 かつ 利益率>15%
- Question Mark: 成長率>0 かつ 利益率≤15%
- Dog: 成長率≤0 かつ 利益率≤15%

> **注意**: 発売6ヶ月未満の商品は `sales_growth_rate` が NULL → Dog に分類される。新商品の評価は `profit_margin` で個別判断すること。

## 6. 市場トレンド分析

**変動分解で売上変動が主因のときに使用。** 市場全体の成長 vs 自社シェア変動を分離する。

```sql
-- 直近6ヶ月の市場トレンド（ASIN別）
SELECT year_month, asin, product_name, total_sales, sales_growth,
  market_imp_growth, market_purch_growth,
  impression_share, purchase_share, impression_share_change, purchase_share_change,
  own_cvr, market_cvr, market_diagnosis
FROM `main-project-477501.analytics.rpt_market_trend_monthly`
WHERE year_month >= FORMAT_DATE('%Y-%m', DATE_SUB(CURRENT_DATE(), INTERVAL 6 MONTH))
ORDER BY year_month DESC, total_sales DESC NULLS LAST
```

**主要カラム:**
- `total_sales` / `sales_growth`: 自社売上と前月比成長率
- `market_imp_growth` / `market_purch_growth`: 市場全体のインプレッション・購入の前月比成長率
- `impression_share` / `purchase_share`: 市場内シェア（インプレッション / 購入）
- `impression_share_change` / `purchase_share_change`: 前月比シェア変動
- `own_cvr` vs `market_cvr`: 自社CVR vs 市場平均CVR
- `market_diagnosis`: 自動診断（`市場成長 + シェア維持/拡大` 等）

**解釈パターン（`market_diagnosis` で自動判定）:**
- 市場成長 + シェア維持/拡大 → 順調。施策を維持
- 市場成長だがシェア低下 → 競合に取られている。広告・SEO・価格を確認
- 市場縮小だがシェア拡大 → 季節要因等で市場縮小だが自社は健闘
- 市場縮小 + シェア低下 → 要注意。商品力・ページ品質の見直し

---

## 7. 広告キャンペーン分析

```sql
-- 直近3ヶ月のキャンペーン別パフォーマンス
SELECT *
FROM `main-project-477501.analytics.rpt_ad_campaign_performance`
WHERE year_month >= FORMAT_DATE('%Y-%m', DATE_SUB(CURRENT_DATE(), INTERVAL 3 MONTH))
ORDER BY year_month DESC, ad_cost DESC
```

**効率分類（VIEW内蔵）:**
- 高効率: ACOS ≤15%
- 中効率: ACOS 15-30%
- 非効率: ACOS >30%
- 売上ゼロ: 売上=0 かつ コスト>0

## 8. キーワード効率分析

```sql
-- 直近30日のキーワード効率（無駄コスト降順）
SELECT *
FROM `main-project-477501.analytics.rpt_ad_keyword_efficiency`
ORDER BY wasted_cost DESC, ad_cost DESC
```

**効率分類（VIEW内蔵）:**
- ROI優良: ACOS ≤15%
- 中間: ACOS 15-30%
- 非効率（入札調整）: ACOS >30%
- 売上ゼロ（停止検討）: 売上=0 かつ コスト>0
- インプレッションのみ: 売上=0 かつ コスト=0

**無駄コスト集計:**
```sql
SELECT
  efficiency_category,
  COUNT(*) AS keyword_count,
  SUM(ad_cost) AS total_cost,
  SUM(wasted_cost) AS total_wasted
FROM `main-project-477501.analytics.rpt_ad_keyword_efficiency`
GROUP BY 1
ORDER BY total_wasted DESC
```

## 9. 広告クロス購入分析

**重要**: 広告停止・予算変更の判断時に必ず実施すること。

```sql
-- 広告ASIN別の真のROAS + クロス購入率（直近90日）
SELECT DISTINCT
  advertised_asin, advertised_sku,
  ad_cost_for_advertised_asin,
  all_sales_from_ad, self_sales, cross_sales,
  true_roas, cross_purchase_ratio
FROM `main-project-477501.analytics.rpt_ad_cross_purchase`
ORDER BY all_sales_from_ad DESC
```

```sql
-- 特定広告ASINの購入商品内訳
SELECT advertised_asin, purchased_asin, purchased_product_name,
  is_cross_purchase, total_sales, total_purchases
FROM `main-project-477501.analytics.rpt_ad_cross_purchase`
WHERE advertised_asin = '{ASIN}'
ORDER BY total_sales DESC
```

### 解釈の注意点
- 全商品でクロス購入率64〜79%。どの柄でも他柄の購入につながる構造
- `true_roas` は クロス購入込み総売上/広告費。通常のROASより大幅に高い
- 広告停止判断は `true_roas` で行う
- クロス購入は全商品共通の現象なので、特に非効率な広告は停止しても他の入口が代替する

## 10. 週次ASIN＋市場データ

```sql
-- 直近4週の週次パフォーマンス + SQPデータ
SELECT *
FROM `main-project-477501.analytics.rpt_weekly_asin_with_sqp`
WHERE week_start >= DATE_SUB(CURRENT_DATE(), INTERVAL 28 DAY)
ORDER BY week_start DESC, total_sales DESC
```

**市場データ指標:**
- `impression_share`: 市場全体のインプレッション中の自社シェア
- `purchase_share`: 市場全体の購入中の自社シェア
- `own_search_cvr` vs `market_search_cvr`: 自社CVR vs 市場平均CVR
- `ranked_query_count`: ランクインしている検索クエリ数（SEO強度の指標）

## 11. 在庫健全性分析

```sql
SELECT *
FROM `main-project-477501.analytics.rpt_inventory_health`
ORDER BY months_of_stock ASC
```

**在庫ステータス（VIEW内蔵）:**
- 要補充: 在庫月数 <2ヶ月
- 適正: 在庫月数 2-8ヶ月
- 過剰在庫: 在庫月数 >8ヶ月

`days_until_stockout` で在庫切れまでの日数も確認可能。

## 12. リピート購入分析

```sql
SELECT *
FROM `main-project-477501.analytics.rpt_repeat_purchase`
ORDER BY report_start_date DESC, orders DESC
```

## 対象期間の基準

| 分析 | 対象期間 |
|------|---------|
| 月次KPI | 当月 + 前月 + 3ヶ月推移 |
| 広告効率（キーワード） | 直近30日 |
| クロス購入 | 直近90日 |
| BCGマトリクス | 直近6ヶ月 |
| 在庫 | 最新スナップショット + 30日移動平均販売数 |