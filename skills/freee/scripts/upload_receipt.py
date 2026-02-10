
"""
Script to upload a receipt/file to freee filebox.
"""
import requests
import json
import argparse
import os
from auth import get_access_token, get_company_id, get_headers, FREEE_API_BASE

def upload_receipt(file_path):
    token = get_access_token()
    cid = get_company_id(token)
    
    url = f"{FREEE_API_BASE}/receipts"
    # Special headers for multipart (requests handles boundary, but Auth is needed)
    headers = {"Authorization": f"Bearer {token}", "X-Api-Version": "2020-06-15"}
    
    print(f"Uploading {file_path}...")
    try:
        with open(file_path, 'rb') as f:
            files = {'receipt': (os.path.basename(file_path), f)}
            data = {'company_id': cid}
            res = requests.post(url, headers=headers, files=files, data=data)
            
            if res.status_code == 201:
                print("Success!")
                print(json.dumps(res.json(), indent=2, ensure_ascii=False))
            else:
                print(f"Failed: {res.status_code}")
                print(res.text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload receipt to freee.")
    parser.add_argument("file_path", help="Path to the file to upload")
    args = parser.parse_args()
    
    upload_receipt(args.file_path)
