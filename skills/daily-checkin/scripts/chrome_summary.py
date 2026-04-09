"""
指定日のChrome閲覧履歴をサマリー表示するスクリプト。
daily-checkin スキルの行動データ取得に使用。

使い方:
    uv run python ~/.claude/skills/daily-checkin/scripts/chrome_summary.py --date 2026-03-30
    uv run python ~/.claude/skills/daily-checkin/scripts/chrome_summary.py  # 昨日
    uv run python ~/.claude/skills/daily-checkin/scripts/chrome_summary.py --json  # JSON出力
"""
import sys
import os
import shutil
import sqlite3
import argparse
import json
from datetime import datetime, timezone, timedelta
from collections import Counter
from urllib.parse import urlparse

sys.stdout.reconfigure(encoding="utf-8")

CHROME_HISTORY_SRC = "C:/Users/ninni/AppData/Local/Google/Chrome/User Data/Default/History"
TMP_DIR = os.path.expanduser("~/projects/tmp")
COPY_PATH = os.path.join(TMP_DIR, "_chrome_hist_checkin.db")
WEBKIT_EPOCH_OFFSET = 11644473600
JST = timezone(timedelta(hours=9))

# フィルタ: 内部ページ・認証画面などノイズを除外
SKIP_DOMAINS = {
    "newtab", "extensions", "", "accounts.google.com",
    "myaccount.google.com", "consent.google.com",
}
SKIP_URL_PATTERNS = [
    "chrome://", "chrome-extension://", "about:", "edge://",
    "/auth", "/login", "/signin", "/oauth", "/callback",
    "accounts.google.com",
]


def webkit_range_for_date(date_str: str):
    """JST日付のWebkitタイムスタンプ範囲(UTC)を返す"""
    dt_jst = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=JST)
    dt_start_utc = dt_jst.astimezone(timezone.utc)
    dt_end_utc = dt_start_utc + timedelta(days=1)
    wk_start = int((dt_start_utc.timestamp() + WEBKIT_EPOCH_OFFSET) * 1_000_000)
    wk_end = int((dt_end_utc.timestamp() + WEBKIT_EPOCH_OFFSET) * 1_000_000)
    return wk_start, wk_end


def is_noise(url: str, domain: str) -> bool:
    if domain in SKIP_DOMAINS:
        return True
    return any(p in url.lower() for p in SKIP_URL_PATTERNS)


def summarize(date_str: str):
    os.makedirs(TMP_DIR, exist_ok=True)
    shutil.copy2(CHROME_HISTORY_SRC, COPY_PATH)

    try:
        wk_start, wk_end = webkit_range_for_date(date_str)
        conn = sqlite3.connect(COPY_PATH)
        cur = conn.execute(
            """
            SELECT u.title, u.url, v.visit_time
            FROM visits v JOIN urls u ON v.url = u.id
            WHERE v.visit_time BETWEEN ? AND ?
            ORDER BY v.visit_time ASC
            """,
            (wk_start, wk_end),
        )
        rows = cur.fetchall()
        conn.close()
    finally:
        if os.path.exists(COPY_PATH):
            os.remove(COPY_PATH)

    # 分類
    domain_counts = Counter()
    entries = []
    for title, url, vt in rows:
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.replace("www.", "")
        except Exception:
            domain = "?"
        if is_noise(url, domain):
            continue
        domain_counts[domain] += 1
        unix_sec = vt / 1_000_000 - WEBKIT_EPOCH_OFFSET
        dt_utc = datetime.fromtimestamp(unix_sec, tz=timezone.utc)
        dt_jst = dt_utc.astimezone(JST)
        entries.append({
            "hour": dt_jst.hour,
            "title": title or "",
            "url": url,
            "domain": domain,
        })

    # 重複タイトル除去してユニークなページを抽出
    seen_titles = set()
    unique_entries = []
    for e in entries:
        key = e["title"][:40] if e["title"] else e["url"][:40]
        if key not in seen_titles:
            seen_titles.add(key)
            unique_entries.append(e)

    return {
        "date": date_str,
        "total_visits": len(rows),
        "filtered_visits": len(entries),
        "unique_pages": len(unique_entries),
        "top_domains": domain_counts.most_common(10),
        "entries": unique_entries,
    }


def print_text(data):
    print(f"=== Chrome履歴: {data['date']} ===")
    print(f"総訪問: {data['total_visits']}  フィルタ後: {data['filtered_visits']}  ユニーク: {data['unique_pages']}")
    print()
    print("ドメイン別:")
    for domain, count in data["top_domains"]:
        print(f"  {count:3d}  {domain}")
    print()
    print("主なページ:")
    for e in data["entries"][:25]:
        title = e["title"][:65] if e["title"] else e["domain"]
        print(f"  {e['hour']:02d}時  {title}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=None, help="対象日 (YYYY-MM-DD)。省略時は昨日")
    parser.add_argument("--json", action="store_true", help="JSON出力")
    args = parser.parse_args()

    if args.date is None:
        yesterday = datetime.now(JST) - timedelta(days=1)
        args.date = yesterday.strftime("%Y-%m-%d")

    data = summarize(args.date)

    if args.json:
        # top_domains をdict化
        data["top_domains"] = {d: c for d, c in data["top_domains"]}
        json.dump(data, sys.stdout, ensure_ascii=False, indent=2)
    else:
        print_text(data)


if __name__ == "__main__":
    main()
