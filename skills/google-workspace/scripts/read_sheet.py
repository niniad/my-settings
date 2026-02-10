import os.path
import argparse
import json
import csv
import sys
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/spreadsheets.readonly'
]
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN_FILE = os.path.join(BASE_DIR, 'token.json')

def main():
    parser = argparse.ArgumentParser(description='Read a Google Sheet')
    parser.add_argument('--spreadsheet_id', required=True, help='The ID of the spreadsheet')
    parser.add_argument('--range', default='Sheet1!A1:Z100', help='The range to read (e.g. Sheet1!A1:E10). Defaults to Sheet1!A1:Z100')
    parser.add_argument('--info', action='store_true', help='Show spreadsheet metadata (sheet names/IDs) instead of reading data')
    parser.add_argument('--format', choices=['json', 'csv', 'table'], default='table', help='Output format (json, csv, table)')
    args = parser.parse_args()

    if not os.path.exists(TOKEN_FILE):
        print("Error: token.json not found. Please run 'python scripts/auth.py' first.")
        return

    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds.valid:
        if creds.expired and creds.refresh_token:
             creds.refresh(Request())
        else:
             print("Token invalid. Run auth.py.")
             return

    service = build('sheets', 'v4', credentials=creds)

    try:
        sheet = service.spreadsheets()
    
        # Extract ID if URL is provided
        target_id = args.spreadsheet_id
        if 'docs.google.com/spreadsheets' in target_id:
            try:
                # Extract ID usually found between /d/ and /edit
                start_marker = '/d/'
                
                # Check for /u/0/d/ format too
                if '/d/' in target_id:
                     start_index = target_id.find('/d/') + 3
                else: 
                     start_index = 0
                
                end_marker = '/edit'
                end_index = target_id.find(end_marker)
                
                if end_index != -1:
                    target_id = target_id[start_index:end_index]
                else:
                    # Case where /edit might not be present, take until next slash or end
                    remaining = target_id[start_index:]
                    if '/' in remaining:
                        target_id = remaining.split('/')[0]
                    else:
                        target_id = remaining
            except Exception:
                pass # Fallback to using the original string

        if args.info:
            print(f"Fetching metadata for Spreadsheet ID: {target_id}")
            metadata = sheet.get(spreadsheetId=target_id).execute()
            print(f"Title: {metadata.get('properties', {}).get('title')}")
            print("Sheets:")
            for s in metadata.get('sheets', []):
                props = s.get('properties', {})
                print(f" - ID: {props.get('sheetId')} | Title: {props.get('title')}")
            return

        result = sheet.values().get(spreadsheetId=target_id,
                                    range=args.range).execute()
        values = result.get('values', [])

        if not values:
            print('No data found.')
            return

        if args.format == 'json':
            print(json.dumps(values, ensure_ascii=False, indent=2))
        elif args.format == 'csv':
            writer = csv.writer(sys.stdout)
            writer.writerows(values)
        else: # table
            for row in values:
                # Handle None/missing values padding if necessary, but simple join is fine for visuals
                print(' | '.join([str(c) for c in row]))

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    main()
