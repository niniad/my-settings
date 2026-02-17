import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
import argparse
import json
import csv
from googleapiclient.discovery import build

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from auth import get_google_creds


def extract_spreadsheet_id(raw_id):
    """URLまたはIDからスプレッドシートIDを抽出"""
    if 'docs.google.com/spreadsheets' in raw_id:
        try:
            start = raw_id.find('/d/') + 3
            end = raw_id.find('/edit')
            if end != -1:
                return raw_id[start:end]
            remaining = raw_id[start:]
            return remaining.split('/')[0] if '/' in remaining else remaining
        except Exception:
            pass
    return raw_id


def cmd_update(service, spreadsheet_id, range_, values, input_option):
    """セル値を上書き更新"""
    body = {'values': values}
    result = service.spreadsheets().values().update(
        spreadsheetId=spreadsheet_id,
        range=range_,
        valueInputOption=input_option,
        body=body
    ).execute()
    print(f"更新完了: {result.get('updatedCells', 0)} セル")


def cmd_append(service, spreadsheet_id, range_, values, input_option):
    """末尾に行を追記"""
    body = {'values': values}
    result = service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range=range_,
        valueInputOption=input_option,
        body=body
    ).execute()
    updates = result.get('updates', {})
    print(f"追記完了: {updates.get('updatedRows', 0)} 行 ({updates.get('updatedRange', '')})")


def cmd_clear(service, spreadsheet_id, range_):
    """指定範囲のセル値をクリア"""
    service.spreadsheets().values().clear(
        spreadsheetId=spreadsheet_id,
        range=range_,
        body={}
    ).execute()
    print(f"クリア完了: {range_}")


def cmd_add_sheet(service, spreadsheet_id, title):
    """新しいシートを追加"""
    body = {
        'requests': [{
            'addSheet': {
                'properties': {'title': title}
            }
        }]
    }
    result = service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id, body=body
    ).execute()
    sheet_id = result['replies'][0]['addSheet']['properties']['sheetId']
    print(f"シート追加完了: '{title}' (ID: {sheet_id})")


def cmd_delete_sheet(service, spreadsheet_id, sheet_id):
    """シートを削除"""
    body = {
        'requests': [{
            'deleteSheet': {'sheetId': int(sheet_id)}
        }]
    }
    service.spreadsheets().batchUpdate(
        spreadsheetId=spreadsheet_id, body=body
    ).execute()
    print(f"シート削除完了: ID {sheet_id}")


def parse_values(values_str):
    """JSON文字列またはCSV文字列から2D配列を生成"""
    try:
        parsed = json.loads(values_str)
        if isinstance(parsed, list):
            if parsed and isinstance(parsed[0], list):
                return parsed
            return [parsed]
    except (json.JSONDecodeError, TypeError):
        pass
    # CSV形式: "a,b,c;d,e,f" → [["a","b","c"],["d","e","f"]]
    rows = values_str.split(';')
    return [row.split(',') for row in rows]


def main():
    parser = argparse.ArgumentParser(description='Google Sheets 書き込み操作')
    parser.add_argument('--spreadsheet_id', required=True, help='スプレッドシートID または URL')
    sub = parser.add_subparsers(dest='command', required=True)

    # update
    p_update = sub.add_parser('update', help='セル値を上書き更新')
    p_update.add_argument('--range', required=True, help='対象範囲 (例: Sheet1!A1:C3)')
    p_update.add_argument('--values', required=True, help='値 (JSON配列 or CSV形式 "a,b;c,d")')
    p_update.add_argument('--raw', action='store_true', help='値をそのまま入力 (デフォルトは数式等を解釈)')

    # append
    p_append = sub.add_parser('append', help='末尾に行を追記')
    p_append.add_argument('--range', required=True, help='対象シート範囲 (例: Sheet1!A:E)')
    p_append.add_argument('--values', required=True, help='値 (JSON配列 or CSV形式 "a,b;c,d")')
    p_append.add_argument('--raw', action='store_true', help='値をそのまま入力')

    # clear
    p_clear = sub.add_parser('clear', help='指定範囲をクリア')
    p_clear.add_argument('--range', required=True, help='対象範囲 (例: Sheet1!A1:C10)')

    # add-sheet
    p_add = sub.add_parser('add-sheet', help='新しいシートを追加')
    p_add.add_argument('--title', required=True, help='シート名')

    # delete-sheet
    p_del = sub.add_parser('delete-sheet', help='シートを削除')
    p_del.add_argument('--sheet_id', required=True, help='シートID (read_sheet.py --info で確認)')

    args = parser.parse_args()

    creds = get_google_creds()
    if not creds:
        print("Error: 認証情報がありません。'python scripts/auth.py' を実行してください。")
        return

    service = build('sheets', 'v4', credentials=creds)
    spreadsheet_id = extract_spreadsheet_id(args.spreadsheet_id)

    if args.command == 'update':
        values = parse_values(args.values)
        input_option = 'RAW' if args.raw else 'USER_ENTERED'
        cmd_update(service, spreadsheet_id, args.range, values, input_option)

    elif args.command == 'append':
        values = parse_values(args.values)
        input_option = 'RAW' if args.raw else 'USER_ENTERED'
        cmd_append(service, spreadsheet_id, args.range, values, input_option)

    elif args.command == 'clear':
        cmd_clear(service, spreadsheet_id, args.range)

    elif args.command == 'add-sheet':
        cmd_add_sheet(service, spreadsheet_id, args.title)

    elif args.command == 'delete-sheet':
        cmd_delete_sheet(service, spreadsheet_id, args.sheet_id)


if __name__ == '__main__':
    main()
