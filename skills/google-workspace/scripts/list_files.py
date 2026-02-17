import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
import argparse
from googleapiclient.discovery import build

# Add scripts directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from auth import get_google_creds

def main():
    parser = argparse.ArgumentParser(description='List files in Google Drive')
    parser.add_argument('--limit', type=int, default=10, help='Maximum number of files to return')
    parser.add_argument('--query', type=str, default=None, help='Query string for filtering files (e.g. "name contains \'report\'")')
    args = parser.parse_args()

    creds = get_google_creds()
    if not creds:
        print("Error: No valid credentials. Please run 'python scripts/auth.py' first.")
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
