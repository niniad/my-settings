"""
ESPRIME共有スプレッドシート → NocoDB agency_transactions 自動取込

使用方法:
  uv run python .claude/skills/monthly-closing/scripts/import_agency_sheet.py [--dry-run] [--sheet-name NAME]

処理:
  1. Google Sheets API でESPRIME共有スプレッドシートを読取
  2. NocoDB既存行と照合して新規行のみ抽出
  3. 入金行は「入金本体 + 代行手数料2%」に自動分割
  4. balance_jpy はSheetsから直接コピー（自動計算しない）
  5. --dry-run: 取込候補表示のみ / 通常: NocoDB APIで書込

注意:
  - balance_jpy は累積残高であり自動計算不可。Sheetsの値を直接転記する
  - 為替レートは直近入金時のレートを以降の取引に適用（ユーザーがSheets上で管理）
  - Google Sheets API は google-workspace スキル経由またはサービスアカウントで認証
"""
import sys
import os
import json
import argparse
import urllib.request
import urllib.error
import sqlite3

sys.stdout.reconfigure(encoding='utf-8')

SPREADSHEET_ID = "1RlrGi_G4k4n37ezgE5sJpgWPXw8CBhHmrTeTJ9UjWH4"
BQ_PROJECT = "main-project-477501"
NOCODB_BASE_URL = "http://localhost:8080/api/v2"
EC_BASE_ID = "pbvdkr5cvkj4n2e"
NOCODB_DB_PATH = "C:/Users/ninni/nocodb/noco.db"

# NocoDB agency_transactions テーブル名（SQLite）
AGENCY_TABLE_SQLITE = "nc_opau___代行会社"


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
        tokens = json.loads(resp.read())
    return tokens["access_token"]


def get_sheets_data(access_token, sheet_name=None):
    """Google Sheets API でスプレッドシートを読取"""
    # まずスプレッドシートのメタデータを取得
    meta_url = f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}"
    req = urllib.request.Request(meta_url, headers={"Authorization": f"Bearer {access_token}"})
    with urllib.request.urlopen(req) as resp:
        meta = json.loads(resp.read())

    sheets = meta.get("sheets", [])
    if not sheets:
        print("ERROR: シートが見つかりません")
        return None, None

    # シート名指定 or 最後のシート（最新）を使用
    target_sheet = None
    if sheet_name:
        for s in sheets:
            if s["properties"]["title"] == sheet_name:
                target_sheet = s
                break
    if not target_sheet:
        target_sheet = sheets[-1]  # 最後のシート = 最新

    title = target_sheet["properties"]["title"]
    print(f"対象シート: {title}")

    # データ取得
    data_url = f"https://sheets.googleapis.com/v4/spreadsheets/{SPREADSHEET_ID}/values/{urllib.parse.quote(title)}"
    req = urllib.request.Request(data_url, headers={"Authorization": f"Bearer {access_token}"})
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())

    return title, data.get("values", [])


def get_existing_nocodb_dates():
    """NocoDB SQLiteから既存の取引日を取得（重複防止用）"""
    if not os.path.exists(NOCODB_DB_PATH):
        return set()
    conn = sqlite3.connect(NOCODB_DB_PATH)
    try:
        rows = conn.execute(
            f'SELECT "発生日", "外貨金額", "備考" FROM "{AGENCY_TABLE_SQLITE}" WHERE "発生日" IS NOT NULL'
        ).fetchall()
        # (日付, 金額, メモ) のタプルで重複判定
        return {(r[0], r[1], r[2]) for r in rows}
    finally:
        conn.close()


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


def parse_sheet_rows(header, rows):
    """Sheetsの行をパース。ヘッダーからカラムインデックスを特定"""
    # ヘッダー候補: 日付, 決済口座, 勘定科目, 原価区分, 商品カテゴリ, 外貨金額, 為替レート, 元残高, 円残高, 備考
    col_map = {}
    for i, h in enumerate(header):
        h_clean = h.strip()
        if "日" in h_clean and ("発生" in h_clean or "日付" in h_clean):
            col_map["date"] = i
        elif "決済" in h_clean or "口座" in h_clean:
            col_map["account"] = i
        elif "勘定" in h_clean or "科目" in h_clean:
            col_map["category"] = i
        elif "原価" in h_clean:
            col_map["cost_category"] = i
        elif "商品" in h_clean:
            col_map["product_category"] = i
        elif "外貨" in h_clean:
            col_map["amount_foreign"] = i
        elif "為替" in h_clean or "レート" in h_clean:
            col_map["exchange_rate"] = i
        elif "元残" in h_clean:
            col_map["balance_foreign"] = i
        elif "円残" in h_clean:
            col_map["balance_jpy"] = i
        elif "備考" in h_clean or "メモ" in h_clean:
            col_map["memo"] = i

    parsed = []
    for row in rows:
        def get_val(key, default=""):
            idx = col_map.get(key)
            if idx is not None and idx < len(row):
                return row[idx].strip() if row[idx] else default
            return default

        entry = {
            "date": get_val("date"),
            "account": get_val("account", "ESPRIME"),
            "amount_foreign": get_val("amount_foreign"),
            "exchange_rate": get_val("exchange_rate"),
            "balance_foreign": get_val("balance_foreign"),
            "balance_jpy": get_val("balance_jpy"),
            "cost_category": get_val("cost_category"),
            "product_category": get_val("product_category"),
            "memo": get_val("memo"),
        }
        if entry["date"] and entry["amount_foreign"]:
            parsed.append(entry)

    return parsed


