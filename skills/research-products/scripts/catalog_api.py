# /// script
# requires-python = ">=3.12"
# dependencies = ["requests>=2.31.0"]
# ///
"""SP-API Catalog Items API — 競合ASIN情報取得ツール。

使い方:
  uv run catalog_api.py get_item --asin B091NQ5WXY
  uv run catalog_api.py get_items --asins B091NQ5WXY B0FB8Z8RZV B08HGB1P8W
  uv run catalog_api.py get_bullets --asin B091NQ5WXY        # 箇条書きのみ
  uv run catalog_api.py get_specs --asin B091NQ5WXY          # 重量・サイズ等

出力: JSON（stdout）
"""

import sys
sys.stdout.reconfigure(encoding="utf-8")

import argparse
import json
import subprocess
import time

import requests

# ============================================================
# 設定
# ============================================================

GCP_PROJECT = "main-project-477501"
SECRET_NAMES = ["SP_API_CLIENT_ID", "SP_API_CLIENT_SECRET", "SP_API_REFRESH_TOKEN"]
_GCLOUD = r"C:\Users\ninni\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"

SP_API_ENDPOINT = "https://sellingpartnerapi-fe.amazon.com"
MARKETPLACE_ID = "A1VC38T7YXB528"  # 日本
INCLUDED_DATA = ["summaries", "attributes", "dimensions", "identifiers"]

# ============================================================
# 認証（gcloud CLI 経由 — stdin=DEVNULL で MCP ストリーム汚染を防ぐ）
# ============================================================

_secrets_cache: dict[str, str] = {}
_access_token: str | None = None


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


def _ensure_auth() -> str:
    global _access_token
    if _access_token is None:
        creds = {name: _get_secret(name) for name in SECRET_NAMES}
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


def _fetch_catalog_item(asin: str) -> dict | None:
    token = _ensure_auth()
    url = f"{SP_API_ENDPOINT}/catalog/2022-04-01/items/{asin}"
    resp = requests.get(
        url,
        headers={"x-amz-access-token": token, "Accept": "application/json"},
        params={
            "marketplaceIds": MARKETPLACE_ID,
            "includedData": ",".join(INCLUDED_DATA),
        },
        timeout=30,
    )
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    return resp.json()


def _extract_bullets(attrs: dict) -> list[str]:
    return [b["value"] for b in attrs.get("bullet_point", [])
            if b.get("language_tag", "").startswith("ja")]


def _extract_weight(attrs: dict) -> str | None:
    w = attrs.get("item_weight", [])
    if w:
        return f"{w[0].get('value')} {w[0].get('unit')}"
    return None


def _extract_dimensions(attrs: dict) -> dict:
    dims = {}
    for key in ["item_dimensions", "item_package_dimensions"]:
        d = attrs.get(key, [])
        if d:
            dims[key] = d[0]
    capacity = attrs.get("capacity", [])
    if capacity:
        dims["capacity"] = capacity[0]
    return dims


def _extract_material(attrs: dict) -> list[str]:
    return [m["value"] for m in attrs.get("material", [])
            if m.get("language_tag", "").startswith("ja")]


# ============================================================
# コマンド実装
# ============================================================

def cmd_get_item(args) -> dict:
    data = _fetch_catalog_item(args.asin)
    if data is None:
        return {"error": f"ASIN {args.asin} not found"}
    return data


def cmd_get_items(args) -> dict:
    results = {}
    for i, asin in enumerate(args.asins):
        if i > 0:
            time.sleep(1.5)  # rate limit
        data = _fetch_catalog_item(asin)
        results[asin] = data or {"error": "not found"}
    return results


def cmd_get_bullets(args) -> dict:
    data = _fetch_catalog_item(args.asin)
    if data is None:
        return {"error": f"ASIN {args.asin} not found"}
    attrs = data.get("attributes", {})
    bullets = _extract_bullets(attrs)
    summaries = data.get("summaries", [{}])
    title = summaries[0].get("itemName", "") if summaries else ""
    return {
        "asin": args.asin,
        "title": title,
        "bullets": bullets,
        "weight": _extract_weight(attrs),
        "material": _extract_material(attrs),
    }


def cmd_get_specs(args) -> dict:
    data = _fetch_catalog_item(args.asin)
    if data is None:
        return {"error": f"ASIN {args.asin} not found"}
    attrs = data.get("attributes", {})
    summaries = data.get("summaries", [{}])
    title = summaries[0].get("itemName", "") if summaries else ""
    return {
        "asin": args.asin,
        "title": title,
        "bullets": _extract_bullets(attrs),
        "weight": _extract_weight(attrs),
        "dimensions": _extract_dimensions(attrs),
        "material": _extract_material(attrs),
        "water_resistance": [w["value"] for w in attrs.get("water_resistance_level", [])],
        "capacity": [c["value"] for c in attrs.get("capacity", [])],
    }


# ============================================================
# CLI
# ============================================================

COMMANDS = {
    "get_item": cmd_get_item,
    "get_items": cmd_get_items,
    "get_bullets": cmd_get_bullets,
    "get_specs": cmd_get_specs,
}


def main():
    parser = argparse.ArgumentParser(description="SP-API Catalog Items CLI")
    parser.add_argument("command", choices=COMMANDS.keys())
    parser.add_argument("--asin", help="単一ASIN")
    parser.add_argument("--asins", nargs="+", help="複数ASIN（スペース区切り）")
    args = parser.parse_args()

    try:
        result = COMMANDS[args.command](args)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
