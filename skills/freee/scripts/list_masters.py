
"""
Script to list masters (Partners, Items, Account Items) from freee.
"""
import requests
import json
import argparse
from auth import get_access_token, get_company_id, get_headers, FREEE_API_BASE
import sys
sys.stdout.reconfigure(encoding="utf-8")

def list_master(resource_name):
    token = get_access_token()
    cid = get_company_id(token)
    
    # resource_name: partners, items, account_items
    url = f"{FREEE_API_BASE}/{resource_name}"
    params = {"company_id": cid}
    
    print(f"Fetching {resource_name}...")
    res = requests.get(url, headers=get_headers(token), params=params)
    res.raise_for_status()
    
    data = res.json().get(resource_name, [])
    
    # Special handling for account items structure which is different
    if resource_name == "account_items":
        data = res.json().get("account_items", [])
    
    print(f"--- {resource_name} (Found: {len(data)}) ---")
    for item in data:
        print(f"ID: {item['id']} | Name: {item['name']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="List masters from freee.")
    parser.add_argument("resource", choices=["partners", "items", "account_items"], help="Resource to list")
    args = parser.parse_args()
    
    list_master(args.resource)
