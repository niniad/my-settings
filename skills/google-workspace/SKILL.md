---
name: google-workspace
description: Google DriveおよびGoogle Sheetsを操作するスキル。ファイルの閲覧・検索・ダウンロード、スプレッドシートの読み書き（更新・追記・クリア・シート管理）を行います。
---

# Google Workspace Skill

Google DriveおよびGoogle Sheets APIを利用して、ファイルの検索・閲覧・ダウンロード、スプレッドシートの読み書きを行うスキルです。

## 前提条件

1.  **GCPプロジェクト設定**
    *   Google Cloud Consoleでプロジェクトを作成（または既存を使用）。
    *   **Google Drive API** と **Google Sheets API** を有効化してください。
    *   **Secret Manager API** を有効化してください。
    *   **OAuth同意画面** を設定（User Type: External/Internal, Test Usersに追加など）。
    *   **OAuth 2.0 クライアント ID** を作成（アプリケーションの種類: **デスクトップ アプリ**）。

2.  **Secret Managerにクレデンシャルを登録**
    *   ダウンロードしたOAuth JSONを `GOOGLE_WORKSPACE_CREDENTIALS` として登録:
    ```bash
    gcloud secrets create GOOGLE_WORKSPACE_CREDENTIALS --project=YOUR_PROJECT_ID
    cat downloaded-credentials.json | gcloud secrets versions add GOOGLE_WORKSPACE_CREDENTIALS --data-file=- --project=YOUR_PROJECT_ID
    ```
    *   トークン用のシークレットも事前作成:
    ```bash
    gcloud secrets create GOOGLE_WORKSPACE_TOKEN --project=YOUR_PROJECT_ID
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
    *   `--info` でシート名・ID一覧を表示。`--format json|csv|table` で出力形式を指定。

*   **セル値の更新**
    *   `python scripts/write_sheet.py --spreadsheet_id <ID> update --range "Sheet1!A1:C2" --values '[["a","b","c"],["d","e","f"]]'`
    *   指定範囲のセル値を上書きします。`--raw` で数式解釈を無効化。

*   **行の追記（末尾追加）**
    *   `python scripts/write_sheet.py --spreadsheet_id <ID> append --range "Sheet1!A:E" --values '[["新規","データ"]]'`
    *   既存データの末尾に行を追加します。

*   **セル値のクリア**
    *   `python scripts/write_sheet.py --spreadsheet_id <ID> clear --range "Sheet1!A1:C10"`
    *   指定範囲のセル値を削除します（書式は保持）。

*   **シートの追加**
    *   `python scripts/write_sheet.py --spreadsheet_id <ID> add-sheet --title "新シート"`

*   **シートの削除**
    *   `python scripts/write_sheet.py --spreadsheet_id <ID> delete-sheet --sheet_id <SHEET_ID>`
    *   シートIDは `read_sheet.py --info` で確認できます。

## 注意事項

*   クレデンシャルとトークンはすべてGCP Secret Managerで管理されています。
*   ローカルに `credentials.json` や `token.json` を配置する必要はありません。
*   `GCP_PROJECT_ID` 環境変数でプロジェクトIDを指定できます（未設定の場合はADCから自動取得）。
*   スコープ変更（Sheets書き込み対応）後は `python scripts/auth.py` で再認証が必要です。
