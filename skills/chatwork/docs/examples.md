# Chatwork API 実装例

## 認証設定

### 環境変数

```bash
export CHATWORK_API_TOKEN="your_api_token"
```

## Python実装例

### 基本クライアント

```python
import os
import requests
from typing import Optional, Dict, Any, List

class ChatworkClient:
    """Chatwork API クライアント"""

    BASE_URL = "https://api.chatwork.com/v2"

    def __init__(self, api_token: Optional[str] = None):
        self.api_token = api_token or os.environ.get("CHATWORK_API_TOKEN")
        if not self.api_token:
            raise ValueError("CHATWORK_API_TOKEN is required")

        self.headers = {
            "X-ChatWorkToken": self.api_token,
            "Content-Type": "application/x-www-form-urlencoded"
        }

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """APIリクエストを実行"""
        url = f"{self.BASE_URL}{endpoint}"
        response = requests.request(
            method=method,
            url=url,
            headers=self.headers,
            params=params,
            data=data
        )
        response.raise_for_status()
        return response.json() if response.text else {}

    # === ユーザー情報 ===

    def get_me(self) -> Dict:
        """自分のアカウント情報を取得"""
        return self._request("GET", "/me")

    def get_my_status(self) -> Dict:
        """未読数などのステータスを取得"""
        return self._request("GET", "/my/status")

    def get_my_tasks(self, assigned_by_account_id: Optional[int] = None, status: str = "open") -> List[Dict]:
        """自分のタスク一覧を取得"""
        params = {"status": status}
        if assigned_by_account_id:
            params["assigned_by_account_id"] = assigned_by_account_id
        return self._request("GET", "/my/tasks", params=params)

    # === コンタクト ===

    def get_contacts(self) -> List[Dict]:
        """コンタクト一覧を取得"""
        return self._request("GET", "/contacts")

    # === チャットルーム ===

    def get_rooms(self) -> List[Dict]:
        """参加しているルーム一覧を取得"""
        return self._request("GET", "/rooms")

    def create_room(
        self,
        name: str,
        members_admin_ids: List[int],
        members_member_ids: Optional[List[int]] = None,
        members_readonly_ids: Optional[List[int]] = None,
        description: str = "",
        icon_preset: str = "group"
    ) -> Dict:
        """グループチャットを作成"""
        data = {
            "name": name,
            "members_admin_ids": ",".join(map(str, members_admin_ids)),
            "description": description,
            "icon_preset": icon_preset
        }
        if members_member_ids:
            data["members_member_ids"] = ",".join(map(str, members_member_ids))
        if members_readonly_ids:
            data["members_readonly_ids"] = ",".join(map(str, members_readonly_ids))
        return self._request("POST", "/rooms", data=data)

    def get_room(self, room_id: int) -> Dict:
        """ルーム情報を取得"""
        return self._request("GET", f"/rooms/{room_id}")

    # === メッセージ ===

    def get_messages(self, room_id: int, force: bool = False) -> List[Dict]:
        """メッセージ一覧を取得"""
        params = {"force": 1 if force else 0}
        return self._request("GET", f"/rooms/{room_id}/messages", params=params)

    def send_message(self, room_id: int, body: str, self_unread: bool = False) -> Dict:
        """メッセージを送信"""
        data = {
            "body": body,
            "self_unread": 1 if self_unread else 0
        }
        return self._request("POST", f"/rooms/{room_id}/messages", data=data)

    def get_message(self, room_id: int, message_id: str) -> Dict:
        """特定のメッセージを取得"""
        return self._request("GET", f"/rooms/{room_id}/messages/{message_id}")

    def update_message(self, room_id: int, message_id: str, body: str) -> Dict:
        """メッセージを更新"""
        data = {"body": body}
        return self._request("PUT", f"/rooms/{room_id}/messages/{message_id}", data=data)

    def delete_message(self, room_id: int, message_id: str) -> Dict:
        """メッセージを削除"""
        return self._request("DELETE", f"/rooms/{room_id}/messages/{message_id}")

    # === タスク ===

    def get_tasks(
        self,
        room_id: int,
        account_id: Optional[int] = None,
        assigned_by_account_id: Optional[int] = None,
        status: str = "open"
    ) -> List[Dict]:
        """タスク一覧を取得"""
        params = {"status": status}
        if account_id:
            params["account_id"] = account_id
        if assigned_by_account_id:
            params["assigned_by_account_id"] = assigned_by_account_id
        return self._request("GET", f"/rooms/{room_id}/tasks", params=params)

    def create_task(
        self,
        room_id: int,
        body: str,
        to_ids: List[int],
        limit: Optional[int] = None,
        limit_type: str = "none"
    ) -> Dict:
        """タスクを作成"""
        data = {
            "body": body,
            "to_ids": ",".join(map(str, to_ids)),
            "limit_type": limit_type
        }
        if limit:
            data["limit"] = limit
        return self._request("POST", f"/rooms/{room_id}/tasks", data=data)

    def update_task_status(self, room_id: int, task_id: int, status: str = "done") -> Dict:
        """タスクのステータスを更新"""
        data = {"body": status}
        return self._request("PUT", f"/rooms/{room_id}/tasks/{task_id}/status", data=data)

    # === メンバー ===

    def get_members(self, room_id: int) -> List[Dict]:
        """ルームメンバー一覧を取得"""
        return self._request("GET", f"/rooms/{room_id}/members")


# === 使用例 ===

if __name__ == "__main__":
    client = ChatworkClient()

    # 自分の情報を取得
    me = client.get_me()
    print(f"ログインユーザー: {me['name']}")

    # ルーム一覧を取得
    rooms = client.get_rooms()
    for room in rooms[:5]:
        print(f"- {room['name']} (ID: {room['room_id']})")

    # メッセージ送信
    # room_id = 123456789
    # client.send_message(room_id, "[info]テストメッセージ[/info]")
```

