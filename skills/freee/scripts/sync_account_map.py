
import os
import sys
import requests
from google.cloud import bigquery
import datetime

# Reuse auth from existing script
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from auth import get_access_token, get_company_id, get_headers, FREEE_API_BASE, _get_project_id

BQ_PROJECT_ID = _get_project_id()
BQ_DATASET = "freee"
TABLE_NAME = "account_map"

# Logical Keys Mapping (From sync_settlements.py)
ACCOUNT_DEFS = {
    "sales_product": "売上高",
    "sales_shipping": "売上高",
    "sales_refunds": "売上戻り高",
    "sales_promotions": "売上値引高",
    "income_reimbursement": "雑収入",
    "expense_commission": "販売手数料",
    "expense_fba_shipping": "荷造運賃",
    "expense_advertising": "広告宣伝費",
    "expense_points": "広告宣伝費",
    "expense_storage": "地代家賃",
    "expense_subscription": "諸会費",
    "expense_other": "支払手数料",
    "reserve": "仮払金",
    "net_amount": "Amazon出品アカウント",
    "expense_cogs": "売上原価",
    "asset_inventory": "商品"
}

def get_account_items_map(token, company_id):
    url = f"{FREEE_API_BASE}/account_items"
    headers = get_headers(token)
    res = requests.get(url, headers=headers, params={"company_id": company_id})
    res.raise_for_status()
    items = res.json().get("account_items", [])
    return {item["name"]: item["id"] for item in items}

def get_taxes_map(token, company_id):
    url = f"{FREEE_API_BASE}/taxes/companies/{company_id}"
    headers = get_headers(token)
    res = requests.get(url, headers=headers)
    res.raise_for_status()
    taxes = res.json().get("taxes", [])
    
    tax_map = {}
    for t in taxes:
        t_name = t["name"]
        if t_name == "sales_with_tax_10": tax_map["sales"] = t["code"]
        elif t_name == "purchase_with_tax_10": tax_map["purchase"] = t["code"]
        elif t_name == "non_taxable": tax_map["none"] = t["code"]
            
    if "sales" not in tax_map:
         for t in taxes:
             if t["name"] == "taxable_10": tax_map["sales"] = t["code"]
    
    return tax_map

def main():
    print("Authenticating...")
    token = get_access_token()
    cid = get_company_id(token)
    
    print("Fetching Account Items...")
    item_map = get_account_items_map(token, cid)
    
    print("Fetching Tax Codes...")
    tax_codes = get_taxes_map(token, cid)
    
    # Prepare Data
    rows = []
    timestamp = datetime.datetime.utcnow().isoformat()
    
    for key, name in ACCOUNT_DEFS.items():
        if name not in item_map:
            print(f"WARNING: Account '{name}' not found for key '{key}'")
            continue
            
        item_id = item_map[name]
        
        # Determine default tax type based on key prefix
        tax_code = tax_codes.get("none") # Default
        if key.startswith("sales_"):
             tax_code = tax_codes.get("sales")
        elif key.startswith("expense_"):
             tax_code = tax_codes.get("purchase")
        
        # Override for specific types
        if key == "expense_cogs": tax_code = tax_codes.get("none") # Transfer
        if key == "sales_refunds": tax_code = tax_codes.get("sales")
        if key == "sales_promotions": tax_code = tax_codes.get("sales")
        
        # Wallet and Reserve are usually non-taxable (Asset moves)
        if key == "net_amount": tax_code = tax_codes.get("none")
        if key == "reserve": tax_code = tax_codes.get("none")
        if key == "asset_inventory": tax_code = tax_codes.get("none")
        
        rows.append({
            "logical_key": key,
            "account_item_id": item_id,
            "tax_code": tax_code,
            "account_name_debug": name,
            "updated_at": timestamp
        })
        
    # Upload to BigQuery
    client = bigquery.Client(project=BQ_PROJECT_ID)
    table_id = f"{BQ_PROJECT_ID}.{BQ_DATASET}.{TABLE_NAME}"
    
    # Define Schema
    schema = [
        bigquery.SchemaField("logical_key", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("account_item_id", "INTEGER", mode="REQUIRED"),
        bigquery.SchemaField("tax_code", "INTEGER", mode="NULLABLE"),
        bigquery.SchemaField("account_name_debug", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("updated_at", "TIMESTAMP", mode="NULLABLE"),
    ]
    
    try:
        table = client.get_table(table_id)
        print(f"Table {table_id} exists. Truncating...")
        client.query(f"TRUNCATE TABLE `{table_id}`").result()
    except:
        print(f"Creating table {table_id}...")
        table = bigquery.Table(table_id, schema=schema)
        client.create_table(table)

    print(f"Inserting {len(rows)} rows...")
    errors = client.insert_rows_json(table_id, rows)
    if errors:
        print(f"Errors: {errors}")
    else:
        print("Success.")

if __name__ == "__main__":
    main()
