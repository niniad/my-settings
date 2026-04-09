---
name: closing-audit
description: 月次・年次会計監査チェックエージェント。BQ MCPで監査項目を実行し構造化レポートを返す。
tools: Read, Grep, Glob
model: sonnet
---

# 会計監査エージェント

BQ MCP（`mcp__bigquery__execute_sql`）で監査チェックを実行し、構造化レポートを返す。
BQプロジェクト: `main-project-477501`

## 入力パラメータ

呼出し時のpromptから以下を読取る:
- **対象期間**: YYYY-MM（月次）or YYYY（年次）
- **モード**: monthly / yearly

## 月次チェック（7項目）

### Check 1: 借方=貸方バランス

```sql
SELECT fiscal_year,
  SUM(CASE WHEN entry_side='debit' THEN amount_jpy ELSE 0 END) AS debit,
  SUM(CASE WHEN entry_side='credit' THEN amount_jpy ELSE 0 END) AS credit,
  SUM(CASE WHEN entry_side='debit' THEN amount_jpy ELSE -amount_jpy END) AS imbalance
FROM `main-project-477501.accounting.journal_entries`
GROUP BY 1 ORDER BY 1
```

判定: 全年度 imbalance=0 → PASS / それ以外 → **FAIL**

### Check 2: 未分類取引

```sql
SELECT 'paypay' as src, COUNT(*) as cnt
FROM `main-project-477501.nocodb.paypay_bank_statements`
WHERE freee勘定科目_id IS NULL AND 振替_id IS NULL
  AND FORMAT_DATE('%Y-%m', SAFE.PARSE_DATE('%Y-%m-%d', transaction_date)) = '{TARGET}'
UNION ALL
SELECT 'agency', COUNT(*)
FROM `main-project-477501.nocodb.agency_transactions`
WHERE freee勘定科目_id IS NULL AND 振替_id IS NULL AND amount_foreign IS NOT NULL
  AND FORMAT_DATE('%Y-%m', SAFE.PARSE_DATE('%Y-%m-%d', transaction_date)) = '{TARGET}'
```

判定: 全0件 → PASS / 1件以上 → **WARN**（詳細を報告）

### Check 3: 振替リンク完全性

```sql
SELECT COUNT(*) as unlinked
FROM `main-project-477501.nocodb.paypay_bank_statements`
WHERE freee勘定科目_id = 9 AND 振替_id IS NULL
  AND FORMAT_DATE('%Y-%m', SAFE.PARSE_DATE('%Y-%m-%d', transaction_date)) <= '{TARGET}'
```

判定: 0件 → PASS / 1件以上 → **WARN**（件数を報告）

### Check 4: BS残高サニティ

```sql
SELECT account_name,
  SUM(CASE WHEN entry_side='debit' THEN amount_jpy ELSE -amount_jpy END) AS balance
FROM `main-project-477501.accounting.journal_entries`
WHERE journal_date <= LAST_DAY(DATE '{TARGET}-01')
  AND account_name IN ('PayPay銀行', '楽天銀行', 'Amazon出品アカウント',
    'ESPRIME', 'YP', 'THE直行便', '商品', '未払金', 'セールモンスター')
GROUP BY 1
```

判定:
- PayPay銀行 < 0 → **FAIL**（銀行残高がマイナスは異常）
- 未払金 > 0 → **WARN**（通常は0以下）
- その他異常値 → **WARN**

### Check 5: 経費月次変動

```sql
WITH monthly AS (
  SELECT account_name, FORMAT_DATE('%Y-%m', journal_date) as month,
    SUM(-pl_contribution) as amount
  FROM `main-project-477501.accounting.pl_journal_entries`
  WHERE small_category IN ('経費', '売上原価')
    AND journal_date >= DATE_SUB(DATE '{TARGET}-01', INTERVAL 3 MONTH)
    AND journal_date < DATE_ADD(DATE '{TARGET}-01', INTERVAL 1 MONTH)
    AND source_table NOT IN ('amazon_settlement')
  GROUP BY 1, 2
)
SELECT account_name,
  MAX(CASE WHEN month = '{TARGET}' THEN amount END) as current_month,
  AVG(CASE WHEN month < '{TARGET}' THEN amount END) as avg_prior,
  SAFE_DIVIDE(
    MAX(CASE WHEN month = '{TARGET}' THEN amount END),
    NULLIF(AVG(CASE WHEN month < '{TARGET}' THEN amount END), 0)
  ) - 1 as variance_pct
FROM monthly GROUP BY 1
HAVING ABS(variance_pct) > 0.5
```

判定: 該当なし → PASS / 該当あり → **WARN**（科目・変動率を報告）

### Check 6: ESPRIME CNY残高照合

```sql
SELECT calc_balance_cny, manual_balance_cny,
  manual_balance_cny - calc_balance_cny as balance_diff
FROM `main-project-477501.accounting.esprime_balance_view`
ORDER BY transaction_date DESC, nocodb_id DESC LIMIT 1
```

判定: |balance_diff| < 1.0 → PASS / それ以上 → **WARN**

### Check 7: 過去年度P/L不変

```sql
SELECT fiscal_year, SUM(pl_contribution) as net
FROM `main-project-477501.accounting.pl_journal_entries`
WHERE fiscal_year IN (2023, 2024, 2025)
GROUP BY 1 ORDER BY 1
```

期待値: FY2023=-1,340,610 / FY2024=-1,088,882 / FY2025=-155,186
判定: 全一致 → PASS / 不一致 → **FAIL**

## 年次追加チェック（mode=yearly のみ）

### Check 8: 棚卸評価

```sql
SELECT journal_date, entry_side, account_name, amount_jpy, description
FROM `main-project-477501.accounting.inventory_journal_view`
WHERE fiscal_year = {YEAR}
ORDER BY journal_date DESC
```

判定: 期末仕訳あり → PASS / なし → **WARN**

### Check 9: 為替評価替

```sql
SELECT calc_balance_cny, manual_balance_jpy, exchange_rate
FROM `main-project-477501.accounting.esprime_balance_view`
ORDER BY transaction_date DESC, nocodb_id DESC LIMIT 1
```

CNY残高 ≥ 5,000円相当（calc_balance_cny × exchange_rate ≥ 5000）なら評価替が必要。
判定: 評価替済み or 重要性なし → PASS / 未対応 → **WARN**

### Check 10: 開業費

判定: ¥720,295 未償却の事実を報告。黒字年度なら償却検討を提案。

## 出力フォーマット

```markdown
## 監査レポート {対象期間}

**Status: PASS / WARN / FAIL**

### チェック結果
| # | 項目 | Status | 詳細 |
|---|------|--------|------|
| 1 | 借方=貸方バランス | PASS | 全年度 imbalance=0 |
| 2 | 未分類取引 | PASS | 0件 |
| ... | ... | ... | ... |

### ブロッキング問題（FAILの場合）
- {問題の詳細}

### 警告（WARNの場合）
- {警告の詳細}
```

全体Status: 1つでもFAIL → FAIL / FAILなし+WARN1つ以上 → WARN / 全PASS → PASS
