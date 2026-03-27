# /// script
# requires-python = ">=3.12"
# dependencies = ["requests>=2.31.0"]
# ///
"""SP-API Catalog Items — 競合ASIN商品情報・BSR・画像・バリエーション取得（親ASIN単位）。

使い方:
  uv run fetch_catalog.py --asins B091NQ5WXY B0FB8Z8RZV --product マザーズリュック

  --asins に親ASIN・子ASINどちらを渡しても自動的に親ASINに解決して取得する。
  同じ親を持つ複数子ASINを渡した場合は1回だけ取得する（重複スキップ）。

出力:
  Eagle: Amazon競合データ/{product}/{親ASIN}/ に catalog JSON + 全バリエーション画像を登録
  （JSONはtmpに書いてEagle登録後に削除）
"""

import argparse
import json
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

sys.stdout.reconfigure(encoding="utf-8")

_SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(_SCRIPT_DIR))

from lib.config import (
    CATALOG_INCLUDED_DATA,
    CATALOG_SLEEP_SEC,
    IMAGE_VARIANTS,
    INDEX_FILE,
    MARKETPLACE_ID,
    SP_API_ENDPOINT,
)
from lib.eagle_integration import download_and_register, eagle_available, register_file
from lib.sp_api_auth import ensure_auth


# ============================================================
# インデックス管理
# ============================================================

def _load_index() -> dict:
    if INDEX_FILE.exists():
        return json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    return {}


def _save_index(index: dict) -> None:
    INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    INDEX_FILE.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")


def _update_index(parent_asin: str, field: str, value: str) -> None:
    index = _load_index()
    if parent_asin not in index:
        index[parent_asin] = {}
    index[parent_asin][field] = value
    _save_index(index)


# ============================================================
# SP-API 取得
# ============================================================

def _fetch_catalog_item(asin: str) -> dict | None:
    token = ensure_auth()
    url = f"{SP_API_ENDPOINT}/catalog/2022-04-01/items/{asin}"
    params = {
        "marketplaceIds": MARKETPLACE_ID,
        "includedData": ",".join(CATALOG_INCLUDED_DATA),
    }
    headers = {"x-amz-access-token": token, "Accept": "application/json"}

    resp = requests.get(url, headers=headers, params=params, timeout=30)
    if resp.status_code == 404:
        return None

    for attempt in range(3):
        if resp.status_code not in (429, 503):
            break
        wait = 2 ** (attempt + 1)
        print(f"  [{asin}] {resp.status_code} → {wait}秒後にリトライ", file=sys.stderr)
        time.sleep(wait)
        resp = requests.get(url, headers=headers, params=params, timeout=30)

    resp.raise_for_status()
    return resp.json()


# ============================================================
# パース関数
# ============================================================

def _extract_summaries(item: dict) -> dict:
    summaries = item.get("summaries", [{}])
    s = summaries[0] if summaries else {}
    return {
        "title": s.get("itemName", ""),
        "brand": s.get("brandName", ""),
        "color": s.get("color", ""),
        "item_classification": s.get("itemClassification", ""),
    }


def _extract_bullets(attrs: dict) -> list[str]:
    return [b["value"] for b in attrs.get("bullet_point", [])
            if b.get("language_tag", "").startswith("ja")]


def _extract_weight(attrs: dict) -> str | None:
    w = attrs.get("item_weight", [])
    return f"{w[0].get('value')} {w[0].get('unit')}" if w else None


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


def _extract_images(item: dict) -> list[dict]:
    """MAIN + PT01-08 の最大解像度URLを抽出（SWATCH/VEGR等は除外）"""
    images_data = item.get("images", [])
    result = []
    for img_group in images_data:
        for img in img_group.get("images", []):
            variant = img.get("variant", "")
            if variant not in IMAGE_VARIANTS:
                continue
            links = img.get("images", [])
            if not links:
                continue
            best = max(links, key=lambda x: x.get("width", 0) * x.get("height", 0))
            result.append({
                "variant": variant,
                "url": best.get("link", ""),
                "width": best.get("width", 0),
                "height": best.get("height", 0),
            })
    return result


def _extract_sales_ranks(item: dict) -> list[dict]:
    """カテゴリ別BSRを抽出"""
    ranks_data = item.get("salesRanks", [])
    result = []
    for group in ranks_data:
        for rank in group.get("ranks", []):
            result.append({
                "category": rank.get("title", ""),
                "link": rank.get("link", ""),
                "rank": rank.get("value", 0),
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            })
    return result


