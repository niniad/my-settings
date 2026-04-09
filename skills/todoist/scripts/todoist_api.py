"""Todoist REST API v1 ラッパー

Usage:
  uv run python todoist_api.py list [--filter FILTER] [--label LABEL]
  uv run python todoist_api.py get TASK_ID
  uv run python todoist_api.py create CONTENT [--desc DESC] [--due DUE] [--label LABEL] [--priority 1-4]
  uv run python todoist_api.py update TASK_ID [--content CONTENT] [--desc DESC] [--due DUE] [--label LABEL]
  uv run python todoist_api.py complete TASK_ID
  uv run python todoist_api.py delete TASK_ID

環境変数 TODOIST_API_TOKEN が必要。未設定の場合は GCP Secret Manager から取得を試みる。
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

import argparse
import json
import os
import subprocess
import urllib.request
import urllib.parse
import urllib.error

BASE_URL = "https://api.todoist.com/api/v1"


def get_token():
    token = os.environ.get("TODOIST_API_TOKEN")
    if token:
        return token
    # Fallback: GCP Secret Manager
    try:
        result = subprocess.run(
            ["gcloud", "secrets", "versions", "access", "latest",
             "--secret=todoist-api-token", "--project=main-project-477501"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    print("ERROR: TODOIST_API_TOKEN not set and GCP Secret Manager unavailable", file=sys.stderr)
    sys.exit(1)


def api_request(method, endpoint, data=None, params=None):
    token = get_token()
    url = f"{BASE_URL}/{endpoint}"
    if params:
        url += "?" + urllib.parse.urlencode(params)

    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    if body:
        req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req) as resp:
            if resp.status == 204:
                return None
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8") if e.fp else ""
        print(f"HTTP {e.code}: {error_body}", file=sys.stderr)
        sys.exit(1)


def format_task(task):
    lines = [f"- {task.get('content', '(no title)')} (ID: {task['id']})"]
    if task.get('description'):
        lines.append(f"  Description: {task['description'][:200]}")
    if task.get('due'):
        due = task['due']
        lines.append(f"  Due: {due.get('date', '')} {due.get('string', '')}")
    if task.get('labels'):
        lines.append(f"  Labels: {', '.join(task['labels'])}")
    pri = task.get('priority', 1)
    if pri > 1:
        lines.append(f"  Priority: {pri}")
    return "\n".join(lines)


def cmd_list(args):
    params = {}
    if args.filter:
        # Use filter endpoint
        data = {"query": args.filter}
        result = api_request("POST", "tasks/filter", data=data)
    else:
        result = api_request("GET", "tasks", params=params)

    # API v1 returns {"results": [...]} or a list
    if isinstance(result, dict):
        tasks = result.get("results", result.get("items", []))
    else:
        tasks = result

    if args.label:
        tasks = [t for t in tasks if args.label in t.get("labels", [])]

    if not tasks:
        print("タスクなし")
        return

    print(f"{len(tasks)} tasks:\n")
    for task in tasks:
        print(format_task(task))
        print()


def cmd_get(args):
    task = api_request("GET", f"tasks/{args.task_id}")
    print(format_task(task))


def cmd_create(args):
    data = {"content": args.content}
    if args.desc:
        data["description"] = args.desc
    if args.due:
        data["due_string"] = args.due
    if args.label:
        data["labels"] = args.label if isinstance(args.label, list) else [args.label]
    if args.priority:
        data["priority"] = args.priority

    task = api_request("POST", "tasks", data=data)
    print(f"Created: {format_task(task)}")


def cmd_update(args):
    data = {}
    if args.content:
        data["content"] = args.content
    if args.desc:
        data["description"] = args.desc
    if args.due:
        data["due_string"] = args.due
    if args.label:
        data["labels"] = args.label if isinstance(args.label, list) else [args.label]

    if not data:
        print("Nothing to update", file=sys.stderr)
        return

    task = api_request("POST", f"tasks/{args.task_id}", data=data)
    print(f"Updated: {format_task(task)}")


def cmd_complete(args):
    api_request("POST", f"tasks/{args.task_id}/close")
    print(f"Completed: {args.task_id}")


def cmd_delete(args):
    api_request("DELETE", f"tasks/{args.task_id}")
    print(f"Deleted: {args.task_id}")


def main():
    parser = argparse.ArgumentParser(description="Todoist CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    # list
    p_list = sub.add_parser("list")
    p_list.add_argument("--filter", "-f", help="Todoist filter query")
    p_list.add_argument("--label", "-l", help="Filter by label name")

    # get
    p_get = sub.add_parser("get")
    p_get.add_argument("task_id")

    # create
    p_create = sub.add_parser("create")
    p_create.add_argument("content")
    p_create.add_argument("--desc", "-d")
    p_create.add_argument("--due")
    p_create.add_argument("--label", "-l", action="append")
    p_create.add_argument("--priority", "-p", type=int, choices=[1, 2, 3, 4])

    # update
    p_update = sub.add_parser("update")
    p_update.add_argument("task_id")
    p_update.add_argument("--content", "-c")
    p_update.add_argument("--desc", "-d")
    p_update.add_argument("--due")
    p_update.add_argument("--label", "-l", action="append")

    # complete
    p_complete = sub.add_parser("complete")
    p_complete.add_argument("task_id")

    # delete
    p_delete = sub.add_parser("delete")
    p_delete.add_argument("task_id")

    args = parser.parse_args()

    commands = {
        "list": cmd_list,
        "get": cmd_get,
        "create": cmd_create,
        "update": cmd_update,
        "complete": cmd_complete,
        "delete": cmd_delete,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
