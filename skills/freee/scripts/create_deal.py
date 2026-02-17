
"""
Script to create a transaction (deal) in freee.
IMPORTANT: This performs a write operation. Ensure user confirmation before running.
"""
import requests
import json
import argparse
from auth import get_access_token, get_company_id, get_headers, FREEE_API_BASE
import sys
sys.stdout.reconfigure(encoding="utf-8")

def create_deal(issue_date, type, amount, account_item_id, tax_code, partner_id=None, description=None):
    token = get_access_token()
    cid = get_company_id(token)
    
    url = f"{FREEE_API_BASE}/deals"
    
    # Basic single-line deal structure
    payload = {
        "company_id": cid,
        "issue_date": issue_date,
        "type": type, # 'income' or 'expense'
        "details": [
            {
                "tax_code": tax_code,
                "account_item_id": account_item_id,
                "amount": amount,
                "description": description
                # "partner_id": partner_id (if needed)
            }
        ]
    }
    if partner_id:
        payload["partner_id"] = partner_id
        
    print(f"Creating Deal: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    confirm = input("Are you sure you want to create this deal? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        return

    res = requests.post(url, headers=get_headers(token), json=payload)
    if res.status_code == 201:
        print("Success! Deal created.")
        print(json.dumps(res.json(), indent=2, ensure_ascii=False))
    else:
        print(f"Failed: {res.status_code}")
        print(res.text)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create a deal in freee.")
    parser.add_argument("--date", required=True, help="Issue Date YYYY-MM-DD")
    parser.add_argument("--type", required=True, choices=["income", "expense"], help="Type: income or expense")
    parser.add_argument("--amount", required=True, type=int, help="Amount")
    parser.add_argument("--account_item_id", required=True, type=int, help="Account Item ID (e.g. 12345)")
    parser.add_argument("--tax_code", required=True, type=int, help="Tax Code (e.g. 108)")
    parser.add_argument("--partner_id", type=int, help="Partner ID")
    parser.add_argument("--description", type=str, help="Description")
    
    args = parser.parse_args()
    
    create_deal(args.date, args.type, args.amount, args.account_item_id, args.tax_code, args.partner_id, args.description)
