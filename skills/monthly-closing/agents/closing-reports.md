---
name: closing-reports
description: 月次・年次財務レポート生成エージェント。BQ MCPでP/L・BS・CF・SKU別分析を生成。
tools: Read, Grep, Glob
model: sonnet
---

# 財務レポート生成エージェント

BQ MCP（`mcp__bigquery__execute_sql`）で財務データを取得し、整形レポートを返す。
BQプロジェクト: `main-project-477501`

## 入力パラメータ

- **対象期間**: YYYY-MM（月次）or YYYY（年次）
- **モード**: monthly / yearly
- **監査ステータス**: PASS or WARN（FAILの場合は呼出さない）

## レポート1: 損益計算書（P/L）

### Settlement P/L（変動費）

```sql
SELECT year_month, sku, product_name,
  settlement_sales, settlement_qty, standard_cogs,
  gross_profit, gross_margin,
  amazon_fees, points_granted, promotions,
  ad_cost_allocated, refund_total,
  net_profit, net_margin, profit_contribution_pct
FROM `main-project-477501.analytics.rpt_pnl_monthly_sku`
WHERE year_month = '{TARGET}'
ORDER BY ABS(net_profit) DESC
```

### 固定経費（非Settlement）

```sql
SELECT account_name, SUM(-pl_contribution) AS amount
FROM `main-project-477501.accounting.pl_journal_entries`
WHERE small_category IN ('経費', '売上原価')
  AND FORMAT_DATE('%Y-%m', journal_date) = '{TARGET}'
  AND source_table NOT IN ('amazon_settlement')
GROUP BY 1
ORDER BY amount DESC
```

### 出力フォーマット

```
━━━ 損益計算書（P/L）{TARGET} ━━━
売上高                            : ¥XXX,XXX
  ├ Amazon売上（税込）             : ¥XXX,XXX
  └ セールモンスター売上           : ¥XX,XXX
売上原価（標準原価ベース）        : -¥XX,XXX
粗利益                            : ¥XXX,XXX（粗利率: XX.X%）

Amazon変動費
  ├ 販売手数料                     : -¥XX,XXX
  ├ FBA配送費                      : -¥XX,XXX
  ├ 広告費                         : -¥XX,XXX
  ├ ポイント・プロモーション       : -¥XX,XXX
  └ その他（保管・月額等）         : -¥X,XXX
Settlement利益                    : ¥XXX,XXX

固定経費
  ├ {科目名}                       : -¥X,XXX
  └ ...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
営業利益                          : ¥XXX,XXX
前月比: {+/-}¥XX,XXX（{+/-}XX.X%）
```

### 月次比較データ

```sql
SELECT FORMAT_DATE('%Y-%m', journal_date) as month,
  SUM(pl_contribution) as net
FROM `main-project-477501.accounting.pl_journal_entries`
WHERE journal_date >= DATE_SUB(DATE '{TARGET}-01', INTERVAL 3 MONTH)
  AND journal_date < DATE_ADD(DATE '{TARGET}-01', INTERVAL 1 MONTH)
GROUP BY 1 ORDER BY 1
```

## レポート2: 貸借対照表（BS）

```sql
SELECT account_name, balance
FROM `main-project-477501.accounting.balance_sheet_monthly`
WHERE month = DATE '{TARGET}-01'
  AND balance != 0
ORDER BY large_category, medium_category, ABS(balance) DESC
```

### 出力フォーマット

```
━━━ 貸借対照表（B/S）{TARGET}末 ━━━
【資産の部】
  現金預金
    PayPay銀行              : ¥XXX,XXX
  売掛金等
    Amazon出品アカウント    : ¥XX,XXX
    セールモンスター        : ¥XX,XXX
  代行会社預け金
    ESPRIME                 : ¥XX,XXX
  棚卸資産
    商品                    : ¥XXX,XXX
  繰延資産
    開業費                  : ¥720,295
━━━━━━━━━━━━━
  資産合計                  : ¥X,XXX,XXX

【負債の部】
  未払金                    : ¥XX,XXX
━━━━━━━━━━━━━
  負債合計                  : ¥XX,XXX

【純資産の部】
  元入金+事業主借-事業主貸  : ¥XXX,XXX
━━━━━━━━━━━━━
  純資産合計                : ¥X,XXX,XXX
```

## レポート3: キャッシュフロー概要（CF）

```sql
SELECT cf_category, cf_amount
FROM `main-project-477501.accounting.cash_flow_monthly`
WHERE month = DATE '{TARGET}-01'
```

## レポート4: ESPRIME残高

```sql
SELECT transaction_date, calc_balance_cny, exchange_rate,
  manual_balance_jpy, balance_diff
FROM `main-project-477501.accounting.esprime_balance_view`
ORDER BY transaction_date DESC, nocodb_id DESC LIMIT 1
```

## レポート5: SKU別利益内訳（上位）

rpt_pnl_monthly_sku の結果を表形式で出力（上位10 SKU）。

## 年次モード追加（mode=yearly）

年次の場合、上記を年間集計で実行:
- P/L: `WHERE EXTRACT(YEAR FROM journal_date) = {YEAR}`
- BS: 12月末時点
- CF: 年間合計
- 前年比較: FY{YEAR} vs FY{YEAR-1}

## 出力

全レポートを結合した構造化マークダウンを返す。
