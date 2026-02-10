---
name: google-workspace
description: Google DriveおよびGoogle Sheetsを操作するスキル。ファイルの閲覧、検索、スプレッドシートの読み込み、ダウンロードを行います。
---

# Google Workspace Skill

Google DriveおよびGoogle Sheets APIを利用して、ファイルの検索、閲覧、ダウンロードを行うスキルです。

## 前提条件

1.  **GCPプロジェクト設定**
    *   Google Cloud Consoleでプロジェクトを作成（または既存を使用）。
    *   **Google Drive API** と **Google Sheets API** を有効化してください。
    *   **Secret Manager API** を有効化してください。
    *   **OAuth同意画面** を設定（User Type: External/Internal, Test Usersに追加など）。
    *   **OAuth 2.0 クライアント ID** を作成（アプリケーションの種類: **デスクトップ アプリ**）。

2.  **Secret Managerにクレデンシャルを登録**
    *   ダウンロードしたOAuth JSONを `google_workspace_credentials` として登録:
    ```bash
    gcloud secrets create google_workspace_credentials --project=YOUR_PROJECT_ID
    cat downloaded-credentials.json | gcloud secrets versions add google_workspace_credentials --data-file=- --project=YOUR_PROJECT_ID
    ```
    *   トークン用のシークレットも事前作成:
    ```bash
    gcloud secrets create google_workspace_token --project=YOUR_PROJECT_ID
    ```

3.  **ライブラリのインストール**
    ```bash
    pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib google-cloud-secret-manager
    ```

4.  **認証（初回のみ）**
    *   `gcloud auth application-default login` でGCP認証を行ってください。
    *   `python scripts/auth.py` を実行してGoogle OAuth認証を行ってください。
    *   ブラウザが起動し、Googleアカウントへのログインと許可が求められます。
    *   認証が成功するとトークンがSecret Managerに保存されます。

## 利用可能なスクリプト

全てのスクリプトは `scripts/` ディレクトリに配置されています。

### 1. 認証

*   **認証実行**
    *   `python scripts/auth.py`
    *   Secret ManagerからOAuthクレデンシャルを取得し、認証フローを実行します。トークンはSecret Managerに保存されます。

### 2. Google Drive（ファイル操作）

*   **ファイル一覧取得**
    *   `python scripts/list_files.py --query "name contains '予定表'"`
    *   Google Drive上のファイルを検索・一覧表示します。
    *   オプション: `--limit <件数>` (デフォルト10), `--query <クエリ 文字列>`

*   **ファイルダウンロード**
    *   `python scripts/download_file.py --file_id <FILE_ID> --output <PATH>`
    *   指定したFile IDのファイルをダウンロードします。
    *   Googleドキュメント形式（Docs, Sheets, Slides）の場合はPDFとしてエクスポートします（デフォルト）。

### 3. Google Sheets（スプレッドシート操作）

*   **シート読み込み**
    *   `python scripts/read_sheet.py --spreadsheet_id <ID> --range "Sheet1!A1:E10"`
    *   指定範囲のデータを読み込み、CSV形式またはJSON形式で標準出力します。

## 注意事項

*   クレデンシャルとトークンはすべてGCP Secret Managerで管理されています。
*   ローカルに `credentials.json` や `token.json` を配置する必要はありません。
*   `GCP_PROJECT_ID` 環境変数でプロジェクトIDを指定できます（未設定の場合はADCから自動取得）。
