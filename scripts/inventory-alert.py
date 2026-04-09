"""在庫アラート自動チェック

BigQuery rpt_inventory_health から在庫残日数を取得し、
発注ポイント以下の商品があればTodoistにタスクを作成する。
週次（月曜朝）にタスクスケジューラから実行。

実行: uv run --with google-cloud-bigquery python inventory-alert.py
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import datetime
import json
import urllib.request
from google.cloud import bigquery

# --- 設定 ---
BQ_PROJECT = "main-project-477501"

# 廃盤確定SKU（発注不要）
DISCONTINUED_SKUS = {
    "YS-JYMD-1J2N",  # てんとう虫
    "NW-X3TX-EPK3",  # 恐竜B
    "FB-0OA0-F0XQ",  # うさぎ・旧
    "2C-D461-YTO0",  # ユニコーン・旧
}

# 廃盤検討中（発注不要）
PHASE_OUT_SKUS = {
    "O8-80TH-VH3Y",  # 無地・赤
}

# 発注ポイント（残日数がこれ以下なら発注必要）
REORDER_POINTS = {
    "normal": {"default": 70, "rucksack": 90},
    "cny": {"default": 100, "rucksack": 115},
}

RUCKSACK_SKUS = {"XC-WB7S-6C88", "UO-ZW0F-XSMT"}


def get_todoist_token():
    """環境変数 TODOIST_API_TOKEN から取得（タスクスケジューラで設定）"""
    import os
    token = os.environ.get("TODOIST_API_TOKEN")
    if not token:
        raise RuntimeError("TODOIST_API_TOKEN environment variable not set")
    return token


def get_reorder_point(sku):
    month = datetime.date.today().month
    period = "cny" if month in (11, 12, 1) else "normal"
    category = "rucksack" if sku in RUCKSACK_SKUS else "default"
    return REORDER_POINTS[period][category]


def create_todoist_task(token, content, description):
    url = "https://api.todoist.com/api/v1/tasks"
    data = json.dumps({
        "content": content,
        "description": description,
        "labels": ["ec"],
        "priority": 3,
    }).encode("utf-8")

    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")

    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    client = bigquery.Client(project=BQ_PROJECT)

    # データ鮮度チェック
    freshness = list(client.query("""
        SELECT
          MAX(report_date) as latest_date,
          DATE_DIFF(CURRENT_DATE(), MAX(report_date), DAY) as days_stale
        FROM `main-project-477501.analytics.fact_daily_asin`
    """).result())

    latest_date = str(freshness[0].latest_date) if freshness else "不明"
    days_stale = freshness[0].days_stale if freshness else 99

    if days_stale > 3:
        print(f"⚠ データが{days_stale}日古い（最終: {latest_date}）。アラートをスキップ。")
        return

    # 在庫データ取得
    rows = list(client.query("""
        SELECT
          seller_sku,
          product_name,
          fulfillable_quantity,
          inbound_working_quantity + inbound_shipped_quantity + inbound_receiving_quantity as inbound_total,
          units_sold_30d,
          ROUND(avg_daily_units, 2) as avg_daily_units,
          ROUND(days_until_stockout, 0) as days_until_stockout,
          stock_status
        FROM `main-project-477501.analytics.rpt_inventory_health`
        WHERE product_name LIKE '%Ufa%'
        ORDER BY days_until_stockout ASC NULLS LAST
    """).result())

    if not rows:
        print("在庫データなし")
        return

    # 発注必要な商品を検出
    alerts = []
    for row in rows:
        sku = row.seller_sku
        if sku in DISCONTINUED_SKUS or sku in PHASE_OUT_SKUS:
            continue

        days_left = row.days_until_stockout
        if days_left is None:
            continue
        days_left = float(days_left)

        inbound = int(row.inbound_total or 0)
        fulfillable = int(row.fulfillable_quantity or 0)
        avg_daily = float(row.avg_daily_units or 0)

        # inbound考慮した実質残日数
        if avg_daily > 0 and inbound > 0:
            effective_days = (fulfillable + inbound) / avg_daily
        else:
            effective_days = days_left

        reorder_point = get_reorder_point(sku)

        if effective_days < reorder_point and inbound == 0:
            alerts.append({
                "sku": sku,
                "name": row.product_name,
                "days_left": days_left,
                "reorder_point": reorder_point,
                "avg_daily": avg_daily,
                "fulfillable": fulfillable,
            })

    if not alerts:
        print("✅ 発注が必要な商品はありません")
        return

    # Todoistにタスクを作成
    todoist_token = get_todoist_token()

    desc_lines = []
    for a in alerts:
        desc_lines.append(
            f"- {a['name']}（{a['sku']}）: 残{a['days_left']:.0f}日 "
            f"（発注ポイント: {a['reorder_point']}日、日販: {a['avg_daily']:.1f}個）"
        )

    description = "\n".join(desc_lines)
    description += f"\n\nデータ鮮度: {latest_date}"
    description += "\n\n`/inventory-check` で詳細確認・発注数計算"

    content = f"🔴 在庫アラート: {len(alerts)}商品が発注ポイント以下"
    task = create_todoist_task(todoist_token, content, description)
    print(f"✅ Todoistタスク作成: {task['id']} - {content}")
    print(description)


if __name__ == "__main__":
    main()
