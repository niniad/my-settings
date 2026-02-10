
import os
import argparse
import sys
import json
import requests
import datetime
from google.cloud import bigquery
from google.oauth2.credentials import Credentials

# Configuration
FREEE_COMPANY_ID = 'your_company_id_here' # User needs to set this or script finds it
FREEE_API_URL = 'https://api.freee.co.jp'
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN_FILE = os.path.join(BASE_DIR, 'token.json')

def get_access_token():
    if not os.path.exists(TOKEN_FILE):
        print(f"Error: {TOKEN_FILE} not found. Run manual_auth.py.")
        sys.exit(1)
    with open(TOKEN_FILE, 'r') as f:
        tokens = json.load(f)
    return tokens.get('access_token')

def get_company_id(access_token):
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(f'{FREEE_API_URL}/api/1/companies', headers=headers)
    if response.status_code == 200:
        companies = response.json().get('companies', [])
        if companies:
            return companies[0]['id'] # Use first company
    print("Error fetching company ID")
    sys.exit(1)

def get_bq_data():
    client = bigquery.Client()
    query = """
        SELECT 
            po_number, 
            CAST(ANY_VALUE(order_date) AS STRING) as order_date,
            SUM(total_unit_cost_jpy * qty) as amount
        FROM `main-project-477501.analytics.view_product_costs`
        GROUP BY po_number
        HAVING amount > 0
        ORDER BY order_date DESC
    """
    return client.query(query).result()

def create_manual_journal(access_token, company_id, po_number, data, dry_run=False):
    # Check for existing logic (omitted for MVP, but strongly recommended)
    
    amount = int(data.amount)
    date_str = data.order_date
    
    payload = {
        "company_id": company_id,
        "issue_date": date_str,
        "details": [
            {
                "entry_side": "debit",
                "tax_code": 22, # Input (Non-taxable for import? need verification. 22=課対仕入(10%) usually. Import is different)
                # For MVP, using standard purchase.
                "account_item_id": 111, # Placeholder for Purchase
                "amount": amount,
                "description": f"PO: {po_number} (Import)"
            },
            {
                "entry_side": "credit",
                "tax_code": None,
                "account_item_id": 222, # Placeholder for Deposit/Prepaid
                "amount": amount,
                "description": f"PO: {po_number} - Deposit"
            }
        ]
    }
    
    print(f"Preparing Journal for {po_number}: {date_str}, Amount: {amount}")
    if dry_run:
        print("  [Dry Run] Skipping API Call")
        return

    # Call API
    # response = requests.post(...)
    print("  [Mock] Created Journal Entry (API call commented out for safety in this demo)")

def main():
    parser = argparse.ArgumentParser(description='Sync BQ Purchases to freee')
    parser.add_argument('--dry-run', action='store_true', default=True) # Default dry-run
    args = parser.parse_args()

    # Auth
    try:
        access_token = get_access_token()
    except Exception:
        print("Auth failed. Please ensure token.json exists.")
        return

    company_id = get_company_id(access_token)
    print(f"Target Company ID: {company_id}")

    # Data
    print("Fetching POs from BigQuery...")
    rows = get_bq_data()
    
    for row in rows:
        create_manual_journal(access_token, company_id, row.po_number, row, dry_run=args.dry_run)

if __name__ == '__main__':
    main()
