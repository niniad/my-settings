# KPI定義・目標値・警告ライン

## EC KPI一覧

| KPI | 定義 | 目標 | 警告 | 取得VIEW |
|-----|------|------|------|----------|
| 月売上 | total_sales合計（Traffic系） | ≥¥420,000 | <¥250,000 | `rpt_kpi_monthly` → sales_status |
| 月次営業利益 | settlement_profit（Settlement系、全費用込み） | ≥¥50,000 | <¥0（赤字） | `rpt_kpi_monthly` → profit_status |
| TACOS | ad_cost/total_sales | ≤5% | >10% | `rpt_kpi_monthly` → tacos_status |
| CVR | units_ordered/sessions | ≥5% | <3% | `rpt_kpi_monthly` → cvr_status |
| FBA在庫月数 | 在庫数/月間販売数 | 4-6ヶ月 | >8 or <2 | `rpt_inventory_health` → stock_status |
| レビュー | review_count, rating | 100件/4.3★ | <4.0★ | NocoDB Amazonレビュー |
| 事業口座残高 | PayPay銀行最新残高 | >¥300,000 | <¥100,000 | NocoDB PayPay銀行テーブル |

### KPI取得SQL

```sql
-- 月次KPI（閾値判定付き）
SELECT * FROM `main-project-477501.analytics.rpt_kpi_monthly`
WHERE year_month >= FORMAT_DATE('%Y-%m', DATE_SUB(CURRENT_DATE(), INTERVAL 3 MONTH))
ORDER BY year_month DESC
```

```sql
-- 在庫健全性
SELECT asin, product_name, fulfillable_quantity, months_of_stock, stock_status, days_until_stockout
FROM `main-project-477501.analytics.rpt_inventory_health`
ORDER BY months_of_stock ASC
```

## 会計方針の要点

- **仕訳日基準**: deposit_date（Amazon入金日）を使用
- **為替差損益**: 独立科目として経費計上
- **原価計算**: `nocodb.standard_cost_history` が正本。標準原価×販売数量（月次分析用）
- **利益の2系統**: `estimated_profit`（Traffic系、手数料控除前）と `settlement_profit`（Settlement系、全費用込み）。意思決定にはSettlement系を使用
- **開業費**: 繰延資産として保持中（任意償却、未開始）

詳細: `C:/Users/ninni/projects/gcp-main-project-477501/accounting_policies.md`

## 利益計算ロジック

```
P&L構造（rpt_pnl_monthly_sku）:
  売上(settlement_sales)
  - 原価(standard_cogs)
  = 売上総利益(gross_profit)
  + Amazon手数料(amazon_fees: 負値)
  = 手数料控除後利益(gross_profit_after_fees)
  + ポイント(points_granted: 負値)
  + プロモーション(promotions: 負値)
  - 広告費(ad_cost_allocated)
  = 営業利益(net_profit)
  + 返品(refund_total: 負値)
  = 返品後利益(net_profit_after_refund)
```

## 単品P&L（2026年原価ベース）

| 商品 | 販売価格 | 原価 | Amazon手数料 | FBA | 粗利/個 | 粗利率 |
|------|---------|------|-------------|-----|---------|--------|
| エプロン単品 | 998円 | 390円 | 150円 | 280円 | 178円 | 17.8% |
| 3枚セット | 2,780円 | 1,170円 | 417円 | 400円 | 793円 | 28.5% |
| マザーズリュック | 4,280円 | 1,592円 | 642円 | 550円 | 1,496円 | 35.0% |

## 広告運用ガイドライン

- **最適広告費**: 月1.5〜2.5万円（TACOS 5%前後）
- これ以上は利益を削るだけで売上はほぼ増えない（2025年10-11月実験で確認済み）
- オーガニック力が強い事業

## NocoDB テーブルID

| テーブル | ID |
|---------|-----|
| KPI_Monthly | mtjjrfldelt8wlp |
| PDCA_Actions | m8ocl2tmdt5p0fk |
