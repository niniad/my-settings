import os
import json
import time
import subprocess
from datetime import datetime
import requests
from google.cloud import bigquery
import sys

# Authentication
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from auth import get_access_token, get_company_id, get_headers, FREEE_API_BASE, _get_project_id

# Config
PROJECT_ID = _get_project_id()
DATASET_ID = "freee"
GCS_BUCKET = "gs://sp-api-bucket/freee"

# Define Sync Targets
TARGETS = {
    "account_items": {
        "endpoint": "account_items", 
        "resource_key": "account_items",
        "write_disposition": "WRITE_TRUNCATE"
    },
    "walletables": {
        "endpoint": "walletables", 
        "resource_key": "walletables",
        "write_disposition": "WRITE_TRUNCATE",
        "multi_type": True # Requires strict type param
    },
    "deals": {
        "endpoint": "deals", 
        "resource_key": "deals",
        "write_disposition": "WRITE_TRUNCATE", # Replace all (for now, to ensure consistency)
        "params": {"limit": 100}
    },
    "manual_journals": {
        "endpoint": "manual_journals", 
        "resource_key": "manual_journals",
        "write_disposition": "WRITE_TRUNCATE",
        "params": {"limit": 100}
    },
    "partners": {
        "endpoint": "partners",
        "resource_key": "partners",
        "write_disposition": "WRITE_TRUNCATE"
    },
    "items": {
        "endpoint": "items",
        "resource_key": "items",
        "write_disposition": "WRITE_TRUNCATE"
    },
    "sections": {
        "endpoint": "sections",
        "resource_key": "sections",
        "write_disposition": "WRITE_TRUNCATE"
    },
    "tags": {
        "endpoint": "tags",
        "resource_key": "tags",
        "write_disposition": "WRITE_TRUNCATE"
    },
    "taxes": {
        "endpoint": "taxes/companies/{company_id}", # Dynamic endpoint
        "resource_key": "taxes",
        "write_disposition": "WRITE_TRUNCATE",
        "use_company_id_in_url": True
    }
}

def fetch_list_resource(token, company_id, endpoint, resource_key, extra_params={}, use_company_id_in_url=False):
    if use_company_id_in_url:
        url = f"{FREEE_API_BASE}/{endpoint.format(company_id=company_id)}"
        # Taxes endpoint usually returns list directly or in a key? Check response.
        # Taxes response: { "taxes": [ ... ] }
    else:
        url = f"{FREEE_API_BASE}/{endpoint}"
        
    headers = get_headers(token)
    offset = 0
    limit = 100
    all_data = []
    
    print(f"Fetching {url} (params={extra_params})...")
    
    while True:
        params = {"company_id": company_id, "limit": limit, "offset": offset}
        params.update(extra_params)
        
        try:
            res = requests.get(url, headers=headers, params=params)
            if res.status_code == 401:
                print("Token expired?")
                res.raise_for_status()
            
            data = res.json()
            
            # Special handling for taxes which might not use offset/limit pagination in the same way?
            # Assuming standard pagination for now.
            
            items = data.get(resource_key, [])
                
            if not items:
                break
            
            # Detect full fetch ignoring limit
            if len(items) > limit:
                print(f"  Received {len(items)} items (limit={limit}). Assuming full fetch.")
                all_data.extend(items)
                break
                
            all_data.extend(items)
            print(f"  Fetched {len(items)} items (Total: {len(all_data)})...")
            
            if len(items) < limit:
                break
                
            offset += limit
            time.sleep(0.3) 
            
        except Exception as e:
            print(f"Error fetching {endpoint}: {e}")
            break
            
    return all_data

def save_jsonl(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        for item in data:
            # Add Metadata
            item['_fetched_at'] = datetime.utcnow().isoformat()
            f.write(json.dumps(item, ensure_ascii=False) + '\n')

def upload_to_gcs(local_file, remote_path):
    print(f"Uploading to {remote_path}...")
    # Use gsutil (assuming it's installed and authenticated)
    cmd = ['gsutil', 'cp', local_file, remote_path]
    subprocess.check_call(cmd, shell=True)

def load_to_bq(client, table_id, gcs_uri, write_disposition):
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        autodetect=True,
        write_disposition=write_disposition,
        ignore_unknown_values=True 
    )
    load_job = client.load_table_from_uri(gcs_uri, table_id, job_config=job_config)
    print(f"Starting BQ load job {load_job.job_id} for {table_id}...")
    load_job.result() # Wait for completion
    print(f"Job finished. Table {table_id} loaded.")

def main():
    try:
        token = get_access_token()
        cid = get_company_id(token)
    except Exception as e:
        print(f"Auth failed: {e}")
        return

    client = bigquery.Client(project=PROJECT_ID)
    
    for name, config in TARGETS.items():
        print(f"\n--- Syncing {name} ---")
        endpoint = config['endpoint']
        resource_key = config.get('resource_key', name)
        params = config.get("params", {})
        use_company_id_in_url = config.get("use_company_id_in_url", False)
        
        data = []
        if config.get("multi_type"):
            # Walletables must be fetched by type
            for w_type in ["bank_account", "credit_card", "wallet"]:
                p = params.copy()
                p["type"] = w_type
                # Note: walletables does not use dynamic URL, so False
                data.extend(fetch_list_resource(token, cid, endpoint, resource_key, p, False))
        else:
            data = fetch_list_resource(token, cid, endpoint, resource_key, params, use_company_id_in_url)
            
        if not data:
            print(f"No data found for {name}. Skipping BQ load.")
            # Even if no data, we might want to truncate table if it should be empty?
            # But safer to skip.
            continue
            
        # 1. Save Local JSONL
        filename = f"temp_{name}.jsonl"
        save_jsonl(data, filename)
        
        # 2. Upload to GCS
        gcs_uri = f"{GCS_BUCKET}/{name}.jsonl"
        try:
            upload_to_gcs(filename, gcs_uri)
        except Exception as e:
            print(f"GCS Upload failed: {e}")
            os.remove(filename)
            continue
        
        # 3. Load to BigQuery
        table_id = f"{PROJECT_ID}.{DATASET_ID}.{name}"
        try:
            load_to_bq(client, table_id, gcs_uri, config['write_disposition'])
        except Exception as e:
            print(f"BigQuery Load failed: {e}")
        
        # Cleanup
        if os.path.exists(filename):
            os.remove(filename)
    
    print("\nSync completed.")

if __name__ == "__main__":
    main()
