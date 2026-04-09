"""ActivityWatch クエリスクリプト
Usage:
  uv run python <this-script>                      # 今日のサマリー
  uv run python <this-script> --date 2026-03-28    # 指定日
  uv run python <this-script> --days 7             # 直近N日間
  uv run python <this-script> --after-22           # 22時以降の詳細のみ
  uv run python <this-script> --after-22 --days 7  # 直近7日間の22時以降
  uv run python <this-script> --json               # JSON出力（他ツール連携用）
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import json
import urllib.request
from urllib.parse import quote
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import argparse

BASE = "http://localhost:5600/api/0"
JST = timezone(timedelta(hours=9))
HOSTNAME = None  # 自動検出

def fetch(url):
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            return json.loads(r.read())
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        print("ActivityWatchが起動していることを確認してください。", file=sys.stderr)
        sys.exit(1)

def detect_hostname():
    global HOSTNAME
    if HOSTNAME:
        return HOSTNAME
    buckets = fetch(f"{BASE}/buckets/")
    for name in buckets:
        if name.startswith("aw-watcher-window_"):
            HOSTNAME = name.replace("aw-watcher-window_", "")
            return HOSTNAME
    print("Error: aw-watcher-window バケットが見つかりません", file=sys.stderr)
    sys.exit(1)

def get_events(bucket, start, end, limit=10000):
    url = f"{BASE}/buckets/{bucket}/events?start={quote(start)}&end={quote(end)}&limit={limit}"
    return fetch(url)

def categorize_app(app, title):
    app_l = app.lower()
    title_l = title.lower()

    # EC関連
    if any(x in title_l for x in ['seller central', 'amazon seller', 'sellercentral', 'amazon ads']):
        return 'EC (Amazon)'
    if 'nocodb' in title_l:
        return 'EC (NocoDB)'

    # AI/開発
    if 'code.exe' in app_l or 'visual studio code' in app_l:
        return 'AI/開発 (VSCode/Claude)'
    if any(x in title_l for x in ['claude', 'chatgpt', 'openai', 'anthropic']):
        return 'AI/開発'
    if any(x in title_l for x in ['bigquery', 'cloud console', 'github']):
        return 'AI/開発 (GCP/GitHub)'

    # コンテンツ消費
    if 'youtube' in title_l:
        return 'コンテンツ消費 (YouTube)'
    if any(x in title_l for x in ['prime video', 'primevideo', 'amazon prime', 'netflix']):
        return 'コンテンツ消費 (動画)'
    if any(x in title_l for x in ['twitter', 'x.com', 'reddit', 'news', 'ニュース']):
        return 'コンテンツ消費 (SNS/ニュース)'

    # 仕事関連
    if any(x in app_l for x in ['outlook', 'teams', 'excel', 'word', 'powerpoint']):
        return '本業 (M365)'

    # ゲーム
    if any(x in app_l for x in ['minecraft', 'steam', 'rimworld']):
        return 'ゲーム'

    # ブラウザ（分類不能）
    if 'chrome' in app_l or 'firefox' in app_l or 'edge' in app_l:
        return 'ブラウジング (その他)'

    # システム
    if app_l in ('explorer.exe', 'lockapp.exe', 'searchhost.exe', 'startmenuexperiencehost.exe'):
        return 'システム'

    if app_l == 'unknown':
        return 'スリープ/放置'

    return f'その他 ({app})'

def format_duration(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    if h > 0:
        return f"{h}h{m:02d}m"
    return f"{m}m"

def analyze_day(date_str):
    hostname = detect_hostname()
    start = f"{date_str}T00:00:00+09:00"
    end_date = datetime.strptime(date_str, "%Y-%m-%d") + timedelta(days=1)
    end = f"{end_date.strftime('%Y-%m-%d')}T00:00:00+09:00"

    events = get_events(f"aw-watcher-window_{hostname}", start, end)
    afk_events = get_events(f"aw-watcher-afk_{hostname}", start, end)

    if not events:
        return None

    categories = defaultdict(float)
    after_22 = defaultdict(float)
    before_22 = defaultdict(float)
    total_seconds = 0
    active_app_seconds = 0  # スリープ/放置/システムを除く
    last_event_time = None
    first_event_time = None

    for e in events:
        ts = datetime.fromisoformat(e['timestamp']).astimezone(JST)
        dur = e['duration']
        app = e['data'].get('app', '?')
        title = e['data'].get('title', '?')
        cat = categorize_app(app, title)

        categories[cat] += dur
        total_seconds += dur

        if cat not in ('スリープ/放置', 'システム'):
            active_app_seconds += dur

        if ts.hour >= 22 or ts.hour < 6:
            after_22[cat] += dur
        else:
            before_22[cat] += dur

        if first_event_time is None or ts < first_event_time:
            first_event_time = ts
        if last_event_time is None or ts > last_event_time:
            last_event_time = ts

    # AFK分析
    active_seconds = sum(e['duration'] for e in afk_events if e['data'].get('status') == 'not-afk')

    return {
        'date': date_str,
        'categories': dict(categories),
        'after_22': dict(after_22),
        'before_22': dict(before_22),
        'total': total_seconds,
        'active_app': active_app_seconds,
        'active_afk': active_seconds,
        'first': first_event_time,
        'last': last_event_time,
    }

def print_summary(result):
    if result is None:
        print("  データなし")
        return

    print(f"\n{'='*60}")
    print(f"  {result['date']}")
    print(f"{'='*60}")

    if result['first'] and result['last']:
        print(f"PC使用時間帯: {result['first'].strftime('%H:%M')} - {result['last'].strftime('%H:%M')}")
    print(f"アクティブ時間（AFK判定）: {format_duration(result['active_afk'])}")
    print(f"アプリ使用時間（放置除く）: {format_duration(result['active_app'])}")

    print(f"\n--- カテゴリ別 ---")
    sorted_cats = sorted(result['categories'].items(), key=lambda x: -x[1])
    for cat, dur in sorted_cats:
        if dur >= 60:
            pct = dur / result['active_app'] * 100 if result['active_app'] > 0 else 0
            print(f"  {cat:30s} {format_duration(dur):>8s}  ({pct:4.1f}%)")

    if result['after_22']:
        night_total = sum(v for k, v in result['after_22'].items() if k not in ('スリープ/放置', 'システム'))
        if night_total >= 60:
            print(f"\n--- 22時-6時の内訳（深夜帯） ---")
            print(f"  深夜帯アクティブ合計: {format_duration(night_total)}")
            sorted_night = sorted(result['after_22'].items(), key=lambda x: -x[1])
            for cat, dur in sorted_night:
                if dur >= 60 and cat not in ('スリープ/放置', 'システム'):
                    print(f"    {cat:28s} {format_duration(dur):>8s}")
        else:
            print(f"\n  22時-6時のアクティブPC使用なし")
    else:
        print(f"\n  22時-6時のPC使用なし")

def result_to_dict(result):
    """JSON出力用にシリアライズ"""
    if result is None:
        return None
    r = dict(result)
    r['first'] = r['first'].isoformat() if r['first'] else None
    r['last'] = r['last'].isoformat() if r['last'] else None
    return r

def main():
    parser = argparse.ArgumentParser(description='ActivityWatch サマリー')
    parser.add_argument('--date', help='分析日 (YYYY-MM-DD)')
    parser.add_argument('--days', type=int, default=1, help='直近N日間')
    parser.add_argument('--after-22', action='store_true', help='22時以降の詳細のみ')
    parser.add_argument('--json', action='store_true', help='JSON出力')
    args = parser.parse_args()

    if args.date:
        dates = [args.date]
    else:
        today = datetime.now(JST).date()
        dates = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(args.days)]
        dates.reverse()

    results = []
    for date_str in dates:
        result = analyze_day(date_str)
        results.append(result)

        if args.json:
            continue

        if args.after_22:
            if result and result['after_22']:
                night_total = sum(v for k, v in result['after_22'].items() if k not in ('スリープ/放置', 'システム'))
                if night_total >= 60:
                    print(f"\n{date_str} 22時以降:")
                    print(f"  アクティブ合計: {format_duration(night_total)}")
                    for cat, dur in sorted(result['after_22'].items(), key=lambda x: -x[1]):
                        if dur >= 60 and cat not in ('スリープ/放置', 'システム'):
                            print(f"    {cat:28s} {format_duration(dur):>8s}")
                else:
                    print(f"\n{date_str}: 22時以降のアクティブPC使用なし")
            else:
                print(f"\n{date_str}: データなし")
        else:
            print_summary(result)

    if args.json:
        json_results = [result_to_dict(r) for r in results]
        print(json.dumps(json_results, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
