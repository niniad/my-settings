# /// script
# requires-python = ">=3.12"
# dependencies = ["requests>=2.31.0", "google-genai>=1.0.0"]
# ///
"""Eagle内の競合データ（JSON）を読み取り、ローカルにCSV参照用ファイルを生成する。

出力CSV:
  catalog.csv  — SP-API _raw_parent をフラット化。全商品仕様+BSR+データ有無フラグ
  reviews.csv  — 全レビュー（variation=バリエーション名。空欄あり）
  images.csv   — 商品画像URL + A+画像（eagle_path + section_text付き）

用語:
  child_asin: Eagleフォルダ名のASIN（fetch_catalog.pyに渡されたASIN）
  parent_asin: 真の親ASIN（_raw_parent.relationships から取得）
"""

import argparse
import csv
import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

import requests

EAGLE_BASE_URL = "http://localhost:41595"
EAGLE_TIMEOUT = 5


# --- Eagle API ---

def _eagle_get(endpoint: str, params: dict | None = None) -> dict:
    url = f"{EAGLE_BASE_URL}{endpoint}"
    if params:
        import urllib.parse
        url += "?" + urllib.parse.urlencode(params)
    return requests.get(url, timeout=EAGLE_TIMEOUT).json()


def _flatten_folders(folders: list[dict], out: list | None = None) -> list[dict]:
    if out is None:
        out = []
    for f in folders:
        out.append(f)
        _flatten_folders(f.get("children", []), out)
    return out


def _find_product_folder(product_name: str) -> str | None:
    result = _eagle_get("/api/folder/list")
    flat = _flatten_folders(result.get("data", []))
    root_id = None
    for f in flat:
        if f.get("name") == "Amazon競合データ":
            root_id = f["id"]
            break
    if not root_id:
        return None
    for f in flat:
        if f.get("id") == root_id:
            for child in f.get("children", []):
                if child.get("name") == product_name:
                    return child["id"]
    return None


def _find_asin_folders(product_folder_id: str) -> list[dict]:
    result = _eagle_get("/api/folder/list")
    flat = _flatten_folders(result.get("data", []))
    for f in flat:
        if f.get("id") == product_folder_id:
            return [
                {"id": c["id"], "name": c["name"]}
                for c in f.get("children", [])
                if re.match(r"^B[0-9A-Z]{9}$", c.get("name", ""))
            ]
    return []


def _get_library_path() -> Path:
    result = _eagle_get("/api/library/info")
    return Path(result.get("data", {}).get("library", {}).get("path", ""))


def _list_folder_items(folder_id: str, lib_path: Path) -> list[dict]:
    result = _eagle_get("/api/item/list", {"folders": folder_id, "limit": 200})
    items = result.get("data", [])
    out = []
    for item in items:
        item_id = item.get("id", "")
        name = item.get("name", "")
        ext = item.get("ext", "")
        tags = item.get("tags", [])
        file_path = lib_path / "images" / f"{item_id}.info" / f"{name}.{ext}"
        out.append({
            "item_id": item_id, "name": name, "ext": ext, "tags": tags,
            "file_path": file_path if file_path.exists() else None,
        })
    return out


def _tag_value(tags: list[str], key: str) -> str:
    prefix = f"{key}:"
    for t in tags:
        if t.startswith(prefix):
            return t[len(prefix):]
    return ""


def _read_json(path: Path) -> dict | None:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"  JSON読み込み失敗: {path} ({e})", file=sys.stderr)
        return None


def _get_latest(items: list[dict], data_type: str) -> dict | None:
    typed = [i for i in items if _tag_value(i["tags"], "type") == data_type and i["file_path"]]
    if not typed:
        return None
    typed.sort(key=lambda x: x["name"], reverse=True)
    return _read_json(typed[0]["file_path"])


def _resolve_parent_asin(data: dict) -> str:
    raw = data.get("_raw_parent", {})
    relationships = raw.get("relationships", [])
    if relationships:
        rels = relationships[0].get("relationships", [])
        if rels:
            parents = rels[0].get("parentAsins", [])
            if parents:
                return parents[0]
    return ""


# --- 画像テキスト抽出（Gemini Vision） ---

def _get_gemini_api_key() -> str:
    import subprocess
    result = subprocess.run(
        ["powershell.exe", "-Command",
         "gcloud secrets versions access latest --secret=GEMINI_API_KEY --project=main-project-477501"],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"GEMINI_API_KEY取得失敗: {result.stderr}")
    return result.stdout.strip()


