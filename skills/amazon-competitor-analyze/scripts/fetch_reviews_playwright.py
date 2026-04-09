# /// script
# requires-python = ">=3.12"
# dependencies = ["playwright>=1.58.0"]
# ///
"""Amazon.co.jp 全★レビュー取得スクリプト（Playwright persistent context版）。

カテゴリ非依存。任意のASINの全★テキストレビューを取得する。
初回のみ --login でAmazonログインが必要。以降はheadlessで自動実行。

使い方:
    # 初回（ログイン用）。ブラウザを閉じるとセッション保存
    uv run fetch_reviews_playwright.py --login

    # catalog.csvから全商品のレビューを取得（推奨。子→親ASIN自動解決）
    uv run fetch_reviews_playwright.py \
        --catalog path/to/competitor-data/catalog.csv \
        --output path/to/competitor-data/reviews.json

    # ASIN直接指定
    uv run fetch_reviews_playwright.py --asins B091NQ5WXY B0FB8Z8RZV

    # CAPTCHAが出た後（遅めペース）
    uv run fetch_reviews_playwright.py --catalog ... --pace slow

既知の注意点:
    - レビューページはAmazonログイン必須（初回 --login で解決）
    - 一部の商品は子ASINでのみレビューページが存在（自動で子→親の両方を試行）
    - 在庫切れ商品はレビューページが存在しない場合がある（自動スキップ）
    - 「さらに10件表示」ボタンクリックで全件読み込み（URLページネーションは無効）
    - 37社で約1時間（normalペース）。CAPTCHA検出時は即中断（取得済み分は保持）
"""

import argparse
import csv
import json
import random
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

from playwright.sync_api import sync_playwright

USER_DATA_DIR = str(Path.home() / ".playwright-amazon")
STAR_FILTERS = ["one_star", "two_star", "three_star", "four_star", "five_star"]
_NON_VARIANT = {"Amazonで購入", "Verified Purchase", "Amazon購入"}

EXTRACT_JS = """els => els.map(el => ({
    star: el.querySelector('[data-hook="review-star-rating"] .a-icon-alt')?.innerText || '',
    title: el.querySelector('[data-hook="review-title"] span:not(.a-icon-alt)')?.innerText || '',
    body: el.querySelector('[data-hook="review-body"] span')?.innerText || '',
    date: el.querySelector('[data-hook="review-date"]')?.innerText || '',
    author: el.querySelector('[data-hook="review-author"] .a-profile-name')?.innerText || '',
    variation: el.querySelector('[data-hook="format-strip"]')?.innerText || null,
}))"""

PACE = {
    "normal": {"page": (4, 7), "star": (3, 5), "product": (10, 15), "batch_pause": 45},
    "slow": {"page": (7, 12), "star": (5, 8), "product": (15, 25), "batch_pause": 90},
}
BATCH_SIZE = 8


def _normalize_variation(v):
    if not v or v in _NON_VARIANT or "で購入" in v:
        return None
    return v


def _sleep(r):
    time.sleep(random.uniform(*r))


def _is_blocked(page):
    url = page.url.lower()
    if "signin" in url:
        return "login_required"
    if "captcha" in url:
        return "captcha"
    try:
        c = page.content()[:1000]
        if "ショッピングを続ける" in c:
            return "captcha"
        if "ページが見つかりません" in c:
            return "not_found"
    except Exception:
        pass
    return None


def _try_review_page(page, asin, pace):
    url = f"https://www.amazon.co.jp/product-reviews/{asin}?reviewerType=all_reviews&sortBy=recent&filterByStar=five_star"
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=20000)
    except Exception:
        return None
    _sleep((2, 3))
    b = _is_blocked(page)
    if b == "not_found":
        return None
    if b in ("captcha", "login_required"):
        return b
    n = page.eval_on_selector_all('[data-hook="review"]', "els => els.length")
    return asin if n > 0 else None


def _resolve_review_asin(page, child, parent, pace):
    r = _try_review_page(page, child, pace)
    if r in ("captcha", "login_required"):
        return r
    if r:
        return r
    if parent and parent != child:
        _sleep((2, 3))
        r = _try_review_page(page, parent, pace)
        if r in ("captcha", "login_required"):
            return r
        if r:
            return r
    return None


