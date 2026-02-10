import os
import sys
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# Add scripts directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from secret_helper import get_credentials_info, get_token_info, save_token

# Scopes for reading Drive files and Sheets
SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/spreadsheets.readonly'
]


def get_google_creds():
    """Secret Managerからトークンを取得し、有効なCredentialsオブジェクトを返す"""
    creds = None

    try:
        token_info = get_token_info()
        creds = Credentials.from_authorized_user_info(token_info, SCOPES)
    except Exception:
        pass

    if creds and not creds.valid:
        if creds.expired and creds.refresh_token:
            print("Refreshing expired token...")
            try:
                creds.refresh(Request())
                save_token(creds.to_json())
                return creds
            except Exception as e:
                print(f"Error refreshing token: {e}")
                creds = None

    if creds and creds.valid:
        return creds

    return None


def main():
    """初回認証用。Secret ManagerからOAuthクレデンシャルを取得し、認証フローを実行する。"""
    creds = get_google_creds()

    if creds:
        print("Authentication successful! (existing token is valid)")
        return

    # 初回認証: credentials情報からOAuthフローを実行
    print("Initiating OAuth flow...")
    try:
        credentials_info = get_credentials_info()
    except Exception as e:
        print(f"Error: Failed to get credentials from Secret Manager: {e}")
        print("Please store google_workspace_credentials in Secret Manager first.")
        print("Example:")
        print('  echo \'{"installed":{...}}\' | gcloud secrets versions add google_workspace_credentials --data-file=-')
        return

    flow = InstalledAppFlow.from_client_config(credentials_info, SCOPES)
    creds = flow.run_local_server(port=0)

    # トークンをSecret Managerに保存
    save_token(creds.to_json())
    print("Token saved to Secret Manager (google_workspace_token)")
    print("Authentication successful!")


if __name__ == '__main__':
    main()
