"""Eagle への競合データ登録・管理モジュール（親ASIN単位）。

フォルダ構成:
  Amazon競合データ/
    {product_name}/           ← --product で指定（例: マザーズリュック）
      {parent_asin}/          ← 親ASIN単位
        catalog_YYYYMMDD.json
        reviews_YYYYMMDD.json
        aplus_YYYYMMDD.json
        {child_asin}_MAIN.jpg
        {child_asin}_PT01.jpg
        {parent_asin}_APLUS_01.jpg  ← A+画像（親ASIN単位）
"""

import sys
from pathlib import Path

import requests

sys.stdout.reconfigure(encoding="utf-8")

EAGLE_BASE_URL = "http://localhost:41595"
EAGLE_TIMEOUT = 5

_folder_cache: dict[str, str] = {}


def eagle_available() -> bool:
    """Eagle が起動していて API に応答するか確認"""
    try:
        resp = requests.get(f"{EAGLE_BASE_URL}/api/application/info", timeout=EAGLE_TIMEOUT)
        return resp.json().get("status") == "success"
    except Exception:
        return False


def _get(endpoint: str, params: dict | None = None) -> dict:
    url = f"{EAGLE_BASE_URL}{endpoint}"
    if params:
        import urllib.parse
        url += "?" + urllib.parse.urlencode(params)
    resp = requests.get(url, timeout=EAGLE_TIMEOUT)
    return resp.json()


def _post(endpoint: str, data: dict) -> dict:
    resp = requests.post(f"{EAGLE_BASE_URL}{endpoint}", json=data, timeout=EAGLE_TIMEOUT)
    return resp.json()


def _list_folders() -> list[dict]:
    result = _get("/api/folder/list")
    if result.get("status") != "success":
        raise RuntimeError(f"フォルダ一覧取得失敗: {result}")
    return result.get("data", [])


def _flatten_folders(folders: list[dict], out: list | None = None) -> list[dict]:
    if out is None:
        out = []
    for f in folders:
        out.append(f)
        _flatten_folders(f.get("children", []), out)
    return out


def _find_folder_by_name(name: str, parent_id: str | None = None) -> str | None:
    flat = _flatten_folders(_list_folders())
    if parent_id is None:
        for f in flat:
            if f.get("name") == name:
                return f["id"]
        return None
    for f in flat:
        if f.get("id") == parent_id:
            for child in f.get("children", []):
                if child.get("name") == name:
                    return child["id"]
            return None
    return None


def _get_or_create_folder(name: str, parent_id: str | None = None) -> str:
    folder_id = _find_folder_by_name(name, parent_id)
    if folder_id:
        return folder_id
    data: dict = {"folderName": name}
    if parent_id:
        data["parent"] = parent_id
    result = _post("/api/folder/create", data)
    if result.get("status") != "success":
        raise RuntimeError(f"フォルダ作成失敗: {result}")
    return result["data"]["id"]


def _get_parent_folder(product_name: str, parent_asin: str) -> str:
    """Amazon競合データ/{product_name}/{parent_asin}/ のフォルダIDを返す（なければ作成）"""
    cache_key = f"{product_name}/{parent_asin}"
    if cache_key in _folder_cache:
        return _folder_cache[cache_key]

    from .config import EAGLE_COMPETITOR_ROOT

    if "root" not in _folder_cache:
        _folder_cache["root"] = _get_or_create_folder(EAGLE_COMPETITOR_ROOT)

    product_key = f"product/{product_name}"
    if product_key not in _folder_cache:
        _folder_cache[product_key] = _get_or_create_folder(product_name, _folder_cache["root"])

    folder_id = _get_or_create_folder(parent_asin, _folder_cache[product_key])
    _folder_cache[cache_key] = folder_id
    return folder_id


def register_file(
    file_path: Path,
    parent_asin: str,
    product_name: str,
    tags: list[str],
    name: str | None = None,
    annotation: str = "",
) -> str | None:
    """ファイル（画像・JSON等）をEagleの親ASINフォルダに登録してeagle_item_idを返す"""
    folder_id = _get_parent_folder(product_name, parent_asin)
    item_name = name or file_path.stem

    data = {
        "path": str(file_path.resolve()),
        "name": item_name,
        "tags": tags,
        "annotation": annotation,
        "folderId": folder_id,
    }
    result = _post("/api/item/addFromPath", data)
    if result.get("status") != "success":
        print(f"  Eagle登録失敗 ({item_name}): {result}", file=sys.stderr)
        return None

    raw = result.get("data")
    eagle_id = raw if isinstance(raw, str) else (raw or {}).get("id", "")
    print(f"  Eagle: {item_name}", file=sys.stderr)
    return eagle_id


def download_and_register(
    url: str,
    parent_asin: str,
    variant: str,
    product_name: str,
    tmp_dir: Path,
    child_asin: str | None = None,
    extra_tags: list[str] | None = None,
) -> dict:
    """URLから画像をダウンロードし、Eagleに登録してメタデータを返す。

    child_asin が None の場合（A+画像など親ASIN単位のもの）は parent_asin をファイル名に使用。
    ファイル名: {child_asin or parent_asin}_{variant}.jpg
    """
    from datetime import datetime

    child = child_asin or parent_asin
    ext = ".png" if ".png" in url.lower() else ".jpg"
    tmp_file = tmp_dir / f"{child}_{variant}{ext}"

    try:
        resp = requests.get(url, timeout=30, stream=True)
        resp.raise_for_status()
        with open(tmp_file, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
    except Exception as e:
        print(f"  画像DL失敗 ({child}/{variant}): {e}", file=sys.stderr)
        return {"child_asin": child, "variant": variant, "url": url, "eagle_id": None, "error": str(e)}

    captured = datetime.now().strftime("%Y%m")
    tags = [
        "type:image",
        f"parent_asin:{parent_asin}",
        f"child_asin:{child}",
        f"variant:{variant}",
        f"captured:{captured}",
    ] + (extra_tags or [])

    eagle_id = register_file(
        file_path=tmp_file,
        parent_asin=parent_asin,
        product_name=product_name,
        tags=tags,
        name=f"{child}_{variant}",
        annotation=url,
    )

    return {"child_asin": child, "variant": variant, "url": url, "eagle_id": eagle_id}


def list_parent_items(
    product_name: str,
    parent_asin: str,
    data_type: str | None = None,
) -> list[dict]:
    """
    Eagle から親ASINフォルダのアイテム一覧を取得してファイルパスを解決する。

    Args:
        data_type: "image" / "catalog" / "reviews" / "aplus" / None（全件）

    Returns:
        [{"item_id", "name", "ext", "tags", "file_path"}, ...]
    """
    folder_id = _get_parent_folder(product_name, parent_asin)
    result = _get("/api/item/list", {"folders": folder_id, "limit": 200})
    items = result.get("data", [])

    lib_result = _get("/api/library/info")
    lib_path = Path(lib_result.get("data", {}).get("library", {}).get("path", ""))

    out = []
    for item in items:
        item_id = item.get("id", "")
        name = item.get("name", "")
        ext = item.get("ext", "")
        tags = item.get("tags", [])

        if data_type:
            item_type = next((t.replace("type:", "") for t in tags if t.startswith("type:")), "")
            if item_type != data_type:
                continue

        file_path = lib_path / "images" / f"{item_id}.info" / f"{name}.{ext}"
        out.append({
            "item_id": item_id,
            "name": name,
            "ext": ext,
            "tags": tags,
            "file_path": str(file_path) if file_path.exists() else None,
        })

    return out