### 通知Bot関数

```python
def notify_chatwork(
    room_id: int,
    message: str,
    title: Optional[str] = None,
    mention_ids: Optional[List[int]] = None,
    api_token: Optional[str] = None
) -> bool:
    """Chatworkに通知を送信するシンプルな関数"""
    import os
    import requests

    token = api_token or os.environ.get("CHATWORK_API_TOKEN")
    if not token:
        raise ValueError("CHATWORK_API_TOKEN is required")

    # メッセージ組み立て
    body_parts = []

    # メンション追加
    if mention_ids:
        mentions = " ".join([f"[To:{uid}]" for uid in mention_ids])
        body_parts.append(mentions)

    # 本文（タイトル付きinfoブロック）
    if title:
        body_parts.append(f"[info][title]{title}[/title]{message}[/info]")
    else:
        body_parts.append(f"[info]{message}[/info]")

    body = "\n".join(body_parts)

    # API呼び出し
    response = requests.post(
        f"https://api.chatwork.com/v2/rooms/{room_id}/messages",
        headers={"X-ChatWorkToken": token},
        data={"body": body}
    )

    return response.status_code == 200


# 使用例
# notify_chatwork(
#     room_id=123456789,
#     message="デプロイが完了しました",
#     title="デプロイ通知",
#     mention_ids=[111111, 222222]
# )
```

### エラー通知

```python
import traceback
from functools import wraps

def chatwork_error_notify(room_id: int, title: str = "エラー通知"):
    """例外発生時にChatworkに通知するデコレータ"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_message = f"関数: {func.__name__}\nエラー: {str(e)}\n\n[code]{traceback.format_exc()}[/code]"
                notify_chatwork(room_id, error_message, title=title)
                raise
        return wrapper
    return decorator


# 使用例
# @chatwork_error_notify(room_id=123456789, title="バッチ処理エラー")
# def my_batch_job():
#     # 処理
#     pass
```

## cURLコマンド例

### メッセージ送信

```bash
curl -X POST \
  -H "X-ChatWorkToken: ${CHATWORK_API_TOKEN}" \
  -d "body=[info]テストメッセージ[/info]" \
  "https://api.chatwork.com/v2/rooms/${ROOM_ID}/messages"
```

### ルーム一覧取得

```bash
curl -X GET \
  -H "X-ChatWorkToken: ${CHATWORK_API_TOKEN}" \
  "https://api.chatwork.com/v2/rooms"
```

### タスク作成

```bash
curl -X POST \
  -H "X-ChatWorkToken: ${CHATWORK_API_TOKEN}" \
  -d "body=タスクの内容&to_ids=123456,789012&limit_type=date&limit=1735689600" \
  "https://api.chatwork.com/v2/rooms/${ROOM_ID}/tasks"
```