def _extract_text_from_url(url: str, genai_client) -> str:
    """画像URLからテキストを抽出する（Gemini Vision）"""
    from google.genai import types
    try:
        resp = genai_client.models.generate_content(
            model="gemini-3.1-flash-lite-preview",
            contents=[
                types.Part.from_uri(file_uri=url, mime_type="image/jpeg"),
                "この商品画像内に表示されている日本語・英語のテキストをすべて抽出してください。"
                "テキストが無い場合は「テキストなし」と返してください。"
                "抽出したテキストのみを返し、説明は不要です。",
            ],
        )
        text = resp.text.strip() if resp.text else ""
        return "" if text == "テキストなし" else text
    except Exception as e:
        print(f"  テキスト抽出失敗: {url[:60]}... ({e})", file=sys.stderr)
        return ""


def _build_asin_parent_map(all_items: dict[str, list[dict]]) -> dict[str, str]:
    mapping = {}
    for eagle_asin, items in all_items.items():
        data = _get_latest(items, "catalog")
        mapping[eagle_asin] = _resolve_parent_asin(data) if data else ""
    return mapping


# --- catalog.csv ---

def _flatten_raw_parent(eagle_asin: str, parent_asin: str, data: dict,
                        has_reviews: bool, has_aplus: bool) -> dict:
    raw = data.get("_raw_parent", {})
    row: dict[str, str] = {
        "child_asin": eagle_asin,
        "parent_asin": parent_asin,
    }

    row["fetched_at"] = data.get("fetched_at", "")[:10]

    summaries = raw.get("summaries", [])
    if summaries:
        s = summaries[0]
        for key in ["brand", "color", "size", "style", "itemName", "manufacturer",
                     "modelNumber", "partNumber", "itemClassification",
                     "websiteDisplayGroupName"]:
            val = s.get(key)
            if val:
                row[key] = str(val)
        bc = s.get("browseClassification", {})
        if bc:
            row["browse_classification"] = bc.get("displayName", "")

    row["title"] = data.get("title", "") or (summaries[0].get("itemName", "") if summaries else "")
    bullets = data.get("bullets", [])
    for i, b in enumerate(bullets, 1):
        row[f"bullet_{i}"] = b

    sales_ranks = raw.get("salesRanks", [])
    for sr_market in sales_ranks:
        for j, cr in enumerate(sr_market.get("classificationRanks", []), 1):
            row[f"bsr_rank_{j}"] = str(cr.get("rank", ""))
            row[f"bsr_category_{j}"] = cr.get("title", "")
        for j, dr in enumerate(sr_market.get("displayGroupRanks", []), 1):
            row[f"bsr_display_rank_{j}"] = str(dr.get("rank", ""))
            row[f"bsr_display_group_{j}"] = dr.get("title", "")

    classifications = raw.get("classifications", [])
    for cl_market in classifications:
        for k, cl in enumerate(cl_market.get("classifications", []), 1):
            row[f"classification_{k}"] = cl.get("displayName", "")

    dimensions = raw.get("dimensions", [])
    if dimensions:
        d = dimensions[0]
        for prefix, dims in [("item", d.get("item", {})), ("pkg", d.get("package", {}))]:
            for dim_key in ["height", "length", "width", "weight"]:
                dim = dims.get(dim_key, {})
                if dim:
                    val = dim.get("value")
                    unit = dim.get("unit", "")
                    if val is not None:
                        row[f"{prefix}_{dim_key}"] = f"{val} {unit}".strip()

    relationships = raw.get("relationships", [])
    if relationships:
        rels = relationships[0].get("relationships", [])
        if rels:
            theme = rels[0].get("variationTheme", {})
            row["variation_theme"] = theme.get("theme", "")
            row["variation_attrs"] = ", ".join(theme.get("attributes", []))

    images_markets = raw.get("images", [])
    if images_markets:
        row["image_count"] = str(len(images_markets[0].get("images", [])))

    row["has_reviews"] = "Y" if has_reviews else "N"
    row["has_aplus"] = "Y" if has_aplus else "N"

    return row


