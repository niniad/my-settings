import os
import sys
sys.stdout.reconfigure(encoding="utf-8")
import argparse
import datetime
import json
import requests
from google.cloud import bigquery
import google.auth

# Add current directory to path to import auth
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from auth import get_access_token, get_company_id, get_headers, FREEE_API_BASE, _get_project_id

BQ_PROJECT_ID = _get_project_id()
SOURCE_VIEW = "freee.settlement_journal_payload_view"
LOG_TABLE = "freee.import_log"

def get_unimported_payloads(client, ignore_log=False, target_id=None):
    where_clause = "1=1"
    if not ignore_log:
        where_clause += f" AND settlement_id NOT IN (SELECT settlement_id FROM `{BQ_PROJECT_ID}.{LOG_TABLE}`)"
    if target_id:
        where_clause += f" AND settlement_id = {target_id}"

    # Fetch JSON details directly from BigQuery
    # Note: TO_JSON_STRING converts the ARRAY<STRUCT> into a JSON string
    query = f"""
        SELECT 
            settlement_id, 
            FORMAT_DATE('%Y-%m-%d', DATE(issue_date)) as issue_date,
            TO_JSON_STRING(json_details) as details_json
        FROM `{BQ_PROJECT_ID}.{SOURCE_VIEW}`
        WHERE {where_clause}
        ORDER BY issue_date ASC
    """
    return list(client.query(query).result())

def post_journal(token, company_id, row):
    url = f"{FREEE_API_BASE}/manual_journals"
    headers = get_headers(token)
    
    try:
        details = json.loads(row.details_json)
    except json.JSONDecodeError:
        print(f"Error decoding JSON for Settlement {row.settlement_id}")
        return None
        
    if not details:
        print(f"Skipping Settlement {row.settlement_id}: No details generated.")
        return None

    # Filter out any incomplete lines (e.g. missing account_item_id)
    valid_details = []
    for d in details:
        if not d.get('account_item_id'):
            print(f"WARNING: Line missing Account ID (Amount: {d.get('amount')}, Desc: {d.get('description')}). Dropping.")
            continue
        valid_details.append(d)

    if not valid_details:
        print("No valid details to post.")
        return None

    payload = {
        "company_id": company_id,
        "issue_date": row.issue_date,
        "details": valid_details,
        "receipt_ids": [] 
    }
    
    res = requests.post(url, headers=headers, json=payload)
    if res.status_code != 201:
        print(f"Failed to post: {res.text}")
        return None
    return res.json()

def log_import(client, settlement_id, journal_res):
    journal_id = journal_res["manual_journal"]["id"]
    now = datetime.datetime.utcnow().isoformat()
    rows = [{
        "settlement_id": settlement_id,
        "imported_at": now,
        "freee_deal_id": journal_id,
        "freee_deal_status": "posted"
    }]
    # Check if log table has more columns, insert defaults if needed.
    # Current schema for import_log: settlement_id, imported_at, freee_deal_id, status...
    # Just minimal insert.
    errors = client.insert_rows_json(f"{BQ_PROJECT_ID}.{LOG_TABLE}", rows)
    if errors:
        print(f"Log Error: {errors}")

# ... (Previous imports)

def get_bq_client_with_drive_scope():
    scopes = [
        "https://www.googleapis.com/auth/cloud-platform",
        "https://www.googleapis.com/auth/drive"
    ]
    credentials, project = google.auth.default(scopes=scopes)
    return bigquery.Client(project=BQ_PROJECT_ID, credentials=credentials)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Dry run.")
    parser.add_argument("--yes", action="store_true", help="Skip confirmation.")
    parser.add_argument("--ignore-log", action="store_true", help="Reprocess all.")
    parser.add_argument("--settlement-id", type=int, help="Target ID.")
    args = parser.parse_args()

    # Auth
    try:
        token = get_access_token()
        cid = get_company_id(token)
        print(f"Authenticated. Company ID: {cid}")
    except Exception as e:
        print(f"Auth failed: {e}")
        return

    # Get Data
    try:
        bq_client = get_bq_client_with_drive_scope()
        rows = get_unimported_payloads(bq_client, args.ignore_log, args.settlement_id)
    except Exception as e:
        print(f"BigQuery Error: {e}")
        return
    
    if not rows:
        print("No settlements to process.")
        return
        
    print(f"Found {len(rows)} settlements.")
    
    for row in rows:
        print(f"\n--- Settlement {row.settlement_id} ({row.issue_date}) ---")
        details = json.loads(row.details_json)
        
        # Display Summary
        total_debit = sum([d['amount'] for d in details if d['entry_side'] == 'debit'])
        credits = sum([d['amount'] for d in details if d['entry_side'] == 'credit'])
        print(f"  Lines: {len(details)}")
        print(f"  Debit: {total_debit:,} | Credit: {credits:,} | Diff: {total_debit - credits}")
        
        # Print lines for debug
        for d in details:
            print(f"   {d['entry_side'].upper():<6} {d['amount']:>10,} : {d.get('description','')} (AcctID: {d.get('account_item_id')})")
        
        if args.dry_run:
            print("  [Dry Run]")
            continue
            
        if not args.yes:
             if input("Post? [y/N]: ").lower() != 'y': continue
             
        res = post_journal(token, cid, row)
        if res:
            print(f"Success! ID: {res['manual_journal']['id']}")
            log_import(bq_client, row.settlement_id, res)

if __name__ == "__main__":
    main()
