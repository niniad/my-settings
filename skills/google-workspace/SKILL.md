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
    *   **OAuth同意画面** を設定（User Type: External/Internal, Test Usersに追加など）。
    *   **OAuth 2.0 クライアント ID** を作成（アプリケーションの種類: **デスクトップ アプリ**）。
    *   JSONファイルをダウンロードし、`credentials.json` という名前で `projects/.agent/skills/google-workspace/` 直下に配置してください。

2.  **ライブラリのインストール**
    *   以下のコマンドで必要なPythonライブラリをインストールしてください。
    ```bash
    pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib pandas
    ```

3.  **認証（初回のみ）**
    *   `python scripts/auth.py` を実行して認証を行ってください。
    *   ブラウザが起動し、Googleアカウントへのログインと許可が求められます。
    *   認証が成功すると `token.json` が生成されます。

## 利用可能なスクリプト

全てのスクリプトは `scripts/` ディレクトリに配置されています。

### 1. 認証

*   **認証実行**
    *   `python scripts/auth.py`
    *   `credentials.json` を読み込み、OAuth認証フローを実行して `token.json` を生成します。

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

*   `token.json` にはアクセストークンが含まれます。git等にコミットしないでください。
*   `credentials.json` は秘密情報です。取り扱いに注意してください。
