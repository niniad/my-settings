
import os
import csv
import sys
import subprocess
from googleapiclient.discovery import build

# Add scripts directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from auth import get_google_creds

# Configuration for REAL DATA (cost_details)
SPREADSHEET_ID = '1bsxFCEucHzOieP38wra8JF7mfxDBcn-Kk4l7hoqIoGk'
TARGET_BUCKET = 'gs://sp-api-bucket/real_sheets'
SHEETS = {
    'shipments': 'shipments!A:Z',
    'shipment_details': 'shipment_details!A:Z',
    'po_details': 'po_details!A:Z'
}

def get_service():
    creds = get_google_creds()
    if not creds:
        print("Error: No valid credentials. Please run 'python scripts/auth.py' first.")
        sys.exit(1)
    return build('sheets', 'v4', credentials=creds)

def download_sheet(service, sheet_name, range_name):
    print(f"Downloading {sheet_name}...")
    try:
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
    except Exception as e:
        print(f"Error downloading {sheet_name}: {e}")
        return None

def upload_to_gcs(filename):
    gcs_path = f"{TARGET_BUCKET}/{filename}"
    print(f"Uploading {filename} to {gcs_path}...")
    try:
        # Use shell=True for Windows
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
            # os.remove(filename) # Keep for inspection if needed, or uncomment to clean

if __name__ == '__main__':
    main()
