
import os
import json
import argparse
import time
import subprocess
from datetime import datetime, timedelta
import requests
from auth import get_access_token, get_company_id, get_headers, FREEE_API_BASE
import sys
sys.stdout.reconfigure(encoding="utf-8")

# Configuration
TARGET_BUCKET = 'gs://sp-api-bucket/freee/deals'
LOCAL_FILE = 'deals.jsonl'

def upload_to_gcs(filename):
    gcs_path = f"{TARGET_BUCKET}/{filename}"
    print(f"Uploading {filename} to {gcs_path}...")
    try:
        subprocess.check_call(['gsutil', 'cp', filename, gcs_path], shell=True)
        print("Upload successful.")
    except subprocess.CalledProcessError as e:
        print(f"Upload failed: {e}")

def fetch_all_deals(start_date=None):
    token = get_access_token()
    cid = get_company_id(token)
    headers = get_headers(token)
    
    url = f"{FREEE_API_BASE}/deals"
    limit = 100
    offset = 0
    all_deals = []
    
    print(f"Fetching deals for Company ID: {cid}...")
    
    while True:
        params = {
            "company_id": cid,
            "limit": limit,
            "offset": offset
        }
        if start_date:
            params["start_issue_date"] = start_date

        try:
            res = requests.get(url, headers=headers, params=params)
            res.raise_for_status()
            data = res.json()
            deals = data.get("deals", [])
            
            if not deals:
                break
                
            all_deals.extend(deals)
            print(f"Fetched {len(deals)} deals (Total: {len(all_deals)})...")
            
            offset += limit
            time.sleep(0.5) # Be nice to API
            
        except Exception as e:
            print(f"Error fetching deals: {e}")
            break
    
    return all_deals

def save_to_jsonl(deals, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        for deal in deals:
            f.write(json.dumps(deal, ensure_ascii=False) + '\n')
    print(f"Saved {len(deals)} deals to {filename}")

if __name__ == "__main__":
    # Default to fetching from 2023-01-01 if strictly needed, or all.
    # User mentioned backfill/history importance.
    start_date = "2023-01-01" 
    
    deals = fetch_all_deals(start_date)
    
    if deals:
        save_to_jsonl(deals, LOCAL_FILE)
        upload_to_gcs(LOCAL_FILE)
    else:
        print("No deals found.")
