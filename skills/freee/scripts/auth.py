
"""
Library to interact with freee API using GCP Secret Manager for credentials.
"""
import os
import requests
import json
import urllib.parse
from google.cloud import secretmanager

# --- Configuration ---
FREEE_API_BASE = "https://api.freee.co.jp/api/1"
TOKEN_URL = "https://accounts.secure.freee.co.jp/public_api/token"
# ---------------------


def _get_project_id():
    """GCPプロジェクトIDを取得"""
    project_id = os.environ.get("GCP_PROJECT_ID")
    if project_id:
        return project_id
    import google.auth
    _, project = google.auth.default()
    return project or "main-project-477501"


sm_client = secretmanager.SecretManagerServiceClient()

def get_secret(secret_name):
    """Retrieve a secret from GCP Secret Manager."""
    project_id = _get_project_id()
    name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
    try:
        response = sm_client.access_secret_version(request={"name": name})
        return response.payload.data.decode("UTF-8")
    except Exception as e:
        raise Exception(f"Failed to get secret {secret_name}: {e}")

def update_refresh_token(new_token):
    """Update the refresh token in Secret Manager."""
    project_id = _get_project_id()
    parent = f"projects/{project_id}/secrets/freee_refresh_token"
    payload = new_token.encode("UTF-8")
    sm_client.add_secret_version(
        request={"parent": parent, "payload": {"data": payload}}
    )

def get_access_token():
    """Get a valid access token, refreshing if necessary."""
    client_id = get_secret("freee_client_id")
    client_secret = get_secret("freee_client_secret")
    refresh_token = get_secret("freee_refresh_token")
    
    data = {
        "grant_type": "refresh_token",
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token
    }
    
    response = requests.post(TOKEN_URL, data=data)
    if response.status_code != 200:
        raise Exception(f"Failed to refresh token: {response.text}")
    
    tokens = response.json()
    if "refresh_token" in tokens:
        update_refresh_token(tokens["refresh_token"])
        
    return tokens["access_token"]

def get_headers(access_token):
    return {
        "Authorization": f"Bearer {access_token}",
        "X-Api-Version": "2020-06-15",
        "Content-Type": "application/json"
    }

def get_company_id(access_token):
    """Get the first available company ID."""
    url = f"{FREEE_API_BASE}/companies"
    res = requests.get(url, headers=get_headers(access_token))
    res.raise_for_status()
    companies = res.json().get("companies", [])
    if not companies:
        raise Exception("No companies found.")
    return companies[0]["id"]
