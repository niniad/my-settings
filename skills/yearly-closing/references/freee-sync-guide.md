# freee同期ガイド

## 前提

- freeeは期中解約。確定申告期間（1-3月）のみ契約
- BQ `accounting.journal_entries` が正本
- freeeへは振替伝票（manual_journals）として一括投入

## 会社情報

- Company ID: 11078943
- 期間設定: 各年度のアカウント期間がfreee管理画面で設定されていること

## 同期スクリプト

パス: `C:/Users/ninni/projects/ec-accounting/scripts/freee_sync_fy2025.py`

実行:
```bash
C:/Users/ninni/infra/nocodb-to-bq/.venv/Scripts/python.exe \
  C:/Users/ninni/projects/ec-accounting/scripts/freee_sync_fy2025.py
```

※ `uv run` ではなく venv の Python を直接使用（バックグラウンド実行防止）

## 3ステップ処理

### Step 1: BQデータ取得
- `accounting.journal_entries` から対象年度の全仕訳を取得
- source_table:source_id でグルーピング
- 全account_name が ACCOUNT_MAP に存在することを検証
- 各トランザクションの借方合計=貸方合計を検証

### Step 2: freee既存データ削除
- 対象年度の manual_journals を全件削除
- 対象年度の deals を全件削除
- レート制限（429）はRetry-Afterヘッダーで待機

### Step 3: freee投入
- 各トランザクションを manual_journal として POST
- 日付 = journal_date
- 詳細 = entry_side, account_item_id, amount, description
- 50+ account_name → freee account_item_id マッピング（ACCOUNT_MAP dict）

## ACCOUNT_MAP（主要）

| BQ account_name | freee account_item_id |
|----------------|----------------------|
| 売上高 | 786598267 |
| 仕入高 | 786598280 |
| 商品 | 786598202 |
| PayPay銀行 | 1007592863 |
| Amazon出品アカウント | 1008403397 |
| ESPRIME | 1007511503 |
| 事業主借 | 786598262 |
| 為替差損益 | 1007603892 |

完全なマッピングはスクリプト内の ACCOUNT_MAP dict を参照。

## 同期後の確認事項

1. freee損益計算書のP/L合計がBQ値と一致
2. freee貸借対照表の主要科目残高:
   - PayPay銀行: 実際の銀行残高と一致
   - Amazon出品アカウント: 12/31精算の未入金分
   - ESPRIME: CNY残高×年末レート ≈ 円建残高
   - 商品: SP-API在庫数×標準原価
3. 資産合計 = 負債合計 + 純資産合計（貸借一致）