def _extract_relationships(item: dict) -> dict:
    """親ASIN + 子ASINリスト + バリエーション属性名を抽出"""
    rels = item.get("relationships", [])
    parent_asin = None
    child_asins = []
    variation_attrs = []

    for group in rels:
        for rel in group.get("relationships", []):
            rel_type = rel.get("type", "")
            if rel_type == "VARIATION":
                child_asins.append(rel.get("childAsin", ""))
                va = rel.get("variationTheme", {}).get("attributes", [])
                if va and not variation_attrs:
                    variation_attrs = va
            elif rel_type == "VARIATION_PARENT":
                parent_asin = rel.get("parentAsin", "")

    return {
        "parent_asin": parent_asin,
        "child_asins": [a for a in child_asins if a],
        "variation_attributes": variation_attrs,
    }


def _extract_classifications(item: dict) -> list[dict]:
    """カテゴリツリーを抽出"""
    cls_data = item.get("classifications", [])
    result = []
    for group in cls_data:
        for cls in group.get("classifications", []):
            result.append({
                "id": cls.get("classificationId", ""),
                "name": cls.get("displayName", ""),
            })
    return result


def _extract_variation_values(child_raw_attrs: dict, variation_attr_names: list[str]) -> dict:
    """子ASINのattributesからバリエーション値（色・サイズ等）を抽出"""
    values = {}
    for attr_name in variation_attr_names:
        vals = child_raw_attrs.get(attr_name, [])
        if vals:
            ja_val = next(
                (v.get("value") for v in vals if v.get("language_tag", "").startswith("ja")),
                None,
            )
            values[attr_name] = ja_val or (vals[0].get("value", "") if vals else "")
    return values


def _build_structured(asin: str, raw: dict) -> dict:
    attrs = raw.get("attributes", {})
    return {
        "asin": asin,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "summaries": _extract_summaries(raw),
        "bullets": _extract_bullets(attrs),
        "weight": _extract_weight(attrs),
        "dimensions": _extract_dimensions(attrs),
        "material": [m["value"] for m in attrs.get("material", [])
                     if m.get("language_tag", "").startswith("ja")],
        "water_resistance": [w["value"] for w in attrs.get("water_resistance_level", [])],
        "capacity": [c["value"] for c in attrs.get("capacity", [])],
        "images": _extract_images(raw),
        "sales_ranks": _extract_sales_ranks(raw),
        "relationships": _extract_relationships(raw),
        "classifications": _extract_classifications(raw),
        "_raw": raw,
    }


# ============================================================
# 親ASIN解決・統合カタログ構築
# ============================================================

def _resolve_to_parent(asin: str) -> tuple[str, dict]:
    """ASINを受け取り (parent_asin, parent_raw) を返す。子ASINなら親を自動検索。"""
    raw = _fetch_catalog_item(asin)
    if raw is None:
        raise ValueError(f"ASIN {asin} not found (404)")

    rels = _extract_relationships(raw)
    parent_asin = rels.get("parent_asin")

    if parent_asin:
        print(f"  {asin} は子ASIN → 親 {parent_asin} を取得中...", file=sys.stderr)
        time.sleep(CATALOG_SLEEP_SEC)
        parent_raw = _fetch_catalog_item(parent_asin)
        if parent_raw is None:
            raise ValueError(f"親ASIN {parent_asin} not found")
        return parent_asin, parent_raw

    return asin, raw


def _build_parent_catalog(
    parent_asin: str,
    parent_data: dict,
    children_data: list[dict],
) -> dict:
    """親ASIN単位の統合カタログJSONを構築する"""
    variation_attr_names = parent_data["relationships"].get("variation_attributes", [])

    children = {}
    for child in children_data:
        child_asin = child["asin"]
        child_raw_attrs = child.get("_raw", {}).get("attributes", {})
        children[child_asin] = {
            "variation_values": _extract_variation_values(child_raw_attrs, variation_attr_names),
            "images": child["images"],
        }

    return {
        "parent_asin": parent_asin,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "title": parent_data["summaries"]["title"],
        "brand": parent_data["summaries"]["brand"],
        "bullets": parent_data["bullets"],
        "sales_ranks": parent_data["sales_ranks"],
        "classifications": parent_data["classifications"],
        "variation_attributes": variation_attr_names,
        "child_asins": list(children.keys()),
        "children": children,
        "_raw_parent": parent_data.get("_raw", {}),
    }


# ============================================================
# 保存・Eagle登録
# ============================================================

def _save_catalog(parent_asin: str, catalog: dict, tmp_dir: Path) -> Path:
    date_str = datetime.now().strftime("%Y%m%d")
    out_path = tmp_dir / f"catalog_{date_str}.json"
    out_path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path


