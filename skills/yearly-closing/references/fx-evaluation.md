# 為替評価替手順

## 対象

期末（12月31日）時点のCNY建て預け金残高。主にESPRIME口座。

## 重要性基準

CNY残高 × 直近レート ≥ ¥5,000 → 評価替実施
¥5,000未満 → スキップ可

## 手順

### 1. CNY残高の確認

```sql
SELECT calc_balance_cny, manual_balance_jpy, exchange_rate
FROM `main-project-477501.accounting.esprime_balance_view`
ORDER BY transaction_date DESC, nocodb_id DESC LIMIT 1
```

### 2. 年末レートの取得

ユーザーに確認: 「12月末の為替レートを教えてください」
- 三菱UFJ TTBレート（推奨）
- 中国人民銀行公示レート

### 3. 差額計算

```
市場価値 = CNY残高 × 年末レート
帳簿価値 = balance_jpy（esprime_balance_view の manual_balance_jpy）
為替差損益 = 市場価値 - 帳簿価値
```

### 4. 仕訳

**損失の場合**（帳簿 > 市場、円安→円高）:
- Dr. 為替差損益(105) / Cr. ESPRIME(5)

**利益の場合**（帳簿 < 市場、円高→円安）:
- Dr. ESPRIME(5) / Cr. 為替差損益(105)

### 5. NocoDB登録

manual_journal_entries テーブルに追加:
- journal_date: {YEAR}-12-31
- debit_account_id / credit_account_id: 上記に従う
- amount: ABS(差額)
- description: "ESPRIME預け金 FY{YEAR}期末 CNY→JPY為替換算調整（{CNY}元 × {rate}円 = ¥{市場} vs 帳簿¥{帳簿}）"

## 過去実績

| FY | CNY残高 | レート | 市場(JPY) | 帳簿(JPY) | 差額 |
|----|---------|--------|-----------|-----------|------|
| 2024 | 8,686元 | 23.10 | ¥200,657 | ¥200,868 | -¥211 |
| 2025 | 391.71元 | 22.36 | ¥8,759 | ¥26,616 | -¥17,857 |
