# 会計方針（要約）

マスター文書: `C:/Users/ninni/projects/ec-accounting/accounting_policies.md`

## 1. 仕訳日基準

**deposit_date（入金日）を使用**（2026-02-25確定）。settlement_end_dateではない。
銀行残高との完全一致を優先。年またぎ（settlement_end=12/30→deposit=1/1）は翌年計上。

## 2. 為替差損益

- 独立科目「為替差損益」(nocodb_id=105, small_category=経費)
- 発生: 代行会社への送金時（送信レートA ≠ 支出レートB）
- 期末評価替: CNY残高 × 年末公示レート vs 帳簿balance_jpy の差額
- 重要性基準: CNY残高 ≥ ¥5,000相当なら評価替実施

## 3. 標準原価法

- SKU別、年次手動更新（`standard_cost_history` テーブル）
- 費目内訳: product_cost, packaging_cost, inspection_cost, international_shipping, customs_tax, other_expenses
- 代行会社の実際原価（agency_transactions の cost_category別集計）と比較して乖離を把握

## 4. 棚卸資産（三分法）

- 期首(1/1): Dr.仕入高 / Cr.商品（前年期末在庫の振替）
- 期末(12/31): Dr.商品 / Cr.仕入高（当年期末在庫の計上）
- 在庫数量: SP-API FBA ledger-summary-view-data (12月末 SELLABLE)
- `inventory_journal_view` が月次で自動生成

## 5. 開業費

- 残高: ¥720,295（任意償却、現在未償却）
- 赤字年度は見送り推奨（節税効果）
- 償却開始時: Dr.繰延資産償却費 / Cr.開業費

## 6. 事業主借

- 個人カード（楽天カード等）で支払った事業経費
- `manual_journal_entries` テーブルに統合済み（2026-03-06）
- nocodb_id=85 / Dr.経費科目 / Cr.事業主借