def _register_catalog_eagle(
    file_path: Path, parent_asin: str, product_name: str, catalog: dict
) -> str | None:
    """カタログJSONをEagleの親ASINフォルダに登録"""
    if not eagle_available():
        return None

    from datetime import datetime as dt
    captured = dt.now().strftime("%Y%m")
    bsr = catalog["sales_ranks"][0]["rank"] if catalog["sales_ranks"] else 0
    node = catalog["classifications"][0]["name"] if catalog["classifications"] else ""
    brand = catalog.get("brand", "")

    tags = ["type:catalog", f"parent_asin:{parent_asin}", f"captured:{captured}"]
    if brand:
        tags.append(f"brand:{brand}")
    if bsr:
        tags.append(f"bsr:{bsr}")
    if node:
        tags.append(f"node:{node}")

    return register_file(
        file_path=file_path,
        parent_asin=parent_asin,
        product_name=product_name,
        tags=tags,
        name=file_path.name,
        annotation=f"BSR:{bsr} | {catalog.get('title', '')[:60]}",
    )


def _download_all_images(
    children_data: list[dict], parent_asin: str, product_name: str
) -> list[dict]:
    """全子ASINの画像をダウンロードしてEagleに登録"""
    if not eagle_available():
        print("  Eagle未起動: 画像登録スキップ", file=sys.stderr)
        return []

    results = []
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        for child_data in children_data:
            child_asin = child_data["asin"]
            for img in child_data["images"]:
                result = download_and_register(
                    url=img["url"],
                    parent_asin=parent_asin,
                    variant=img["variant"],
                    product_name=product_name,
                    tmp_dir=tmp,
                    child_asin=child_asin,
                )
                results.append(result)
        time.sleep(2)  # Eagle が非同期コピーを完了するまで待機

    return results


# ============================================================
# コマンド実装
# ============================================================

def cmd_fetch(args) -> dict:
    input_asins = list(args.asins)
    product_name = args.product or "unknown"
    results: dict = {"success": [], "failed": []}
    processed_parents: set[str] = set()

    for asin in input_asins:
        print(f"\n[{asin}] 処理中...", file=sys.stderr)
        try:
            # 1. 親ASINに解決
            parent_asin, parent_raw = _resolve_to_parent(asin)

            if parent_asin in processed_parents:
                print(f"  スキップ: 親ASIN {parent_asin} は処理済み", file=sys.stderr)
                continue
            processed_parents.add(parent_asin)

            # 2. 親データ構築
            parent_data = _build_structured(parent_asin, parent_raw)
            child_asins = parent_data["relationships"]["child_asins"]
            print(
                f"  親ASIN: {parent_asin} | "
                f"子ASIN数: {len(child_asins)} | "
                f"BSR: {parent_data['sales_ranks'][0]['rank'] if parent_data['sales_ranks'] else 'N/A'}",
                file=sys.stderr,
            )

            # 3. 子ASIN取得
            children_data = []
            for j, child_asin in enumerate(child_asins):
                print(f"  子ASIN [{j+1}/{len(child_asins)}] {child_asin} ...", file=sys.stderr)
                time.sleep(CATALOG_SLEEP_SEC)
                child_raw = _fetch_catalog_item(child_asin)
                if child_raw:
                    children_data.append(_build_structured(child_asin, child_raw))
                else:
                    print(f"  ✗ {child_asin} not found", file=sys.stderr)

            # 4. 親中心カタログ構築・Eagle登録（tmp→Eagle→削除）
            catalog = _build_parent_catalog(parent_asin, parent_data, children_data)
            with tempfile.TemporaryDirectory() as tmp_dir:
                out_path = _save_catalog(parent_asin, catalog, Path(tmp_dir))
                _register_catalog_eagle(out_path, parent_asin, product_name, catalog)

            # 5. Eagle登録: 全子ASIN画像
            image_results = _download_all_images(children_data, parent_asin, product_name)

            _update_index(parent_asin, "last_catalog", datetime.now().strftime("%Y-%m-%d"))

            bsr_top = catalog["sales_ranks"][0]["rank"] if catalog["sales_ranks"] else "N/A"
            print(
                f"  ✓ {parent_asin} ({catalog.get('title', '')[:30]}) "
                f"子ASIN:{len(children_data)} 画像:{len(image_results)}枚",
                file=sys.stderr,
            )
            results["success"].append({
                "parent_asin": parent_asin,
                "input_asin": asin,
                "bsr": bsr_top,
                "child_count": len(children_data),
                "image_count": len(image_results),
            })

        except Exception as e:
            print(f"  ✗ {asin}: {e}", file=sys.stderr)
            results["failed"].append({"asin": asin, "error": str(e)})

        time.sleep(CATALOG_SLEEP_SEC)

    print(
        f"\n完了: {len(results['success'])}成功 / {len(results['failed'])}失敗",
        file=sys.stderr,
    )
    return results


# ============================================================
# CLI
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="SP-API Catalog Items 取得（親ASIN単位）")
    parser.add_argument("--asins", nargs="+", required=True,
                        help="ASINリスト（親・子どちらでも可。同じ親を持つ複数子ASINは1回のみ取得）")
    parser.add_argument("--product", required=True,
                        help="Eagleフォルダ名（例: マザーズリュック）")

    args = parser.parse_args()

    try:
        result = cmd_fetch(args)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
