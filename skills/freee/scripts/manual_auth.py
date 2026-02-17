
"""
Simple script to help user authorize freee API manually through the CLI.
This is used when the automated token refresh flow fails or needs initial setup.
"""
import os
import sys
sys.stdout.reconfigure(encoding="utf-8")
import requests
import urllib.parse
from google.cloud import secretmanager

# Add scripts directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from auth import _get_project_id

# Configuration
REDIRECT_URI = "urn:ietf:wg:oauth:2.0:oob"
AUTH_URL = "https://accounts.secure.freee.co.jp/public_api/authorize"
TOKEN_URL = "https://accounts.secure.freee.co.jp/public_api/token"

def get_secret(secret_name):
    client = secretmanager.SecretManagerServiceClient()
    project_id = _get_project_id()
    name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
    try:
        response = client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except:
        return None

def save_secret(secret_id, payload):
    client = secretmanager.SecretManagerServiceClient()
    project_id = _get_project_id()
    parent = f"projects/{project_id}/secrets/{secret_id}"
    payload_bytes = payload.encode("UTF-8")
    try:
        client.add_secret_version(
            request={"parent": parent, "payload": {"data": payload_bytes}}
        )
        print(f"Updated secret: {secret_id}")
    except Exception as e:
        print(f"Failed to update secret {secret_id}: {e}")

def main():
    print("--- freee API Manual Authorization Helper ---")
    
    # Try to load ID/Secret from Secret Manager
    client_id = get_secret("FREEE_CLIENT_ID")
    client_secret = get_secret("FREEE_CLIENT_SECRET")
    
    if not client_id or not client_secret:
        print("Could not find Client ID/Secret in Secret Manager.")
        client_id = input("Enter Client ID: ").strip()
        client_secret = input("Enter Client Secret: ").strip()
        
        save = input("Save these credentials to Secret Manager? (y/n): ").lower()
        if save == 'y':
            save_secret("FREEE_CLIENT_ID", client_id)
            save_secret("FREEE_CLIENT_SECRET", client_secret)
    else:
        print(f"Loaded Client ID: {client_id[:4]}... (from Secret Manager)")

    # 1. Generate Auth URL
    params = {
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "read_write" 
    }
    url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
    
    print("\n" + "="*60)
    print("1. Open the following URL in your browser:")
    print(url)
    print("="*60 + "\n")
    
    # 2. Get Code
    code = input("2. Enter the Authorization Code displayed after login: ").strip()
    
    # 3. Exchange
    data = {
        "grant_type": "authorization_code",
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": REDIRECT_URI
    }
    
    print("\nExchanging code for tokens...")
    res = requests.post(TOKEN_URL, data=data)
    
    if res.status_code == 200:
        tokens = res.json()
        access_token = tokens.get("access_token")
        refresh_token = tokens.get("refresh_token")
        
        print("\nSuccess!")
        print(f"Access Token: {access_token[:10]}...")
        
        # Save Refresh Token
        save_secret("FREEE_REFRESH_TOKEN", refresh_token)
        print("Refresh token saved to Secret Manager.")
    else:
        print("\nFailed!")
        print(res.text)

if __name__ == "__main__":
    main()
