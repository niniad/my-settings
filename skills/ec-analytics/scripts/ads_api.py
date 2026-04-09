# /// script
# requires-python = ">=3.12"
# dependencies = ["requests>=2.31.0"]
# ///
"""Amazon Ads API CLI — SP キャンペーン管理ツール。

使い方:
  uv run ads_api.py list_campaigns [--state ENABLED|PAUSED|ARCHIVED]
  uv run ads_api.py list_ad_groups --campaign-id <id>
  uv run ads_api.py list_keywords --campaign-id <id>
  uv run ads_api.py list_targets --campaign-id <id>
  uv run ads_api.py list_product_ads --campaign-id <id>
  uv run ads_api.py update_campaign_state --campaign-id <id> --state ENABLED|PAUSED
  uv run ads_api.py update_campaign_budget --campaign-id <id> --budget <amount>
  uv run ads_api.py update_keyword_bid --keyword-id <id> --bid <amount>
  uv run ads_api.py update_keyword_state --keyword-id <id> --state ENABLED|PAUSED
  uv run ads_api.py update_target_bid --target-id <id> --bid <amount>
  uv run ads_api.py update_target_state --target-id <id> --state ENABLED|PAUSED

出力: JSON（stdout）
"""

import sys
sys.stdout.reconfigure(encoding="utf-8")

import argparse
import json
import subprocess

import requests

# ============================================================
# 設定
# ============================================================

GCP_PROJECT = "main-project-477501"
SECRET_NAMES = [
    "AMAZON_ADS_CLIENT_ID",
    "AMAZON_ADS_CLIENT_SECRET",
    "AMAZON_ADS_REFRESH_TOKEN",
    "AMAZON_ADS_PROFILE_ID",
]
_GCLOUD = r"C:\Users\ninni\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"

BASE_URL = "https://advertising-api-fe.amazon.com"
MAX_BID_JPY = 5000.0
MAX_BUDGET_JPY = 100_000.0

RESOURCE_CONFIG = {
    "campaigns":  {"list": "/sp/campaigns/list",  "update": "/sp/campaigns",  "vnd": "spCampaign.v3"},
    "adGroups":   {"list": "/sp/adGroups/list",   "update": "/sp/adGroups",   "vnd": "spAdGroup.v3"},
    "productAds": {"list": "/sp/productAds/list", "update": "/sp/productAds", "vnd": "spProductAd.v3"},
    "keywords":   {"list": "/sp/keywords/list",   "update": "/sp/keywords",   "vnd": "spKeyword.v3"},
    "targets":    {"list": "/sp/targets/list",    "update": "/sp/targets",    "vnd": "spTargetingClause.v3"},
}

# ============================================================
# 認証（gcloud CLI 経由 — stdin=DEVNULL で MCP ストリーム汚染を防ぐ）
# ============================================================

_secrets_cache: dict[str, str] = {}
_access_token: str | None = None
_profile_id: str | None = None
_client_id: str | None = None


def _get_secret(name: str) -> str:
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


def _ensure_auth() -> tuple[str, str, str]:
    global _access_token, _profile_id, _client_id
    if _access_token is None:
        creds = {name: _get_secret(name) for name in SECRET_NAMES}
        resp = requests.post(
            "https://api.amazon.co.jp/auth/o2/token",
            data={
                "grant_type": "refresh_token",
                "refresh_token": creds["AMAZON_ADS_REFRESH_TOKEN"],
                "client_id": creds["AMAZON_ADS_CLIENT_ID"],
                "client_secret": creds["AMAZON_ADS_CLIENT_SECRET"],
            },
            timeout=30,
        )
        resp.raise_for_status()
        _access_token = resp.json()["access_token"]
        _client_id = creds["AMAZON_ADS_CLIENT_ID"]
        _profile_id = creds["AMAZON_ADS_PROFILE_ID"]
    return _access_token, _client_id, _profile_id


def _headers(resource: str) -> dict:
    token, client_id, profile_id = _ensure_auth()
    mime = f"application/vnd.{RESOURCE_CONFIG[resource]['vnd']}+json"
    return {
        "Authorization": f"Bearer {token}",
        "Amazon-Advertising-API-ClientId": client_id,
        "Amazon-Advertising-API-Scope": profile_id,
        "Accept": mime,
        "Content-Type": mime,
    }


# ============================================================
# API 操作
# ============================================================

