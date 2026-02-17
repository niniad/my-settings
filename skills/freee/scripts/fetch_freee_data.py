
import os
import json
import argparse
import time
import subprocess
from datetime import datetime
import requests
from auth import get_access_token, get_company_id, get_headers, FREEE_API_BASE
import sys
sys.stdout.reconfigure(encoding="utf-8")

# Configuration
BUCKET_BASE = 'gs://sp-api-bucket/freee'
ENDPOINTS = {
    'manual_journals': 'manual_journals',
    'wallet_txns': 'wallet_txns'
}

def upload_to_gcs(filename, subfolder):
    gcs_path = f"{BUCKET_BASE}/{subfolder}/{filename}"
    print(f"Uploading {filename} to {gcs_path}...")
    try:
        subprocess.check_call(['gsutil', 'cp', filename, gcs_path], shell=True)
        print("Upload successful.")
    except subprocess.CalledProcessError as e:
        print(f"Upload failed: {e}")

def fetch_data(endpoint, start_date=None, limit=100):
    token = get_access_token()
    cid = get_company_id(token)
    headers = get_headers(token)
    
    url = f"{FREEE_API_BASE}/{endpoint}"
    offset = 0
    all_data = []
    
    print(f"Fetching {endpoint} for Company ID: {cid}...")
    
    while True:
        params = {
            "company_id": cid,
            "limit": limit,
            "offset": offset
        }
        # Note: manual_journals use issue_date, wallet_txns use date (start_date/end_date)
        if start_date:
            if endpoint == 'manual_journals':
                params["start_issue_date"] = start_date
            elif endpoint == 'wallet_txns':
                params["start_date"] = start_date

        try:
            res = requests.get(url, headers=headers, params=params)
            res.raise_for_status()
            data = res.json()
            items = data.get(endpoint, [])
            
            if not items:
                break
                
            all_data.extend(items)
            print(f"Fetched {len(items)} items (Total: {len(all_data)})...")
            
            offset += limit
            time.sleep(0.5) 
            
        except Exception as e:
            print(f"Error fetching {endpoint}: {e}")
            break
    
    return all_data

def save_to_jsonl(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    print(f"Saved {len(data)} items to {filename}")

if __name__ == "__main__":
    start_date = "2023-01-01" # Set a reasonable start date
    
    for key, endpoint in ENDPOINTS.items():
        data = fetch_data(endpoint, start_date)
        if data:
            filename = f"{key}.jsonl"
            save_to_jsonl(data, filename)
            upload_to_gcs(filename, key)
        else:
            print(f"No data found for {key}")
