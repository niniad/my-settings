
"""
Script to list receipts (files) from freee filebox.
"""
import requests
import json
import argparse
from auth import get_access_token, get_company_id, get_headers, FREEE_API_BASE

def list_receipts(start_date=None, end_date=None):
    token = get_access_token()
    cid = get_company_id(token)
    
    url = f"{FREEE_API_BASE}/receipts"
    params = {
        "company_id": cid,
        "limit": 100
    }
    if start_date: params["start_date"] = start_date
    if end_date: params["end_date"] = end_date
    
    res = requests.get(url, headers=get_headers(token), params=params)
    res.raise_for_status()
    
    receipts = res.json().get("receipts", [])
    
    print(f"--- Receipts (Found: {len(receipts)}) ---")
    for r in receipts:
        status_str = r.get('status', 'unknown')
        print(f"ID: {r['id']} | Date: {r['issue_date']} | Status: {status_str} | File: {r.get('file_name')}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="List receipts from freee.")
    parser.add_argument("--start_date", help="Start date YYYY-MM-DD")
    parser.add_argument("--end_date", help="End date YYYY-MM-DD")
    args = parser.parse_args()
    
    list_receipts(args.start_date, args.end_date)
