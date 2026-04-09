# /// script
# requires-python = ">=3.12"
# dependencies = ["requests>=2.31.0"]
# ///
"""Amazon.co.jp レビュー取得スクリプト（親ASIN単位、agent-browser使用）。

使い方:
  uv run fetch_reviews.py --asins B000PARENT1 B000PARENT2 --product マザーズリュック
  uv run fetch_reviews.py --asins B000PARENT --product マザーズリュック --max-reviews 100

前提:
  - 親ASINを渡すこと（子ASINを渡すとそのバリエーションのレビューのみになる）
  - Chrome を起動した状態で実行（--auto-connect モード）

出力:
  C:/Users/ninni/data/amazon/competitors/{親ASIN}/reviews_{YYYYMMDD}.json  ← バックアップ
  Eagle: Amazon競合データ/{product}/{親ASIN}/ に reviews JSON を登録

レビューJSON構造:
  {
    "parent_asin": "B000XXX",
    "reviews": [
      {
        "star": "5.0 out of 5 stars",
        "title": "...",
        "body": "...",
        "date": "...",
        "author": "...",
        "variation": "色: ブラック"  ← どのバリエーションへのレビューか（不明なら null）
      }
    ]
  }
"""

import argparse
import json
import random
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

_SCRIPT_DIR = Path(__file__).parent
sys.path.insert(0, str(_SCRIPT_DIR))

from lib.eagle_integration import eagle_available, register_file

SELECTORS_FILE = _SCRIPT_DIR / "selectors" / "amazon_jp.json"
import sys as _sys
AGENT_BROWSER = "npx.cmd" if _sys.platform == "win32" else "npx"
AGENT_BROWSER_ARGS = ["agent-browser", "--session-name", "amazon-jp"]


def _load_selectors() -> dict:
    return json.loads(SELECTORS_FILE.read_text(encoding="utf-8"))


def _ab(subcmd: list[str], capture: bool = True) -> str:
    cmd = [AGENT_BROWSER] + AGENT_BROWSER_ARGS + subcmd
    result = subprocess.run(
        cmd, capture_output=capture, text=True, encoding="utf-8", errors="replace", timeout=60,
    )
    return result.stdout.strip() if capture else ""


def _ab_eval(js: str) -> str:
    # --stdin でJS文字列をstdinから渡してshellクォート問題を回避
    cmd = [AGENT_BROWSER] + AGENT_BROWSER_ARGS + ["eval", "--stdin"]
    result = subprocess.run(
        cmd, input=js, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60,
    )
    return result.stdout.strip()


def _extract_reviews_js(selectors: dict) -> str:
    """レビュー抽出用JS（セレクタJSONから動的生成）"""
    item_sels = selectors["reviews"]["item"]
    star_sels = selectors["reviews"]["star"]
    title_sels = selectors["reviews"]["title"]
    body_sels = selectors["reviews"]["body"]
    date_sels = selectors["reviews"]["date"]
    author_sels = selectors["reviews"]["author"]
    variation_sels = selectors["reviews"]["variation"]

    def sel_js(sels: list[str], context: str = "el") -> str:
        parts = [f'{context}.querySelector("{s}")?.innerText?.trim()' for s in sels]
        return " || ".join(parts) + ' || ""'

    def sel_js_nullable(sels: list[str], context: str = "el") -> str:
        """null を返す版（バリエーションが存在しない場合は null）"""
        parts = [
            f'({context}.querySelector("{s}") ? {context}.querySelector("{s}").innerText.trim() : null)'
            for s in sels
        ]
        return " || ".join(parts)

    return f"""
(function() {{
  const itemSelectors = {json.dumps(item_sels)};
  let items = [];
  for (const sel of itemSelectors) {{
    items = Array.from(document.querySelectorAll(sel));
    if (items.length > 0) break;
  }}
  return items.map(el => ({{
    star: {sel_js(star_sels)},
    title: {sel_js(title_sels)},
    body: {sel_js(body_sels)},
    date: {sel_js(date_sels)},
    author: {sel_js(author_sels)},
    variation: {sel_js_nullable(variation_sels)},
  }}));
}})()
"""


def _fetch_pages(parent_asin: str, base_params: str, max_per_filter: int,
                  selectors: dict, existing_bodies: set[str]) -> list[dict]:
    """指定URLパラメータでページネーションしてレビューを取得"""
    url = f"https://www.amazon.co.jp/product-reviews/{parent_asin}?{base_params}"
    _ab(["open", url])
    time.sleep(2)

    reviews: list[dict] = []
    raw = _ab_eval(_extract_reviews_js(selectors))
    try:
        page_reviews = json.loads(raw) if raw and raw.startswith("[") else []
        new = [r for r in page_reviews if r.get("body", "")[:50] not in existing_bodies]
        reviews.extend(new)
        for r in new:
            existing_bodies.add(r.get("body", "")[:50])
    except Exception:
        pass

    page = 2
    while len(reviews) < max_per_filter:
        next_url = f"https://www.amazon.co.jp/product-reviews/{parent_asin}?{base_params}&pageNumber={page}"
        _ab(["open", next_url])
        time.sleep(random.uniform(3, 5))

        raw2 = _ab_eval(_extract_reviews_js(selectors))
        try:
            more = json.loads(raw2) if raw2 and raw2.startswith("[") else []
            if not more:
                break
            new = [r for r in more if r.get("body", "")[:50] not in existing_bodies]
            if not new:
                break
            reviews.extend(new)
            for r in new:
                existing_bodies.add(r.get("body", "")[:50])
        except Exception:
            break
        page += 1

    return reviews


