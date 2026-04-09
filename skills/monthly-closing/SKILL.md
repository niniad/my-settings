---
name: monthly-closing
description: >
  月次会計締めスキル。NocoDB手動入力ガイド→BQ同期→監査→月次P/L・BS・CF生成まで一気通貫。
  BQが唯一の会計システム（freee非使用）。ユーザーはテーブル名・SQL不要。
  トリガー: 「月次締め」「月次会計」「会計締め」「P/L確認」「試算表」「貸借対照表」
  「仕訳確認」「振替リンク」「銀行明細インポート」
---

# 月次会計締め

## 概要

NocoDB手動入力→BQ同期→監査→レポート生成の5フェーズで月次締めを完了する。
監査とレポート生成はそれぞれ独立コンテキストのエージェントに委任し、精度を確保する。

ec-analytics との役割分担:
- **本スキル**: 固定経費仕訳、GL、試算表、BS、CF（`accounting.pl_journal_entries` に投入）
- **ec-analytics**: Settlement P/L、広告分析、KPI（Phase 3c で固定経費を読取）

---

## Phase 0: コンテキストロード (🤖 自動)

**0-1. 対象月の特定**
ユーザーに確認: 「何月分の月次締めですか？」（または直前月を推測）
→ `{TARGET_YYYY_MM}` として以降で使用

**0-2. データ鮮度チェック**

`mcp__bigquery__execute_sql` で以下を確認:

```sql
-- Settlement最新日
SELECT MAX(DATE(booking_date)) as latest
FROM `main-project-477501.accounting.settlement_journal_view`

-- 未分類PayPay取引数
SELECT COUNT(*) as unclassified
FROM `main-project-477501.nocodb.paypay_bank_statements`
WHERE freee勘定科目_id IS NULL AND 振替_id IS NULL

-- 前月P/L
SELECT SUM(pl_contribution) as net
FROM `main-project-477501.accounting.pl_journal_entries`
WHERE FORMAT_DATE('%Y-%m', journal_date) = '{PREV_MONTH}'
```

**0-3. ステータス表示**

```
【月次締め状況 {TARGET_YYYY_MM}】
📊 Settlement最新: {日付}
📋 未分類PayPay: {N}件
📈 前月P/L: ¥{金額}
```

---

## Phase 1: データ収集

### 1-1: 銀行明細インポート (👤 CSVパス提供 → 🤖 自動処理)

> 「{TARGET_YYYY_MM}のPayPay銀行明細CSVをダウンロードしてファイルパスを教えてください。」

ユーザーがCSVパスを提供後:
- `scripts/import_bank_csv.py` を実行
- `accounting.merchant_account_rules` の PayPay分類ルールで自動分類
- 未分類の行のみユーザーに提示して科目確認

### 1-2: Amazon Settlement 確認 (🤖 自動)

```sql
SELECT settlement_id, DATE(booking_date) as date, net_amount_check
FROM `main-project-477501.accounting.settlement_journal_view`
WHERE FORMAT_DATE('%Y-%m', DATE(booking_date)) = '{TARGET_YYYY_MM}'
ORDER BY booking_date
```

欠落時 → Cloud Runジョブログ確認を案内

### 1-3: 振替リンク (🤖 自動マッチ → 👤 承認)

`scripts/auto_transfer_match.py` を実行:
- PayPay未リンクAmazon入金（`freee勘定科目_id=9, 振替_id IS NULL`）を取得
- settlement_journal_view の net_amount_check と金額一致マッチ
- マッチ結果をユーザーに提示 → 承認後NocoDB API書込

### 1-4: ESPRIME/代行会社 (🤖 自動取込 → 👤 確認)

`scripts/import_agency_sheet.py` を実行:
- Google Sheets APIでESPRIM共有スプレッドシートを読取
- 既存NocoDB行と照合し新規行のみ抽出
- 入金行は自動で「入金本体 + 代行手数料2%」に分割
- 新規取引一覧をユーザーに提示 → 承認後NocoDB書込
- balance_jpy はSheetsから直接コピー（自動計算しない）

詳細: [special-transactions.md](references/special-transactions.md)

### 1-5: セールモンスター (👤 CSVあれば提供)

> 「{TARGET_YYYY_MM}のセールモンスター売上レポートCSVはありますか？」

あれば → NocoDB APIでインポート（分類不要、全行→売上高/セールモンスター）