def _fetch_reviews(page, review_asin, max_reviews, pace):
    all_reviews = []
    seen = set()
    blocked = False

    for sf in STAR_FILTERS:
        if blocked:
            break
        url = f"https://www.amazon.co.jp/product-reviews/{review_asin}?reviewerType=all_reviews&sortBy=recent&filterByStar={sf}"
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=20000)
        except Exception:
            continue
        _sleep(pace["page"])

        b = _is_blocked(page)
        if b in ("login_required", "captcha"):
            blocked = True
            break
        if b == "not_found":
            continue

        star_reviews = []
        for r in page.eval_on_selector_all('[data-hook="review"]', EXTRACT_JS):
            key = (r.get("body", "").strip(), r.get("date", ""))
            if key[0] and key not in seen:
                seen.add(key)
                r["variation"] = _normalize_variation(r.get("variation"))
                star_reviews.append(r)

        while len(all_reviews) + len(star_reviews) < max_reviews:
            try:
                btn = page.locator('a:has-text("さらに"), a:has-text("more reviews")').first
                if not btn.is_visible(timeout=3000):
                    break
                btn.click(timeout=5000)
            except Exception:
                break
            _sleep(pace["page"])
            if _is_blocked(page) in ("captcha", "login_required"):
                blocked = True
                break
            new = 0
            for r in page.eval_on_selector_all('[data-hook="review"]', EXTRACT_JS):
                key = (r.get("body", "").strip(), r.get("date", ""))
                if key[0] and key not in seen:
                    seen.add(key)
                    r["variation"] = _normalize_variation(r.get("variation"))
                    star_reviews.append(r)
                    new += 1
            if new == 0:
                break

        all_reviews.extend(star_reviews)
        print(f"    [{sf}] {len(star_reviews)}件", file=sys.stderr)
        if len(all_reviews) >= max_reviews:
            break
        _sleep(pace["star"])

    return {"review_asin": review_asin, "count": len(all_reviews), "reviews": all_reviews[:max_reviews], "blocked": blocked}


def _load_catalog(path):
    products = []
    with open(path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            products.append({
                "child_asin": row["child_asin"],
                "parent_asin": row.get("parent_asin", row["child_asin"]),
                "brand": row.get("brand", ""),
            })
    return products


def main():
    parser = argparse.ArgumentParser(description="Amazon全★レビュー取得（Playwright版・汎用）")
    g = parser.add_mutually_exclusive_group()
    g.add_argument("--asins", nargs="+", help="ASINリスト")
    g.add_argument("--catalog", help="catalog.csvパス（子→親ASIN自動解決）")
    parser.add_argument("--output", help="出力JSONファイルパス")
    parser.add_argument("--max-reviews", type=int, default=500, help="最大取得件数/商品")
    parser.add_argument("--login", action="store_true", help="headedモードでログイン")
    parser.add_argument("--pace", choices=["normal", "slow"], default="normal")
    args = parser.parse_args()

    if args.login:
        with sync_playwright() as p:
            ctx = p.chromium.launch_persistent_context(USER_DATA_DIR, headless=False, locale="ja-JP")
            pg = ctx.pages[0] if ctx.pages else ctx.new_page()
            pg.goto("https://www.amazon.co.jp", wait_until="domcontentloaded")
            print("Amazonにログイン後、ブラウザを閉じてください。", file=sys.stderr)
            try:
                pg.wait_for_event("close", timeout=300000)
            except Exception:
                pass
            try:
                ctx.close()
            except Exception:
                pass
            print("セッション保存完了。", file=sys.stderr)
        return

    if args.catalog:
        products = _load_catalog(args.catalog)
    elif args.asins:
        products = [{"child_asin": a, "parent_asin": a, "brand": ""} for a in args.asins]
    else:
        parser.error("--asins または --catalog を指定")

    pace = PACE[args.pace]
    results = {}

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(USER_DATA_DIR, headless=True, locale="ja-JP")
        page = ctx.pages[0] if ctx.pages else ctx.new_page()

        for i, prod in enumerate(products):
            child, parent, brand = prod["child_asin"], prod["parent_asin"], prod["brand"][:15]
            print(f"[{i+1}/{len(products)}] {child} ({brand})...", file=sys.stderr)

            ra = _resolve_review_asin(page, child, parent, pace)
            if ra in ("captcha", "login_required"):
                print(f"  ブロック。残りをスキップ。", file=sys.stderr)
                results[child] = {"child_asin": child, "count": 0, "reviews": [], "blocked": True}
                for rem in products[i+1:]:
                    results[rem["child_asin"]] = {"child_asin": rem["child_asin"], "count": 0, "reviews": [], "skipped": True}
                break
            if not ra:
                print(f"  レビューページなし", file=sys.stderr)
                results[child] = {"child_asin": child, "count": 0, "reviews": [], "no_page": True}
                _sleep(pace["product"])
                continue

            print(f"  ASIN: {ra} ({'child' if ra == child else 'parent'})", file=sys.stderr)
            result = _fetch_reviews(page, ra, args.max_reviews, pace)
            result["child_asin"] = child
            result["parent_asin"] = parent
            results[child] = result

            if result["blocked"]:
                print(f"  ブロック。残りをスキップ。", file=sys.stderr)
                for rem in products[i+1:]:
                    results[rem["child_asin"]] = {"child_asin": rem["child_asin"], "count": 0, "reviews": [], "skipped": True}
                break

            print(f"  合計: {result['count']}件", file=sys.stderr)
            if i < len(products) - 1:
                _sleep(pace["product"])
                if (i+1) % BATCH_SIZE == 0:
                    p_ = pace["batch_pause"]
                    print(f"  --- 休憩 {p_}秒 ({i+1}/{len(products)}) ---", file=sys.stderr)
                    time.sleep(p_)

        ctx.close()

    total = sum(r["count"] for r in results.values())
    ok = sum(1 for r in results.values() if r["count"] > 0)
    print(f"\n完了: {ok}/{len(products)}社, {total}件", file=sys.stderr)

    out = json.dumps(results, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(out, encoding="utf-8")
        print(f"保存: {args.output}", file=sys.stderr)
    else:
        print(out)


if __name__ == "__main__":
    main()
