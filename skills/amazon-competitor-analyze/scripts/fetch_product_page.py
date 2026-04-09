# /// script
# requires-python = ">=3.12"
# dependencies = ["playwright>=1.58.0"]
# ///
"""Amazon.co.jp 商品ページから価格・評価・スペックを取得する汎用スクリプト。

カテゴリ非依存。商品ページ上の全スペック情報をkey-value形式で取得する。
Playwright headlessで動作。ログイン不要。

使い方:
    # 単品テスト
    uv run fetch_product_page.py --asins B091NQ5WXY

    # 複数商品（出力ファイル指定）
    uv run fetch_product_page.py --asins B091NQ5WXY B0FB8Z8RZV --output prices.json

    # ブラウザ表示モード（デバッグ用）
    uv run fetch_product_page.py --asins B091NQ5WXY --headed

出力JSON構造:
    {
      "B091NQ5WXY": {
        "asin": "B091NQ5WXY",
        "title": "...",
        "price": 5900,
        "price_text": "￥5,900",
        "rating": "5つ星のうち4.5",
        "review_count": 997,
        "star_distribution": {"5star": "50%", "4star": "26%", ...},
        "specs": {"重量": "800 g", "容量": "23 L", ...},
        "bullets": ["箇条書き1", "箇条書き2", ...]
      }
    }
"""

import argparse
import json
import re
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from playwright.sync_api import sync_playwright


def _extract_product_data(page) -> dict:
    """商品ページから汎用データを抽出"""
    result = {
        "title": "",
        "price": None,
        "price_text": "",
        "rating": "",
        "review_count": None,
        "star_distribution": {},
        "specs": {},
        "bullets": [],
    }

    # タイトル
    try:
        result["title"] = page.locator("#centerCol h1 span").first.inner_text(timeout=5000).strip()
    except Exception:
        try:
            result["title"] = page.title().split(":")[0].strip()
        except Exception:
            pass

    # 価格（複数セレクタを順に試行）
    for sel in [
        "#corePrice_feature_div .a-offscreen",
        ".priceToPay .a-offscreen",
        "#corePriceDisplay_desktop_feature_div .a-offscreen",
        "#price_inside_buybox",
        "#priceblock_ourprice",
    ]:
        try:
            text = page.locator(sel).first.inner_text(timeout=2000).strip()
            if text and ("￥" in text or "¥" in text):
                result["price_text"] = text
                match = re.search(r"[\d,]+", text.replace("￥", "").replace("¥", ""))
                if match:
                    result["price"] = int(match.group().replace(",", ""))
                break
        except Exception:
            continue

    # 評価
    try:
        result["rating"] = page.locator("#acrPopover .a-icon-alt").first.inner_text(timeout=3000).strip()
    except Exception:
        pass

    # レビュー数
    try:
        text = page.locator("#acrCustomerReviewText").first.inner_text(timeout=3000).strip()
        match = re.search(r"[\d,]+", text)
        if match:
            result["review_count"] = int(match.group().replace(",", ""))
    except Exception:
        pass

    # ★分布ヒストグラム
    for star in range(5, 0, -1):
        try:
            pct = page.locator(
                f"#histogramTable tr:nth-child({6 - star}) .a-text-right a"
            ).first.inner_text(timeout=2000).strip()
            result["star_distribution"][f"{star}star"] = pct
        except Exception:
            pass

    # スペック表（商品の詳細テーブル — カテゴリ非依存で全key-value取得）
    for table_sel in [
        "#productDetails_techSpec_section_1 tr",
        "#productDetails_detailBullets_sections1 tr",
        "#detailBullets_feature_div li",
    ]:
        try:
            rows = page.locator(table_sel).all()
            for row in rows:
                text = row.inner_text()
                parts = re.split(r"\t+|\n+", text.strip())
                if len(parts) >= 2:
                    key = parts[0].strip().rstrip(":")
                    val = parts[1].strip()
                    if key and val and key != val:
                        result["specs"][key] = val
        except Exception:
            continue

    # 箇条書き
    try:
        bullets = page.locator("#feature-bullets li span.a-list-item").all()
        for b in bullets:
            text = b.inner_text().strip()
            if text and len(text) > 5:
                result["bullets"].append(text)
    except Exception:
        pass

    return result


def main():
    parser = argparse.ArgumentParser(description="Amazon商品ページから価格・スペック取得（汎用）")
    parser.add_argument("--asins", nargs="+", required=True, help="ASINリスト")
    parser.add_argument("--output", help="出力JSONファイルパス（省略時はstdout）")
    parser.add_argument("--headed", action="store_true", help="ブラウザを表示する")
    parser.add_argument("--delay", type=float, default=4.0, help="商品間の待機秒数")
    args = parser.parse_args()

    results = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not args.headed)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            ),
            locale="ja-JP",
        )
        page = context.new_page()

        for i, asin in enumerate(args.asins):
            print(f"[{i + 1}/{len(args.asins)}] {asin}...", file=sys.stderr)
            try:
                page.goto(
                    f"https://www.amazon.co.jp/dp/{asin}",
                    wait_until="domcontentloaded",
                    timeout=15000,
                )
                time.sleep(1.5)
                data = _extract_product_data(page)
                data["asin"] = asin
                results[asin] = data
                print(
                    f"  {data['price_text'] or '---'} | {data['title'][:40]}",
                    file=sys.stderr,
                )
            except Exception as e:
                print(f"  エラー: {e}", file=sys.stderr)
                results[asin] = {"asin": asin, "error": str(e)}

            if i < len(args.asins) - 1:
                time.sleep(args.delay)

        browser.close()

    output = json.dumps(results, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"保存: {args.output} ({len(results)}社)", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
