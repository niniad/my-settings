---
name: freee
description: freee API操作支援スキル。GCP Secret Managerで認証情報を管理し、freee APIへアクセス。取引（仕訳）の参照・登録、マスタ管理（取引先・品目・口座）、証憑（レシート）アップロードなどを実行。書き込み操作はユーザー確認必須。
---

# freee API Skill

freee会計のAPIを利用して、経理業務の自動化やデータ参照を行うスキルです。

## 前提条件

1. **認証情報の管理**
   - Google Cloud Secret Manager (GCP Project: `main-project-477501`) を使用して認証情報を管理しています。
   - 必要なSecret:
     - `freee_client_id`
     - `freee_client_secret`
     - `freee_refresh_token`
   - 初回認証やトークン切れの場合は、`scripts/manual_auth.py` を使用して手動でトークンを取得してください。

## 利用可能なスクリプト

全てのスクリプトは `scripts/` ディレクトリに配置されています。Python実行環境が必要です（`python scripts/script_name.py`）。

### 1. 参照・分析系 (Read-Only)

*   **取引（仕訳）一覧取得**
    *   `python scripts/list_deals.py --limit <N> --start_date <YYYY-MM-DD> --end_date <YYYY-MM-DD>`
    *   指定期間の仕訳データをリストアップします。
*   **マスタ一覧取得**
    *   `python scripts/list_masters.py <partners|items|account_items>`
    *   取引先、品目、勘定科目の一覧を取得します。
*   **証憑（レシート）一覧取得**
    *   `python scripts/list_receipts.py --start_date <YYYY-MM-DD>`
    *   ファイルボックス内のファイル一覧を取得します。
*   **試算表（残高）取得**
    *   `python scripts/get_trial_balance.py --fiscal_year <YYYY>`
    *   指定年度の貸借対照表・損益計算書の残高を取得します。

### 2. 作成・登録系 (Write with Confirmation)
**※重要: 書き込み操作を実行する際は、必ず実行内容を表示し、ユーザーの「y」入力を求める確認フローが入っています。**

*   **証憑（レシート）アップロード**
    *   `python scripts/upload_receipt.py <file_path>`
    *   PDFや画像ファイルをfreeeのファイルボックスへアップロードします。
*   **取引（仕訳）作成**
    *   `python scripts/create_deal.py --date <YYYY-MM-DD> --type <income|expense> --amount <N> --account_item_id <ID> --tax_code <ID> ...`
    *   新しい取引（収入/支出）を登録します。
*   **マスタ作成**
    *   `python scripts/create_master.py <partners|items> --name <NAME>`
    *   新しい取引先や品目を登録します。
*   **請求書作成**
    *   `python scripts/create_invoice.py --partner_id <ID> ...`
    *   請求書を作成します（簡易版）。
*   **Amazon決済連携**
    *   `python scripts/sync_settlements.py [--dry-run]`
    *   BigQueryの集計データを元に、settlement_id単位で振替伝票を作成・登録します。
    *   実行前に `--dry-run` で仕訳内容と勘定科目のマッピングを確認してください。

### 3. 認証系

*   **手動認証ヘルパー**
    *   `python scripts/manual_auth.py`
    *   ブラウザでの認可フローを経て、新しいRefresh Tokenを取得・保存します。

## 使用例

```bash
# 1. 2024年の仕訳を確認
python scripts/list_deals.py --start_date 2024-01-01 --end_date 2024-01-31

# 2. 領収書をアップロード
python scripts/upload_receipt.py "C:/path/to/receipt.pdf"

# 3. 新しい取引先「株式会社テスト」を追加（確認あり）
python scripts/create_master.py partners --name "株式会社テスト"
```

## 注意事項
- 書き込みを行うスクリプトは、ユーザー承認なしに自動実行（`SafeToAutoRun: true`）しないでください。
- 認証エラー（401）が発生した場合は、自動的にRefresh Tokenによる更新を試みますが、それでも失敗する場合は `manual_auth.py` の実行をユーザーに依頼してください。
