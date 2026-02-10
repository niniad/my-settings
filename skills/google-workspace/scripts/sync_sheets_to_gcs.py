
import os
import csv
import sys
import subprocess
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Configuration
SPREADSHEET_ID = '1mMuw4LSeobfzr66jVhojMX83iEkd4bvDmfx7VJfido8'
TARGET_BUCKET = 'gs://sp-api-bucket/google_sheets'
SHEETS = {
    'deposit_inflow': 'deposit_inflow!A:Z',
    'agency_ledger': 'agency_ledger!A:Z',
    'external_payments': 'external_payments!A:Z',
    'po_details': 'po_details!A:Z'
}
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN_FILE = os.path.join(BASE_DIR, 'token.json')

def get_service():
    if not os.path.exists(TOKEN_FILE):
        print("Error: token.json not found.")
        sys.exit(1)
    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            print("Token invalid.")
            sys.exit(1)
    return build('sheets', 'v4', credentials=creds)

def download_sheet(service, sheet_name, range_name):
    print(f"Downloading {sheet_name}...")
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=range_name).execute()
    values = result.get('values', [])
    
    if not values:
        print(f"No data found for {sheet_name}.")
        return None

    filename = f"{sheet_name}.csv"
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(values)
    print(f"Saved {filename}")
    return filename

def upload_to_gcs(filename):
    gcs_path = f"{TARGET_BUCKET}/{filename}"
    print(f"Uploading {filename} to {gcs_path}...")
    try:
        # Use shell=True for Windows to find gcutil (usually a batch file)
        subprocess.check_call(['gsutil', 'cp', filename, gcs_path], shell=True)
        print("Upload successful.")
    except subprocess.CalledProcessError as e:
        print(f"Upload failed: {e}")

def main():
    service = get_service()
    for name, rng in SHEETS.items():
        filename = download_sheet(service, name, rng)
        if filename:
            upload_to_gcs(filename)
            os.remove(filename) # Clean up

if __name__ == '__main__':
    main()
