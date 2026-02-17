
"""
Script to create an Invoice in freee.
IMPORTANT: This performs a write operation. Ensure user confirmation before running.
"""
import requests
import json
import argparse
from auth import get_access_token, get_company_id, get_headers, FREEE_API_BASE
import sys
sys.stdout.reconfigure(encoding="utf-8")

def create_invoice(partner_id, issue_date, due_date, amount, description):
    token = get_access_token()
    cid = get_company_id(token)
    
    url = f"{FREEE_API_BASE}/invoices"
    
    # Simplified invoice creation
    payload = {
        "company_id": cid,
        "issue_date": issue_date,
        "due_date": due_date,
        "partner_id": partner_id,
        "invoice_contents": [
            {
                "order": 0,
                "type": "normal",
                "quantity": 1,
                "unit_price": amount,
                "vat": int(amount * 0.1), # Simple 10% assumption for demo
                "description": description,
                "account_item_id": 12345, # Placeholder, user needs to specify or lookup
                "tax_code": 129 # Placeholder for tax code
            }
        ]
    }
    
    print("WARNING: This script uses placeholder Account Item ID and Tax Code.")
    print(f"Creating Invoice: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    confirm = input("Are you sure you want to create this invoice? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        return

    res = requests.post(url, headers=get_headers(token), json=payload)
    if res.status_code == 201:
        print("Success! Invoice created.")
        print(json.dumps(res.json(), indent=2, ensure_ascii=False))
    else:
        print(f"Failed: {res.status_code}")
        print(res.text)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create an invoice in freee.")
    parser.add_argument("--partner_id", required=True, type=int, help="Partner ID")
    parser.add_argument("--issue_date", required=True, help="Issue Date YYYY-MM-DD")
    parser.add_argument("--due_date", required=True, help="Due Date YYYY-MM-DD")
    parser.add_argument("--amount", required=True, type=int, help="Amount")
    parser.add_argument("--description", required=True, help="Description")
    
    args = parser.parse_args()
    
    create_invoice(args.partner_id, args.issue_date, args.due_date, args.amount, args.description)
