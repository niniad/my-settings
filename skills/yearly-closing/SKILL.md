---
name: yearly-closing
description: >
  年次決算・確定申告準備スキル。12月月次締め→年次調整仕訳→BQ最終検証→freee同期→確定申告チェックリスト。
  monthly-closingの上位プロセス。freee再契約→同期→確定申告まで一気通貫。
  トリガー: 「年次締め」「決算」「確定申告」「確定申告準備」「年末締め」「freee同期」
---

# 年次決算・確定申告準備

## 概要

12月月次締め→年次調整仕訳→BQ最終検証→freee同期→確定申告の5フェーズ。
monthly-closing スキルのエージェント（closing-audit, closing-reports）を mode=yearly で再利用。

確定P/L: FY2023=-1,340,610 / FY2024=-1,088,882 / FY2025=-155,186

---

## Phase 1: 12月月次締め

monthly-closing スキルを実行（Phase 0-5 全て）。
> 「まず12月分の月次締めを完了します。/monthly-closing を実行してください。」

月次締め完了を確認してから Phase 2 へ。

---

## Phase 2: 年次調整仕訳

### 2-1: 棚卸評価 (🤖 自動検証 → 👤 翌年原価登録)

**Step A: 仕訳存在確認**
```sql
SELECT journal_date, entry_side, account_name, amount_jpy, description
FROM `main-project-477501.accounting.inventory_journal_view`
WHERE fiscal_year = {YEAR}
ORDER BY journal_date DESC
```
12月末の期末棚卸仕訳（Dr.商品/Cr.仕入高）が存在するか確認。

**Step B: 独立クロスチェック**
inventory-evaluation.md の「独立検証クエリ」を実行し、SUM(line_total) と上記仕訳額を突合する。
- 差額 < 5% → PASS
- 差額 5-10% → WARN（原価改定タイミングや廃盤在庫の影響を確認）
- 差額 > 10% → FAIL（調査必要、Phase 3に進まない）

**Step C: 翌年原価登録確認**
```sql
SELECT * FROM `main-project-477501.nocodb.standard_cost_history`
WHERE effective_start_date >= '{NEXT_YEAR}-01-01'
```
> 「翌年分の標準原価（standard_cost_history）を登録済みですか？
> 未登録の場合、NocoDB の標準原価履歴テーブルに新年度の原価を追加してください。」

詳細: [inventory-evaluation.md](references/inventory-evaluation.md)

### 2-2: 為替評価替 (👤 レート提供 → 🤖 計算 → 👤 確認)

```sql
SELECT calc_balance_cny, manual_balance_jpy, exchange_rate
FROM `main-project-477501.accounting.esprime_balance_view`
ORDER BY transaction_date DESC, nocodb_id DESC LIMIT 1
```

**重要性判定**: calc_balance_cny × exchange_rate ≥ 5,000円 → 評価替実施

実施手順:
1. 🤖 ESPRIME CNY残高を取得
2. 👤 年末公示レートを提供（三菱UFJ TTB or 中国人民銀行）
3. 🤖 差額計算: (CNY残高 × 年末レート) - 帳簿balance_jpy
4. 👤 仕訳内容を確認
5. 🤖 NocoDB manual_journal_entries に書込

詳細: [fx-evaluation.md](references/fx-evaluation.md)

### 2-3: 開業費償却判断 (👤 判断)

> 「開業費 ¥720,295 が未償却のまま残っています。」
>
> 当年度の P/L が:
> - **赤字** → 償却見送りを推奨（赤字繰越で将来の節税効果を維持）
> - **黒字** → 償却開始を検討（任意の金額を償却可能）
>
> 償却する場合: Dr.繰延資産償却費 / Cr.開業費

### 2-4: 未払金・未収金確認 (🤖 自動)

```sql
SELECT account_name,
  SUM(CASE WHEN entry_side='debit' THEN amount_jpy ELSE -amount_jpy END) AS balance
FROM `main-project-477501.accounting.journal_entries`
WHERE journal_date <= DATE '{YEAR}-12-31'
  AND account_name IN ('未払金', 'Amazon出品アカウント', 'セールモンスター')
GROUP BY 1
```

Amazon年末残高（12/31精算済みで翌年入金分）が計上されていることを確認。

---

## Phase 3: BQ最終検証 (→ closing-audit mode=yearly)

monthly-closing/agents/closing-audit.md を読み、Agent tool で呼出す。

```
Agent tool 呼出し:
  prompt: 年次決算監査を実行してください。
    対象期間: {YEAR}
    モード: yearly
    [closing-audit.md の全内容を展開]
```

月次7項目 + 年次3項目（棚卸・為替・開業費）の計10項目を検証。

---

## Phase 4: freee同期（確定申告用）

### 4-1: freee再契約 (👤)
> 「freeeの契約を再開してください（確定申告期間のみ）。
> 会社ID: 11078943」

### 4-2: freee同期実行 (🤖 案内 → 👤 実行)

スクリプト: `C:/Users/ninni/projects/ec-accounting/scripts/freee_sync_fy2025.py`

```bash
C:/Users/ninni/infra/nocodb-to-bq/.venv/Scripts/python.exe \
  C:/Users/ninni/projects/ec-accounting/scripts/freee_sync_fy2025.py
```

※ FY2026以降は同スクリプトの FISCAL_YEAR 定数を変更、またはコピーして使用

詳細: [freee-sync-guide.md](references/freee-sync-guide.md)

### 4-3: freee試算表確認 (👤)

> 「freeeの以下を確認してください:」
>
> | 確認項目 | 確認方法 |
> |---------|---------|
> | 損益計算書 | BQ P/L（¥{期待値}）と一致 |
> | 貸借対照表 | PayPay銀行・Amazon出品・ESPRIME・商品の残高 |
> | 貸借一致 | 資産合計 = 負債合計 + 純資産合計 |

---

## Phase 5: 確定申告チェックリスト

詳細: [tax-filing-checklist.md](references/tax-filing-checklist.md)

```
【年次決算チェックリスト FY{YEAR}】
☐ 12月月次締め完了
☐ 棚卸評価完了（inventory_journal_view確認済み）
☐ 為替評価替完了（該当する場合）
☐ 開業費償却判断完了
☐ BQ全年度P/L不変確認
☐ BQ全年度バランス=0確認
☐ freee再契約完了
☐ freee同期実行完了
☐ freee損益計算書確認
☐ freee貸借対照表確認
☐ freee貸借一致確認
☐ 期末棚卸高をfreeeに手動入力
☐ 開業費残高を申告書に記載
☐ 消費税申告書確認（freee自動計算）
☐ 確定申告書作成・提出
```