def _list(resource: str, body: dict | None = None, max_results: int = 100) -> list[dict]:
    cfg = RESOURCE_CONFIG[resource]
    request_body: dict = {"maxResults": max_results}
    if body:
        request_body.update(body)
    resp = requests.post(
        f"{BASE_URL}{cfg['list']}", headers=_headers(resource), json=request_body, timeout=30
    )
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, list):
        return data
    for key in [resource, resource.lower(), "results"]:
        if key in data:
            return data[key]
    return [data]


def _update(resource: str, updates: list[dict]) -> list[dict]:
    cfg = RESOURCE_CONFIG[resource]
    resp = requests.put(
        f"{BASE_URL}{cfg['update']}", headers=_headers(resource), json={resource: updates}, timeout=30
    )
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, list):
        return data
    for key in [resource, "results", "responses"]:
        if key in data:
            return data[key]
    return [data]


# ============================================================
# コマンド実装
# ============================================================

def cmd_list_campaigns(args) -> dict:
    body = {}
    if args.state:
        body["stateFilter"] = {"include": [args.state]}
    return {"campaigns": _list("campaigns", body)}


def cmd_list_ad_groups(args) -> dict:
    body = {"campaignIdFilter": {"include": [args.campaign_id]}}
    return {"adGroups": _list("adGroups", body)}


def cmd_list_keywords(args) -> dict:
    body = {"campaignIdFilter": {"include": [args.campaign_id]}}
    return {"keywords": _list("keywords", body)}


def cmd_list_targets(args) -> dict:
    body = {"campaignIdFilter": {"include": [args.campaign_id]}}
    return {"targets": _list("targets", body)}


def cmd_list_product_ads(args) -> dict:
    body = {"campaignIdFilter": {"include": [args.campaign_id]}}
    return {"productAds": _list("productAds", body)}


def cmd_update_campaign_state(args) -> dict:
    result = _update("campaigns", [{"campaignId": int(args.campaign_id), "state": args.state}])
    return {"updated": result}


def cmd_update_campaign_budget(args) -> dict:
    budget = float(args.budget)
    if budget <= 0 or budget > MAX_BUDGET_JPY:
        return {"error": f"予算は 0〜{MAX_BUDGET_JPY} 円で指定してください"}
    result = _update("campaigns", [{"campaignId": int(args.campaign_id),
                                    "budget": {"budget": budget, "budgetType": "DAILY"}}])
    return {"updated": result}


def cmd_update_keyword_bid(args) -> dict:
    bid = float(args.bid)
    if bid <= 0 or bid > MAX_BID_JPY:
        return {"error": f"入札額は 0〜{MAX_BID_JPY} 円で指定してください"}
    result = _update("keywords", [{"keywordId": int(args.keyword_id), "bid": {"value": bid, "bidType": "FIXED_AMOUNT"}}])
    return {"updated": result}


def cmd_update_keyword_state(args) -> dict:
    result = _update("keywords", [{"keywordId": int(args.keyword_id), "state": args.state}])
    return {"updated": result}


def cmd_update_target_bid(args) -> dict:
    bid = float(args.bid)
    if bid <= 0 or bid > MAX_BID_JPY:
        return {"error": f"入札額は 0〜{MAX_BID_JPY} 円で指定してください"}
    result = _update("targets", [{"targetId": int(args.target_id), "bid": bid}])
    return {"updated": result}


def cmd_update_target_state(args) -> dict:
    result = _update("targets", [{"targetId": int(args.target_id), "state": args.state}])
    return {"updated": result}


# ============================================================
# CLI
# ============================================================

COMMANDS = {
    "list_campaigns": cmd_list_campaigns,
    "list_ad_groups": cmd_list_ad_groups,
    "list_keywords": cmd_list_keywords,
    "list_targets": cmd_list_targets,
    "list_product_ads": cmd_list_product_ads,
    "update_campaign_state": cmd_update_campaign_state,
    "update_campaign_budget": cmd_update_campaign_budget,
    "update_keyword_bid": cmd_update_keyword_bid,
    "update_keyword_state": cmd_update_keyword_state,
    "update_target_bid": cmd_update_target_bid,
    "update_target_state": cmd_update_target_state,
}


def main():
    parser = argparse.ArgumentParser(description="Amazon Ads API CLI")
    parser.add_argument("command", choices=COMMANDS.keys())
    parser.add_argument("--state", help="ENABLED / PAUSED / ARCHIVED")
    parser.add_argument("--campaign-id")
    parser.add_argument("--keyword-id")
    parser.add_argument("--target-id")
    parser.add_argument("--budget", type=float)
    parser.add_argument("--bid", type=float)
    args = parser.parse_args()

    try:
        result = COMMANDS[args.command](args)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
