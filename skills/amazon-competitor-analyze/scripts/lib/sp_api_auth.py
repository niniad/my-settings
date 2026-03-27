"""SP-API 認証モジュール（GCP Secret Manager経由）"""

import subprocess
import sys

import requests

sys.stdout.reconfigure(encoding="utf-8")

GCP_PROJECT = "main-project-477501"
SECRET_NAMES = ["SP_API_CLIENT_ID", "SP_API_CLIENT_SECRET", "SP_API_REFRESH_TOKEN"]
_GCLOUD = r"C:\Users\ninni\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"

_secrets_cache: dict[str, str] = {}
_access_token: str | None = None


def get_secret(name: str) -> str:
    if name in _secrets_cache:
        return _secrets_cache[name]
    result = subprocess.run(
        ["powershell.exe", "-Command",
         f'& "{_GCLOUD}" secrets versions access latest --secret={name} --project={GCP_PROJECT}'],
        capture_output=True, text=True, timeout=20,
        stdin=subprocess.DEVNULL,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Secret {name} 取得失敗: {result.stderr.strip()}")
    value = result.stdout.strip()
    _secrets_cache[name] = value
    return value


def ensure_auth() -> str:
    global _access_token
    if _access_token is None:
        creds = {name: get_secret(name) for name in SECRET_NAMES}
        resp = requests.post(
            "https://api.amazon.com/auth/o2/token",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={
                "grant_type": "refresh_token",
                "refresh_token": creds["SP_API_REFRESH_TOKEN"],
                "client_id": creds["SP_API_CLIENT_ID"],
                "client_secret": creds["SP_API_CLIENT_SECRET"],
            },
            timeout=30,
        )
        resp.raise_for_status()
        _access_token = resp.json()["access_token"]
    return _access_token