def build_catalog_csv(all_items: dict[str, list[dict]], asin_map: dict[str, str], output_dir: Path):
    rows = []
    for eagle_asin, items in all_items.items():
        data = _get_latest(items, "catalog")
        if not data:
            continue
        has_reviews = any(_tag_value(i["tags"], "type") == "reviews" and i["file_path"] for i in items)
        has_aplus = any(_tag_value(i["tags"], "type") == "aplus" and i["file_path"] for i in items)
        rows.append(_flatten_raw_parent(eagle_asin, asin_map.get(eagle_asin, ""), data,
                                        has_reviews, has_aplus))

    if not rows:
        print("  catalog: データなし", file=sys.stderr)
        return

    all_keys: list[str] = []
    seen = set()
    priority = ["child_asin", "parent_asin", "title", "brand", "color", "size", "style",
                "bsr_rank_1", "bsr_category_1", "bsr_rank_2", "bsr_category_2",
                "bsr_display_rank_1", "bsr_display_group_1",
                "image_count", "variation_theme", "variation_attrs",
                "browse_classification", "itemClassification",
                "item_height", "item_length", "item_width", "item_weight",
                "pkg_height", "pkg_length", "pkg_width", "pkg_weight",
                "manufacturer", "modelNumber", "partNumber",
                "has_reviews", "has_aplus", "fetched_at"]
    for k in priority:
        for row in rows:
            if k in row and k not in seen:
                all_keys.append(k)
                seen.add(k)
                break
    bullet_keys = sorted({k for row in rows for k in row if k.startswith("bullet_")},
                         key=lambda x: int(x.split("_")[1]))
    for k in bullet_keys:
        if k not in seen:
            all_keys.append(k)
            seen.add(k)
    for row in rows:
        for k in row:
            if k not in seen:
                all_keys.append(k)
                seen.add(k)

    out_path = output_dir / "catalog.csv"
    with open(out_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=all_keys, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"  catalog.csv: {len(rows)}行, {len(all_keys)}カラム", file=sys.stderr)


# --- images.csv（商品画像 + A+画像+テキスト統合） ---

def build_images_csv(all_items: dict[str, list[dict]], asin_map: dict[str, str],
                     lib_path: Path, output_dir: Path, genai_client=None):
    rows = []
    for eagle_asin, items in all_items.items():
        parent_asin = asin_map.get(eagle_asin, "")

        # 商品画像URL（variant毎に最大サイズのみ）
        data = _get_latest(items, "catalog")
        if data:
            raw = data.get("_raw_parent", {})
            images_markets = raw.get("images", [])
            if images_markets:
                best_per_variant: dict[str, dict] = {}
                for img in images_markets[0].get("images", []):
                    variant = img.get("variant", "")
                    pixels = (img.get("width", 0) or 0) * (img.get("height", 0) or 0)
                    if variant not in best_per_variant or pixels > best_per_variant[variant]["_pixels"]:
                        best_per_variant[variant] = {**img, "_pixels": pixels}

                for variant, img in sorted(best_per_variant.items()):
                    url = img.get("link", "")
                    text = ""
                    # --extract-text 指定時: MAIN以外のサブ画像をOCR
                    if genai_client and url and variant != "MAIN":
                        text = _extract_text_from_url(url, genai_client)
                        import time
                        time.sleep(0.3)  # レート制限対策

                    rows.append({
                        "child_asin": eagle_asin,
                        "parent_asin": parent_asin,
                        "source": "product",
                        "variant": variant,
                        "url": url,
                        "width": img.get("width", ""),
                        "height": img.get("height", ""),
                        "eagle_path": "",
                        "text": text,
                    })

        # A+画像（eagle_path付き）+ A+テキストを紐付け
        aplus_data = _get_latest(items, "aplus")
        aplus_texts = {}
        if aplus_data and aplus_data.get("found", False):
            texts = aplus_data.get("texts", [])
            # A+テキストをセクション番号で索引化（APLUS_01 → texts[0]）
            for i, text in enumerate(texts):
                aplus_texts[f"APLUS_{i+1:02d}"] = text

        aplus_images = [i for i in items
                        if _tag_value(i["tags"], "type") == "image"
                        and _tag_value(i["tags"], "variant").startswith("APLUS")]
        # variant順にソート
        aplus_images.sort(key=lambda x: _tag_value(x["tags"], "variant"))

        for img in aplus_images:
            variant = _tag_value(img["tags"], "variant")
            rows.append({
                "child_asin": eagle_asin,
                "parent_asin": parent_asin,
                "source": "aplus",
                "variant": variant,
                "url": "",
                "width": "",
                "height": "",
                "eagle_path": str(img["file_path"]) if img["file_path"] else "",
                "text": aplus_texts.get(variant, ""),
            })

    if not rows:
        print("  images: データなし", file=sys.stderr)
        return

    fieldnames = ["child_asin", "parent_asin", "source", "variant",
                  "url", "width", "height", "eagle_path", "text"]
    out_path = output_dir / "images.csv"
    with open(out_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"  images.csv: {len(rows)}行", file=sys.stderr)


