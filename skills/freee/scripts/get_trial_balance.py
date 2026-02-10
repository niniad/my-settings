
"""
Script to get Trial Balance (PL/BS) from freee.
"""
import requests
import json
import argparse
from auth import get_access_token, get_company_id, get_headers, FREEE_API_BASE

def get_trial_balance(fiscal_year):
    token = get_access_token()
    cid = get_company_id(token)
    
    # Reports endpoint
    url = f"{FREEE_API_BASE}/reports/trial_balance"
    params = {
        "company_id": cid,
        "fiscal_year": fiscal_year
        # "breakdown_display_type": "partner" # Optional
    }
    
    print(f"Fetching Trial Balance for FY{fiscal_year}...")
    res = requests.get(url, headers=get_headers(token), params=params)
    res.raise_for_status()
    
    data = res.json().get("trial_balance", {})
    balances = data.get("balances", [])
    
    print(f"--- Trial Balance FY{fiscal_year} (Top items) ---")
    # Show top items by amount? Or just list important ones like Sales
    
    # Simple dump of hierarchical view is hard in CLI, list flat items
    for item in balances:
         # account_item_name, amount
         name = item.get("account_item_name")
         amount = item.get("closing_balance")
         print(f"{name}: {amount}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get Trial Balance from freee.")
    parser.add_argument("--fiscal_year", required=True, type=int, help="Fiscal Year (e.g. 2024)")
    args = parser.parse_args()
    
    get_trial_balance(args.fiscal_year)