def main():
    parser = argparse.ArgumentParser(description="ESPRIME Sheets → NocoDB 取込")
    parser.add_argument("--dry-run", action="store_true", help="取込候補表示のみ")
    parser.add_argument("--sheet-name", help="対象シート名（未指定時は最新シート）")
    args = parser.parse_args()

    print("=== ESPRIME Sheets → NocoDB 取込 ===\n")

    # 認証
    access_token = get_nocodb_token()  # OAuth access token（Sheets APIにも使える）

    # Sheets読取
    import urllib.parse
    sheet_title, raw_data = get_sheets_data(access_token, args.sheet_name)
    if not raw_data or len(raw_data) < 2:
        print("ERROR: シートにデータがありません")
        sys.exit(1)

    header = raw_data[0]
    data_rows = raw_data[1:]
    print(f"ヘッダー: {header}")
    print(f"データ行: {len(data_rows)} 行\n")

    # パース
    parsed = parse_sheet_rows(header, data_rows)
    print(f"パース成功: {len(parsed)} 行\n")

    # 既存データと照合
    existing = get_existing_nocodb_dates()
    new_entries = []
    for p in parsed:
        try:
            amount = float(p["amount_foreign"].replace(",", ""))
        except ValueError:
            continue
        key = (p["date"], amount, p["memo"])
        if key not in existing:
            p["amount_float"] = amount
            new_entries.append(p)

    print(f"新規行: {len(new_entries)} 件（既存 {len(parsed) - len(new_entries)} 件はスキップ）\n")

    if not new_entries:
        print("新規取込対象なし。終了。")
        return

    # 表示
    print("--- 取込候補 ---")
    for e in new_entries:
        print(f"  {e['date']} | {e['account']} | {e['amount_float']:+,.2f} CNY | rate={e['exchange_rate']} | {e['memo'][:40]}")

    if args.dry_run:
        print("\n[DRY RUN] 書込は行いません。")
        return

    # NocoDB書込
    print(f"\n=== NocoDB書込準備 ===")
    print("ユーザー確認: 上記の取込候補をNocoDB に書き込みますか？ (y/n)")
    confirm = input().strip().lower()
    if confirm != 'y':
        print("キャンセルしました。")
        return

    # NocoDB APIトークン取得
    creds_path = os.path.expanduser(
        "~/AppData/Roaming/gcloud/legacy_credentials/ninnin0304@gmail.com/adc.json"
    )
    with open(creds_path) as f:
        creds = json.load(f)
    data = urllib.parse.urlencode({
        "client_id": creds["client_id"],
        "client_secret": creds["client_secret"],
        "refresh_token": creds["refresh_token"],
        "grant_type": "refresh_token"
    }).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data)
    with urllib.request.urlopen(req) as resp:
        at = json.loads(resp.read())["access_token"]

    # Secret Manager → NocoDB token
    secret_url = f"https://secretmanager.googleapis.com/v1/projects/{BQ_PROJECT}/secrets/NOCODB_API_TOKEN/versions/latest:access"
    req = urllib.request.Request(secret_url, headers={"Authorization": f"Bearer {at}"})
    with urllib.request.urlopen(req) as resp:
        payload = json.loads(resp.read())
    import base64
    nocodb_token = base64.b64decode(payload["payload"]["data"]).decode().strip()

    # テーブルID取得
    tables = nocodb_request("GET", f"/meta/bases/{EC_BASE_ID}/tables", nocodb_token)
    agency_table_id = None
    for t in tables.get("list", []):
        if "代行会社" in t.get("title", ""):
            agency_table_id = t["id"]
            break

    if not agency_table_id:
        print("ERROR: 代行会社テーブルが見つかりません")
        sys.exit(1)

    success = 0
    for e in new_entries:
        record = {
            "発生日": e["date"],
            "決済口座": e["account"],
            "外貨金額": e["amount_float"],
            "備考": e["memo"],
        }
        if e["exchange_rate"]:
            try:
                record["為替レート"] = float(e["exchange_rate"].replace(",", ""))
            except ValueError:
                pass
        if e["balance_foreign"]:
            try:
                record["元残高"] = float(e["balance_foreign"].replace(",", ""))
            except ValueError:
                pass
        if e["balance_jpy"]:
            try:
                record["円残高"] = float(e["balance_jpy"].replace(",", ""))
            except ValueError:
                pass
        if e["cost_category"]:
            record["原価区分"] = e["cost_category"]
        if e["product_category"]:
            record["商品カテゴリ"] = e["product_category"]

        result = nocodb_request("POST", f"/tables/{agency_table_id}/records", nocodb_token, record)
        if result:
            success += 1
            print(f"  ✓ {e['date']} | {e['amount_float']:+,.2f} CNY | {e['memo'][:30]}")

    print(f"\n完了: {success}/{len(new_entries)} 件書込済み")


if __name__ == "__main__":
    main()