# --- reviews.csv ---

def build_reviews_csv(all_items: dict[str, list[dict]], asin_map: dict[str, str], output_dir: Path):
    rows = []
    for eagle_asin, items in all_items.items():
        parent_asin = asin_map.get(eagle_asin, "")
        data = _get_latest(items, "reviews")
        if not data:
            continue

        for rev in data.get("reviews", []):
            star_raw = rev.get("star", "")
            star_match = re.match(r"([\d.]+)", str(star_raw))
            star = star_match.group(1) if star_match else star_raw

            # variation: "Amazonで購入" 等の非バリエーション文字列は空にする
            variation = rev.get("variation") or ""
            if variation in ("Amazonで購入", "Amazon.co.jpで購入"):
                variation = ""

            # title: スクレイパーが星評価テキストをtitleに入れている場合は空にする
            title = rev.get("title", "")
            if re.match(r"^5つ星のうち[\d.]+$", title):
                title = ""

            rows.append({
                "child_asin": eagle_asin,
                "parent_asin": parent_asin,
                "variation": variation,
                "star": star,
                "title": title,
                "body": rev.get("body", ""),
                "date": rev.get("date", ""),
                "captured_date": data.get("fetched_at", "")[:10],
            })

    if not rows:
        print("  reviews: データなし", file=sys.stderr)
        return

    fieldnames = ["child_asin", "parent_asin", "variation", "star", "title", "body", "date", "captured_date"]
    out_path = output_dir / "reviews.csv"
    with open(out_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    print(f"  reviews.csv: {len(rows)}行", file=sys.stderr)


# --- メイン ---

def main():
    parser = argparse.ArgumentParser(description="Eagle競合データ → ローカルCSV変換")
    parser.add_argument("--product", required=True, help="Eagle内の商品名（例: マザーズリュック）")
    parser.add_argument("--output", required=True, help="CSV出力先ディレクトリ")
    parser.add_argument("--extract-text", action="store_true",
                        help="Gemini Visionで商品サブ画像のテキストを抽出（API課金あり）")
    args = parser.parse_args()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        info = _eagle_get("/api/application/info")
        if info.get("status") != "success":
            print("エラー: Eagle APIに接続できません。", file=sys.stderr)
            sys.exit(1)
    except Exception:
        print("エラー: Eagle APIに接続できません。", file=sys.stderr)
        sys.exit(1)

    print(f"商品: {args.product}", file=sys.stderr)

    product_folder_id = _find_product_folder(args.product)
    if not product_folder_id:
        print(f"エラー: Eagle内に「Amazon競合データ/{args.product}」が見つかりません。", file=sys.stderr)
        sys.exit(1)

    asin_folders = _find_asin_folders(product_folder_id)
    if not asin_folders:
        print("エラー: ASINフォルダが見つかりません。", file=sys.stderr)
        sys.exit(1)

    print(f"ASIN数: {len(asin_folders)}", file=sys.stderr)
    lib_path = _get_library_path()

    all_items: dict[str, list[dict]] = {}
    for af in asin_folders:
        eagle_asin = af["name"]
        items = _list_folder_items(af["id"], lib_path)
        all_items[eagle_asin] = items
        print(f"  {eagle_asin}: {len(items)}アイテム", file=sys.stderr)

    asin_map = _build_asin_parent_map(all_items)
    mapped = sum(1 for v in asin_map.values() if v)
    print(f"\n親ASIN解決: {mapped}/{len(asin_map)}", file=sys.stderr)

    # テキスト抽出用Geminiクライアント
    genai_client = None
    if args.extract_text:
        from google import genai
        api_key = _get_gemini_api_key()
        genai_client = genai.Client(api_key=api_key)
        print("テキスト抽出: ON（Gemini Vision）", file=sys.stderr)

    print(f"CSV出力先: {output_dir}", file=sys.stderr)
    build_catalog_csv(all_items, asin_map, output_dir)
    build_reviews_csv(all_items, asin_map, output_dir)
    build_images_csv(all_items, asin_map, lib_path, output_dir, genai_client)

    # 不要になったファイルを削除
    for old_file in ["aplus.csv", "asin_map.csv"]:
        old_path = output_dir / old_file
        if old_path.exists():
            old_path.unlink()
            print(f"  {old_file}: 削除（統合済み）", file=sys.stderr)

    print("\n完了", file=sys.stderr)


if __name__ == "__main__":
    main()
