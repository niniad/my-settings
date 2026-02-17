
"""
Script to create a master item (Partner or Item) in freee.
IMPORTANT: This performs a write operation. Ensure user confirmation before running.
"""
import requests
import json
import argparse
from auth import get_access_token, get_company_id, get_headers, FREEE_API_BASE
import sys
sys.stdout.reconfigure(encoding="utf-8")

def create_master(resource, name, code=None):
    token = get_access_token()
    cid = get_company_id(token)
    
    url = f"{FREEE_API_BASE}/{resource}"
    payload = {
        "company_id": cid,
        "name": name
    }
    if code:
        payload["code"] = code
        
    print(f"Creating {resource[:-1]}: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    confirm = input("Are you sure you want to create this item? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        return

    res = requests.post(url, headers=get_headers(token), json=payload)
    if res.status_code == 201:
        print("Success! Created.")
        print(json.dumps(res.json(), indent=2, ensure_ascii=False))
    else:
        print(f"Failed: {res.status_code}")
        print(res.text)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create master item in freee.")
    parser.add_argument("resource", choices=["partners", "items"], help="Resource type")
    parser.add_argument("--name", required=True, help="Name of the item")
    parser.add_argument("--code", help="Code (optional)")
    
    args = parser.parse_args()
    
    create_master(args.resource, args.name, args.code)
