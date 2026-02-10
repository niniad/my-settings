import os.path
import argparse
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# We match the scopes from auth.py to ensure the token is valid
SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/spreadsheets.readonly'
]

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN_FILE = os.path.join(BASE_DIR, 'token.json')

def main():
    parser = argparse.ArgumentParser(description='List files in Google Drive')
    parser.add_argument('--limit', type=int, default=10, help='Maximum number of files to return')
    parser.add_argument('--query', type=str, default=None, help='Query string for filtering files (e.g. "name contains \'report\'")')
    args = parser.parse_args()

    if not os.path.exists(TOKEN_FILE):
        print("Error: token.json not found. Please run 'python scripts/auth.py' first.")
        return

    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            print("Refreshing token...")
            creds.refresh(Request())
        else:
            print("Token invalid. Run auth.py.")
            return

    service = build('drive', 'v3', credentials=creds)

    query = args.query
    if query:
        if "trashed" not in query:
             query += " and trashed = false"
    else:
        query = "trashed = false"

    try:
        results = service.files().list(
            q=query,
            pageSize=args.limit,
            fields="nextPageToken, files(id, name, mimeType, webViewLink)",
        ).execute()
        
        items = results.get('files', [])

        if not items:
            print('No files found.')
        else:
            print(f'Found {len(items)} files:')
            for item in items:
                print(f"[File] {item['name']}")
                print(f"  ID: {item['id']}")
                print(f"  Type: {item['mimeType']}")
                print(f"  Link: {item['webViewLink']}")
                print("-" * 20)

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    main()