### 1-6: 未分類ゼロ確認ゲート (🤖 自動)

```sql
SELECT COUNT(*) FROM `main-project-477501.nocodb.paypay_bank_statements`
WHERE freee勘定科目_id IS NULL AND 振替_id IS NULL
  AND FORMAT_DATE('%Y-%m', SAFE.PARSE_DATE('%Y-%m-%d', transaction_date)) = '{TARGET_YYYY_MM}'
```

0件でなければ Phase 1 に戻り、該当行を提示して分類を依頼。

---

## Phase 2: BQ同期 & バリデーション (🤖 自動)

### 2-1: NocoDB → BQ 同期

```bash
cd C:/Users/ninni/infra/nocodb-to-bq && uv run python main.py
```

### 2-2: 借方=貸方バランスチェック (**ハードゲート**)

```sql
SELECT fiscal_year,
  SUM(CASE WHEN entry_side='debit' THEN amount_jpy ELSE 0 END) AS debit,
  SUM(CASE WHEN entry_side='credit' THEN amount_jpy ELSE 0 END) AS credit,
  SUM(CASE WHEN entry_side='debit' THEN amount_jpy ELSE -amount_jpy END) AS imbalance
FROM `main-project-477501.accounting.journal_entries`
GROUP BY 1 ORDER BY 1
```

**imbalance ≠ 0 → 即時停止。原因調査が必要。**

### 2-3: 過去年度P/L不変確認 (**ハードゲート**)

```sql
SELECT fiscal_year, SUM(pl_contribution) as net
FROM `main-project-477501.accounting.pl_journal_entries`
WHERE fiscal_year IN (2023, 2024, 2025)
GROUP BY 1 ORDER BY 1
```

期待値: FY2023=-1,340,610 / FY2024=-1,088,882 / FY2025=-155,186
**不一致 → 即時停止。VIEW定義またはデータに問題あり。**

---

## Phase 3: 監査 (🤖 → closing-audit エージェント)

[agents/closing-audit.md](agents/closing-audit.md) を読み、Agent tool で呼出す。

```
Agent tool 呼出し:
  prompt: 以下の監査を実行してください。
    対象期間: {TARGET_YYYY_MM}
    モード: monthly
    [closing-audit.md の全内容をここに展開]
```

**結果ハンドリング**:
- `PASS` → Phase 4 へ
- `WARN` → 警告をユーザーに提示。承認後 Phase 4 へ
- `FAIL` → 停止。ブロッキング問題をユーザーに提示

---

## Phase 4: レポート生成 (🤖 → closing-reports エージェント)

[agents/closing-reports.md](agents/closing-reports.md) を読み、Agent tool で呼出す。

```
Agent tool 呼出し:
  prompt: 以下のレポートを生成してください。
    対象期間: {TARGET_YYYY_MM}
    モード: monthly
    監査ステータス: {PASS or WARN}
    [closing-reports.md の全内容をここに展開]
```

受取ったレポート（P/L・BS・CF・SKU内訳）をユーザーに提示。

---

## Phase 5: 締め確認

```
【月次締めチェックリスト {TARGET_YYYY_MM}】
✅ 銀行明細インポート完了
✅ 振替リンク設定完了
✅ 未分類取引: 0件
✅ NocoDB → BQ 同期完了
✅ 借方=貸方バランス: OK
✅ 過去年度P/L: 不変
✅ 監査: {PASS/WARN}
✅ 月次レポート生成完了

→ {TARGET_YYYY_MM}の月次締めが完了しました。
→ 詳細なKPI分析・広告分析は /ec-analytics で実行できます。
```

---

## 注意事項

- balance_jpy（代行会社円残高）は自動計算しない。累積残高であり手動調整を含む
- freee同期は本スキルの対象外（yearly-closing で対応）
- BQカラム名はNocoDB日本語名と異なる。詳細: [data-source-map.md](references/data-source-map.md)
- 発注ロット別原価はmemoから `REGEXP_EXTRACT(memo, r'PO-\d+')` で抽出可能

## 参照ドキュメント

- [会計方針](references/accounting-policies.md) — deposit_date基準、為替、標準原価
- [データソースマップ](references/data-source-map.md) — テーブル・カラム・VIEW定義
- [勘定科目表](references/chart-of-accounts.md) — nocodb_id・分類・PayPay分類ルール
- [特殊取引処理](references/special-transactions.md) — 不足金・代行送金・振替手順
