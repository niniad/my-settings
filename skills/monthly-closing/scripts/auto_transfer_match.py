"""
振替自動マッチスクリプト: PayPay Amazon入金 ↔ Settlement金額を照合

使用方法:
  uv run --with google-cloud-bigquery python .claude/skills/monthly-closing/scripts/auto_transfer_match.py [--dry-run]

処理:
  1. BQから未リンクPayPay Amazon入金（freee勘定科目_id=9, 振替_id IS NULL）を取得
  2. BQから settlement_journal_view の net_amount_check を取得
  3. 金額一致でペアマッチ
  4. --dry-run: マッチ候補表示のみ / 通常: NocoDB APIで transfer_records 作成 + 振替_id 更新
"""
import sys
import os
import json
import argparse
import urllib.request
import urllib.error

sys.stdout.reconfigure(encoding='utf-8')

BQ_PROJECT = "main-project-477501"
NOCODB_BASE_URL = "http://localhost:8080/api/v2"
EC_BASE_ID = "pbvdkr5cvkj4n2e"


def get_nocodb_token():
    """GCP Secret Manager から NocoDB APIトークンを取得"""
    creds_path = os.path.expanduser(
        "~/AppData/Roaming/gcloud/legacy_credentials/ninnin0304@gmail.com/adc.json"
    )
    with open(creds_path) as f:
        creds = json.load(f)
    import urllib.parse
    data = urllib.parse.urlencode({
        "client_id": creds["client_id"],
        "client_secret": creds["client_secret"],
        "refresh_token": creds["refresh_token"],
        "grant_type": "refresh_token"
    }).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data)
    with urllib.request.urlopen(req) as resp:
        access_token = json.loads(resp.read())["access_token"]
    secret_url = (
        f"https://secretmanager.googleapis.com/v1/projects/{BQ_PROJECT}"
        f"/secrets/NOCODB_API_TOKEN/versions/latest:access"
    )
    req = urllib.request.Request(secret_url, headers={"Authorization": f"Bearer {access_token}"})
    with urllib.request.urlopen(req) as resp:
        payload = json.loads(resp.read())
    import base64
    return base64.b64decode(payload["payload"]["data"]).decode().strip()


def bq_query(sql):
    """BQ REST API でクエリ実行（google-cloud-bigquery不要版）"""
    from google.cloud import bigquery
    client = bigquery.Client(project=BQ_PROJECT)
    return list(client.query(sql).result())


def nocodb_request(method, path, token, data=None):
    url = f"{NOCODB_BASE_URL}{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method, headers={
        "xc-token": token,
        "Content-Type": "application/json"
    })
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"  API Error {e.code}: {e.read().decode()}")
        return None


def main():
    parser = argparse.ArgumentParser(description="振替自動マッチ")
    parser.add_argument("--dry-run", action="store_true", help="マッチ候補表示のみ")
    args = parser.parse_args()

    print("=== 振替自動マッチ ===\n")

    # 1. 未リンクPayPay Amazon入金を取得
    print("1. 未リンクPayPay Amazon入金を検索...")
    unlinked_paypay = bq_query("""
        SELECT nocodb_id, transaction_date, amount, description
        FROM `main-project-477501.nocodb.paypay_bank_statements`
        WHERE CAST(freee勘定科目_id AS INT64) = 9
          AND 振替_id IS NULL
          AND amount > 0
        ORDER BY transaction_date
    """)
    print(f"   → {len(unlinked_paypay)} 件の未リンク入金\n")

    if not unlinked_paypay:
        print("未リンク入金なし。振替マッチ不要。")
        return

    # 2. Settlement deposit金額を取得
    print("2. Settlement入金額を検索...")
    settlements = bq_query("""
        SELECT settlement_id, DATE(booking_date) as booking_date,
          CAST(net_amount_check AS INT64) as net_amount
        FROM `main-project-477501.accounting.settlement_journal_view`
        ORDER BY booking_date
    """)
    print(f"   → {len(settlements)} 件のSettlement\n")

    # 3. 金額マッチング
    print("3. 金額マッチング...\n")
    matched = []
    unmatched_paypay = []
    used_settlements = set()

    for pp in unlinked_paypay:
        pp_amount = pp.amount
        pp_date = str(pp.transaction_date)
        found = False
        for st in settlements:
            if st.settlement_id in used_settlements:
                continue
            # 金額完全一致 + 日付が近い（Settlement→PayPay入金は同日か1日差）
            if st.net_amount == pp_amount:
                matched.append({
                    "paypay_id": pp.nocodb_id,
                    "paypay_date": pp_date,
                    "paypay_amount": pp_amount,
                    "paypay_desc": pp.description,
                    "settlement_id": st.settlement_id,
                    "settlement_date": str(st.booking_date),
                    "settlement_amount": st.net_amount,
                })
                used_settlements.add(st.settlement_id)
                found = True
                break
        if not found:
            unmatched_paypay.append({
                "nocodb_id": pp.nocodb_id,
                "date": pp_date,
                "amount": pp_amount,
                "description": pp.description,
            })

    # 結果表示
    print(f"=== マッチ結果 ===")
    print(f"  マッチ成功: {len(matched)} 件")
    print(f"  マッチ不可: {len(unmatched_paypay)} 件\n")

    if matched:
        print("--- マッチペア ---")
        for m in matched:
            print(f"  PayPay #{m['paypay_id']} ({m['paypay_date']}) ¥{m['paypay_amount']:,}")
            print(f"    ↔ Settlement {m['settlement_id']} ({m['settlement_date']}) ¥{m['settlement_amount']:,}")

    if unmatched_paypay:
        print("\n--- マッチ不可（手動確認要） ---")
        for u in unmatched_paypay:
            print(f"  PayPay #{u['nocodb_id']} ({u['date']}) ¥{u['amount']:,} - {u['description']}")

    if args.dry_run:
        print("\n[DRY RUN] 書込は行いません。")
        return

    if not matched:
        print("\nマッチペアなし。終了。")
        return

    # 4. NocoDB書込
    print(f"\n=== NocoDB書込 ({len(matched)} 件) ===")
    token = get_nocodb_token()

    # 振替テーブルID取得
    tables = nocodb_request("GET", f"/meta/bases/{EC_BASE_ID}/tables", token)
    transfer_table_id = None
    paypay_table_id = None
    for t in tables.get("list", []):
        title = t.get("title", "")
        if "振替" in title and "ビュー" not in title:
            transfer_table_id = t["id"]
        if "PayPay" in title:
            paypay_table_id = t["id"]

    if not transfer_table_id or not paypay_table_id:
        print("ERROR: テーブルIDが取得できません")
        sys.exit(1)

    success = 0
    for m in matched:
        # 振替レコード作成
        transfer = nocodb_request("POST", f"/tables/{transfer_table_id}/records", token, {
            "振替日": m["paypay_date"],
            "金額": m["paypay_amount"],
            "メモ": f"Amazon Settlement {m['settlement_id']}",
        })
        if not transfer:
            continue

        transfer_id = transfer.get("Id") or transfer.get("id")

        # PayPay側の振替_id更新
        nocodb_request("PATCH", f"/tables/{paypay_table_id}/records", token, {
            "Id": m["paypay_id"],
            "振替": transfer_id,
        })
        success += 1
        print(f"  ✓ PayPay #{m['paypay_id']} ↔ Settlement {m['settlement_id']} (振替#{transfer_id})")

    print(f"\n完了: {success}/{len(matched)} 件リンク済み")


if __name__ == "__main__":
    main()
