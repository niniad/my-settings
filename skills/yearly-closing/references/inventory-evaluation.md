# 棚卸評価手順

## 方式

標準原価法（SKU別、年次更新）。三分法で期首/期末仕訳。

## 自動生成

`accounting.inventory_journal_view` が月次で以下を自動生成:
- 期首(1/1): Dr.仕入高 / Cr.商品（前年期末在庫の振替）
- 期末(12/31): Dr.商品 / Cr.仕入高（当年期末在庫の計上）

## 在庫数量ソース

SP-API FBA ledger-summary-view-data の12月末 SELLABLE 数量。
Cloud Runジョブで日次取得 → BQ `sp_api_external` に格納。

## 標準原価テーブル

`nocodb.standard_cost_history`:
- products_id: 製品マスタFK
- standard_cost: 合計標準原価
- 費目内訳: product_cost, packaging_cost, inspection_cost, international_shipping, customs_tax, other_expenses
- effective_start_date / effective_end_date: 適用期間

## 確認クエリ

```sql
-- 期末棚卸仕訳の確認
SELECT journal_date, entry_side, account_name, amount_jpy, description
FROM `main-project-477501.accounting.inventory_journal_view`
WHERE fiscal_year = {YEAR}
ORDER BY journal_date DESC

-- 標準原価の翌年分登録確認
SELECT * FROM `main-project-477501.nocodb.standard_cost_history`
WHERE effective_start_date >= '{NEXT_YEAR}-01-01'
```

## 独立検証クエリ（クロスチェック用）

inventory_journal_view の金額を、SP-API在庫 × 標準原価で独立計算した値と突合する。

```sql
-- SP-API在庫数量 × 標準原価 = 期末棚卸高（独立計算）
WITH latest_inventory AS (
  SELECT
    seller_sku,
    product_name,
    fulfillable_quantity
  FROM `main-project-477501.analytics.rpt_inventory_health`
  WHERE fulfillable_quantity > 0
),
current_cost AS (
  SELECT
    p.sku AS seller_sku,
    sc.standard_cost
  FROM `main-project-477501.nocodb.standard_cost_history` sc
  JOIN `main-project-477501.nocodb.product_master` p
    ON sc.products_id = p.nocodb_id
  WHERE CURRENT_DATE('Asia/Tokyo') BETWEEN sc.effective_start_date
    AND COALESCE(sc.effective_end_date, '2099-12-31')
)
SELECT
  i.seller_sku,
  i.product_name,
  i.fulfillable_quantity AS qty,
  c.standard_cost AS unit_cost,
  i.fulfillable_quantity * c.standard_cost AS line_total
FROM latest_inventory i
LEFT JOIN current_cost c ON i.seller_sku = c.seller_sku
ORDER BY line_total DESC
```

**検証方法**: 上記の `SUM(line_total)` と `inventory_journal_view` の期末仕訳額を比較。
- 差額 < 5% → OK
- 差額 5-10% → 原価改定タイミングや廃盤在庫の影響を確認
- 差額 > 10% → 標準原価テーブルまたは在庫数量に問題あり。調査必要

## 過去実績

| FY | 期末在庫額 | SKU数 |
|----|----------|-------|
| 2024 | ¥483,968 | 11 |
| 2025 | ¥502,320 | 11 |
