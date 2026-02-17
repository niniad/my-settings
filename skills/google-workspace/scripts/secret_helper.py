"""
Google Workspace スキル用 Secret Manager ヘルパー

credentials.json / token.json の内容をSecret Managerから取得・保存する。
ローカル開発では gcloud auth application-default login が必要。
"""
import os
import json
from google.cloud import secretmanager


def _get_project_id():
    """GCPプロジェクトIDを取得"""
    project_id = os.environ.get("GCP_PROJECT_ID")
    if project_id:
        return project_id
    import google.auth
    _, project = google.auth.default()
    return project or "main-project-477501"


_sm_client = None


def _get_client():
    global _sm_client
    if _sm_client is None:
        _sm_client = secretmanager.SecretManagerServiceClient()
    return _sm_client


def get_secret(secret_name):
    """Secret Managerからシークレットを取得"""
    client = _get_client()
    project_id = _get_project_id()
    name = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")


def save_secret(secret_name, value):
    """Secret Managerにシークレットを保存（新しいバージョンを追加）"""
    client = _get_client()
    project_id = _get_project_id()
    parent = f"projects/{project_id}/secrets/{secret_name}"
    payload = value.encode("UTF-8")
    client.add_secret_version(
        request={"parent": parent, "payload": {"data": payload}}
    )


def get_credentials_info():
    """Secret Managerからcredentials.json相当の情報を取得"""
    raw = get_secret("GOOGLE_WORKSPACE_CREDENTIALS")
    return json.loads(raw)


def get_token_info():
    """Secret Managerからtoken.json相当の情報を取得"""
    raw = get_secret("GOOGLE_WORKSPACE_TOKEN")
    return json.loads(raw)


def save_token(creds_json_str):
    """token情報をSecret Managerに保存"""
    save_secret("GOOGLE_WORKSPACE_TOKEN", creds_json_str)
