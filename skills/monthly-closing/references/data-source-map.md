# データソースマップ

## NocoDB → BQ 同期テーブル（アクティブ）

同期コマンド: `cd C:/Users/ninni/infra/nocodb-to-bq && uv run python main.py`
方式: WRITE_TRUNCATE（全テーブル全削除後に再挿入）

### paypay_bank_statements（PayPay銀行）

| BQカラム | 型 | NocoDB元名 | 用途 |
|----------|-----|-----------|------|
| nocodb_id | INT64 | id | PK |
| transaction_date | STRING | 操作日 | 取引日 |
| amount | INT64 | お預かり金額 | 入出金額 |
| description | STRING | 摘要 | 取引内容 |
| balance | INT64 | 残高 | 口座残高 |
| memo | STRING | 備考 | メモ |
| is_transfer | BOOL | 振替 | 振替フラグ |
| 振替_id | FLOAT64 | nc_opau___振替_id | 振替テーブルFK |
| freee勘定科目_id | FLOAT64 | nc_opau___freee勘定科目_id | 勘定科目FK |

### agency_transactions（代行会社）

| BQカラム | 型 | 用途 |
|----------|-----|------|
| nocodb_id | INT64 | PK |
| transaction_date | STRING | 発生日 |
| payment_account | STRING | ESPRIME/YP/THE直行便 |
| amount_foreign | FLOAT64 | 外貨金額(CNY) |
| exchange_rate | FLOAT64 | 為替レート |
| balance_foreign | FLOAT64 | 元残高(CNY) |
| balance_jpy | FLOAT64 | 円残高（累積、自動計算不可） |
| cost_category | STRING | 費目（商品代金/検品梱包/国際送料等） |
| product_category | STRING | 商品名（お食事エプロン等） |
| memo | STRING | 取引詳細・PO番号 |
| freee勘定科目_id | FLOAT64 | 勘定科目FK |
| 振替_id | FLOAT64 | 振替テーブルFK |

PO番号抽出: `REGEXP_EXTRACT(memo, r'PO-\d+')` → purchase_lot_master.po にJOIN

### その他アクティブテーブル

- **transfer_records**: transfer_date, amount, memo
- **manual_journal_entries**: journal_date, debit_account_id, credit_account_id, amount, description（事業主借も含む）
- **account_items**: nocodb_id, account_name, small_category, large_category
- **sale_monster_reports**: sale_date, sale_category, detail_description, total_amount_incl_tax, marketplace
- **standard_cost_history**: standard_cost, effective_start_date, effective_end_date, products_id, 費目別内訳
- **product_master**: 商品マスタ

### 廃止テーブル（BQ歴史データのみ残存）

| テーブル | 廃止理由 |
|----------|----------|
| rakuten_bank_statements | 2025-07口座廃止 |
| ntt_finance_statements | カード廃止 |
| amazon_account_statements | **BQから削除済み** settlement_journal_viewに移行 |
| owner_contribution_entries | **BQから削除済み** manual_journal_entriesに統合 |

## BQ accounting VIEWs

| VIEW | 用途 |
|------|------|
| journal_entries | 8ソース統合・複式仕訳（メインVIEW） |
| pl_journal_entries | P/L用（small_category, pl_contribution付き） |
| settlement_journal_view | Amazon精算→14科目展開 |
| inventory_journal_view | 月次棚卸仕訳（自動生成） |
| esprime_balance_view | ESPRIME CNY残高追跡 |
| trial_balance | 期末試算表 |
| balance_sheet_monthly | 月次BS |
| cash_flow_monthly | 月次CF |
| general_ledger | 勘定元帳（running_balance付き） |

## BQ analytics VIEWs（ec-analytics用）

| VIEW | 用途 |
|------|------|
| rpt_pnl_monthly_detail | SKU別P/L（26指標） |
| rpt_pnl_monthly_sku | SKU別P/L簡易版（利益貢献率付き） |
| stg_cost_standard | 標準原価（有効期間付き） |