# Amazon filterByStar パラメータ値
_STAR_FILTERS = ["one_star", "two_star", "three_star", "four_star", "five_star"]


def _fetch_reviews_for_parent(parent_asin: str, max_reviews: int, selectors: dict) -> list[dict]:
    """親ASINのレビューページから全★・全バリエーションのレビューを取得。

    戦略: 各★（1-5）別にfilterByStarで取得し、全★のレビューを確実にカバー。
    Amazonのデフォルトソートは5★偏重のため、★別取得で偏りを排除する。
    """
    all_reviews: list[dict] = []
    seen_bodies: set[str] = set()
    per_star = max(max_reviews // 5, 20)  # 各★あたりの上限

    for star_filter in _STAR_FILTERS:
        params = f"reviewerType=all_reviews&sortBy=recent&filterByStar={star_filter}"
        print(f"  [{star_filter}] 取得中...", file=sys.stderr)
        star_reviews = _fetch_pages(parent_asin, params, per_star, selectors, seen_bodies)
        all_reviews.extend(star_reviews)
        print(f"  [{star_filter}] {len(star_reviews)}件", file=sys.stderr)

        if len(all_reviews) >= max_reviews:
            break
        time.sleep(random.uniform(1, 2))

    # variationを正規化（空文字・"Amazonで購入" 等はnullに）
    _NON_VARIANT = {"Amazonで購入", "Verified Purchase", "Amazon購入"}
    for r in all_reviews:
        v = r.get("variation")
        if not v or v in _NON_VARIANT or "で購入" in v:
            r["variation"] = None

    return all_reviews[:max_reviews]


def _register_reviews_eagle(
    file_path: Path, parent_asin: str, product_name: str
) -> str | None:
    """レビューJSONをEagleに登録"""
    if not eagle_available():
        return None

    captured = datetime.now().strftime("%Y%m")
    tags = [
        "type:reviews",
        f"parent_asin:{parent_asin}",
        f"captured:{captured}",
    ]
    return register_file(
        file_path=file_path,
        parent_asin=parent_asin,
        product_name=product_name,
        tags=tags,
        name=file_path.name,
    )


def cmd_fetch(args):
    selectors = _load_selectors()
    product_name = args.product or "unknown"
    results = {"success": [], "failed": []}

    for i, parent_asin in enumerate(args.asins):
        print(f"[{i+1}/{len(args.asins)}] {parent_asin} レビュー取得中...", file=sys.stderr)

        try:
            reviews = _fetch_reviews_for_parent(parent_asin, args.max_reviews, selectors)

            # Eagle登録（tmpに書いて登録後に削除）
            date_str = datetime.now().strftime("%Y%m%d")
            filename = f"reviews_{date_str}.json"
            with tempfile.TemporaryDirectory() as tmp_dir:
                tmp_path = Path(tmp_dir) / filename
                tmp_path.write_text(
                    json.dumps(
                        {
                            "parent_asin": parent_asin,
                            "fetched_at": datetime.now().isoformat(),
                            "count": len(reviews),
                            "reviews": reviews,
                        },
                        ensure_ascii=False,
                        indent=2,
                    ),
                    encoding="utf-8",
                )
                _register_reviews_eagle(tmp_path, parent_asin, product_name)

            print(f"  ✓ {parent_asin}: {len(reviews)}件", file=sys.stderr)
            results["success"].append({
                "parent_asin": parent_asin,
                "count": len(reviews),
            })

        except Exception as e:
            print(f"  ✗ {parent_asin}: {e}", file=sys.stderr)
            results["failed"].append({"asin": parent_asin, "error": str(e)})

        if i < len(args.asins) - 1:
            time.sleep(random.uniform(3, 5))

    print(f"\nFetched: {len(results['success'])}/{len(args.asins)} ASINs", file=sys.stderr)
    return results


def main():
    parser = argparse.ArgumentParser(description="Amazon.co.jp レビュー取得（親ASIN単位）")
    parser.add_argument("--asins", nargs="+", required=True, help="親ASINリスト")
    parser.add_argument("--product", required=True, help="Eagleフォルダ名（例: マザーズリュック）")
    parser.add_argument("--max-reviews", type=int, default=50, help="最大取得件数/商品（デフォルト: 50）")
    args = parser.parse_args()

    try:
        result = cmd_fetch(args)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
