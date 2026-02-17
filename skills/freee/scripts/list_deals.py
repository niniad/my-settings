
"""
Script to list transactions (deals) from freee.
"""
import requests
import json
import argparse
from auth import get_access_token, get_company_id, get_headers, FREEE_API_BASE
import sys
sys.stdout.reconfigure(encoding="utf-8")

def list_deals(limit=20, start_date=None, end_date=None, keyword=None):
    token = get_access_token()
    cid = get_company_id(token)
    
    url = f"{FREEE_API_BASE}/deals"
    params = {
        "company_id": cid,
        "limit": limit
    }
    if start_date: params["start_issue_date"] = start_date
    if end_date: params["end_issue_date"] = end_date
    # Keyword search not directly supported by deals endpoint widely like SQL, 
    # but some filtering parameters exist (status, type, etc.)
    # For now we stick to dates.
    
    res = requests.get(url, headers=get_headers(token), params=params)
    res.raise_for_status()
    
    deals = res.json().get("deals", [])
    
    print(f"--- Deals (Found: {len(deals)}) ---")
    for d in deals:
        print(f"ID: {d['id']} | Date: {d['issue_date']} | Amount: {d['amount']} | Type: {d['type']}")
        # Show details
        for detail in d.get("details", []):
             print(f"  - {detail.get('account_item_name')} / {detail.get('tax_code_name')} : {detail.get('amount')}")
        print("-" * 20)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="List deals from freee.")
    parser.add_argument("--limit", type=int, default=20, help="Number of deals to fetch")
    parser.add_argument("--start_date", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end_date", type=str, help="End date (YYYY-MM-DD)")
    args = parser.parse_args()
    
    list_deals(args.limit, args.start_date, args.end_date)
