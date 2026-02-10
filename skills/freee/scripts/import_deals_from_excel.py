
import pandas as pd
import requests
import json
import time
import sys
import os
from auth import get_access_token, get_company_id, get_headers, FREEE_API_BASE

# Mappings (Cache)
ACCOUNT_ITEMS = {}
TAX_CODES = {}
PARTNERS = {}
WALLETS = {}
ACCOUNT_CATEGORIES = {}

def load_metadata(headers, company_id):
    print("Loading Metadata...")
    # Account Items
    res = requests.get(f"{FREEE_API_BASE}/account_items?company_id={company_id}", headers=headers)
    if res.ok:
        for item in res.json()['account_items']:
            ACCOUNT_ITEMS[item['name']] = item['id']
            # Cache Category
            # API returns 'account_category_id' or logical category?
            # Actually, `group_name` or `walletable_id`.
            # Use `shortcut1` or `shortcut_num`? No.
            # Best is to rely on IDs or names.
            # Simplified: If name in known PL list? No.
            # Let's inspect ONE item to see structure. Assuming 'group_name' exists.
            # But wait, I can just use a Try-Catch on the processing.
            # Better: Fetch Account Item Details.
            pass
            # Also handle shortcut names if needed
    
    # Tax Codes
    res = requests.get(f"{FREEE_API_BASE}/taxes/companies/{company_id}", headers=headers)
    if res.ok:
        for item in res.json()['taxes']:
            TAX_CODES[item['name']] = item['code']

    # Partners
    res = requests.get(f"{FREEE_API_BASE}/partners?company_id={company_id}", headers=headers)
    if res.ok:
        for item in res.json()['partners']:
            PARTNERS[item['name']] = item['id']
            PARTNERS[item['code']] = item['id'] # Support code lookup

    # Walletables
    res = requests.get(f"{FREEE_API_BASE}/walletables?company_id={company_id}", headers=headers)
    if res.ok:
        for item in res.json()['walletables']:
            WALLETS[item['name']] = {'id': item['id'], 'type': item['type']}

def get_tax_code(name):
    # Map Excel names to Freee names if ambiguous
    # '課対仕入10%' -> 108 (usually)
    # This might need fuzzy matching or strict mapping.
    # For now, rely on API name match.
    if name in TAX_CODES: return TAX_CODES[name]
    # Fallback common imports
    if '課対仕入10%' in str(name): return 108
    if '対象外' in str(name): return 1
    return 108 # Default 10%

def process_file(file_path):
    token = get_access_token()
    company_id = get_company_id(token)
    headers = get_headers(token)
    
    if not ACCOUNT_ITEMS:
        load_metadata(headers, company_id)

    df = pd.read_excel(file_path)
    print(f"Processing {len(df)} rows from {os.path.basename(file_path)}...")

    for index, row in df.iterrows():
        # Logic to determine Deal Type
        dr_name = row['借方勘定科目']
        cr_name = row['貸方勘定科目']
        
        # SKIP if Dr is Money (Wallet) AND Cr is Money/BS (Settlement/Transfer)
        # Heuristic: If Dr is in WALLETS, skip (treat as settlement or transfer) -> Manually handle later?
        # User wants "Deals" for Cost Allocation. Costs are Expenses.
        if dr_name in WALLETS:
            print(f"Skipping Row {index}: Dr is Wallet ({dr_name}) - likely Settlement/Transfer.")
            continue
            
        # If Dr is '売掛金' (AR) -> Sales Occurrence? -> Income Deal.
        # But 'Sales Occurrence' usually has Cr = Sales.
        # If row is `Dr 売掛金 / Cr 売上高` -> Income Deal.
        # If row is `Dr 仕入高 / Cr 買掛金` -> Expense Deal.
        
        # Primary Check: Is Dr an Expense? Or Cr an Income?
        # We don't have categories mapped, but we know Wallets.
        
        is_income = False
        is_expense = False
        
        # Simple Name Heuristics for common PL items to be safe
        # Or just assume: If not Wallet, it is PL?
        if dr_name not in WALLETS: is_expense = True
        
        # If Cr is Sales (Income), override
        if '売上' in str(cr_name) or '受取' in str(cr_name) or 'Income' in str(cr_name):
            is_income = True
            is_expense = False
        
        amount = row['借方金額']
        date = str(row['発生日']).split(' ')[0].replace('/', '-')
        desc = str(row['摘要'])
        if 'nan' in desc: desc = ""

        # Build Payload
        payload = {
            "company_id": company_id,
            "issue_date": date,
            "type": "income" if is_income else "expense",
            "details": [
                {
                    "tax_code": get_tax_code(row['貸方税区分'] if is_income else row['借方税区分']),
                    "account_item_id": ACCOUNT_ITEMS.get(cr_name if is_income else dr_name),
                    "amount": amount,
                    "description": desc
                }
            ],
            "payments": []
        }
        
        if not payload['details'][0]['account_item_id']:
            print(f"Skipping Row {index}: Unknown Account {dr_name}")
            continue

        # Payment / Settlement
        if cr_name in WALLETS:
            payload['payments'].append({
                "amount": amount,
                "from_walletable_id": WALLETS[cr_name]['id'],
                "from_walletable_type": WALLETS[cr_name]['type'],
                "date": date 
            })
        else:
            # Unsettled or Partner?
            # If Cr is 'YP', check if partner
            if cr_name in PARTNERS:
                payload['partner_id'] = PARTNERS[cr_name]
                # Unsettled expense
            else:
                # If Cr is '未払金' or similar generic liability without partner?
                # Treat as Unsettled.
                pass
        
        # POST
        res = requests.post(f"{FREEE_API_BASE}/deals", headers=headers, json=payload)
        if res.status_code == 201:
            print(f"Row {index}: Created Deal {date} {amount}")
        else:
            print(f"Row {index}: Failed {res.text}")
        
        time.sleep(0.1)

if __name__ == "__main__":
    files = [
        r"c:\Users\ninni\Documents\projects\freee\money_forward\freee_import_2023.xlsx",
        r"c:\Users\ninni\Documents\projects\freee\money_forward\freee_import_2024.xlsx",
        r"c:\Users\ninni\Documents\projects\freee\money_forward\freee_import_2025.xlsx"
    ]
    for f in files:
        process_file(f)
