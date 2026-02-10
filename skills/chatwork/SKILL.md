---
name: chatwork
description: Chatwork APIの開発支援。メッセージ送信、チャットルーム管理、タスク管理、ファイル操作などをサポート。APIトークン認証でシンプルに利用可能。
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - Write
---

# Chatwork API 開発支援

## 概要

Chatwork APIを使用したアプリケーション開発を支援します。

## API基本情報

| 項目 | 値 |
|------|-----|
| ベースURL | `https://api.chatwork.com/v2` |
| 認証方式 | APIトークン（ヘッダー） |
| レスポンス形式 | JSON |
| レート制限 | 300リクエスト/5分 |

## 認証

リクエストヘッダーにAPIトークンを含める：
```
X-ChatWorkToken: your_api_token
```

APIトークンは [Chatwork設定 > API発行](https://www.chatwork.com/service/packages/chatwork/subpackages/api/token.php) から取得。

## エンドポイント一覧

### ユーザー情報

| メソッド | エンドポイント | 説明 |
|---------|---------------|------|
| GET | `/me` | 自分のアカウント情報を取得 |
| GET | `/my/status` | 未読数・タスク数などのステータス取得 |
| GET | `/my/tasks` | 自分に割り当てられたタスク一覧 |

### コンタクト

| メソッド | エンドポイント | 説明 |
|---------|---------------|------|
| GET | `/contacts` | コンタクト一覧を取得 |

### チャットルーム

| メソッド | エンドポイント | 説明 |
|---------|---------------|------|
| GET | `/rooms` | 参加しているルーム一覧 |
| POST | `/rooms` | グループチャットを作成 |
| GET | `/rooms/{room_id}` | ルーム情報を取得 |
| PUT | `/rooms/{room_id}` | ルーム情報を更新 |
| DELETE | `/rooms/{room_id}` | ルームを退席/削除 |

### メンバー

| メソッド | エンドポイント | 説明 |
|---------|---------------|------|
| GET | `/rooms/{room_id}/members` | メンバー一覧を取得 |
| PUT | `/rooms/{room_id}/members` | メンバーを変更 |

### メッセージ

| メソッド | エンドポイント | 説明 |
|---------|---------------|------|
| GET | `/rooms/{room_id}/messages` | メッセージ一覧を取得 |
| POST | `/rooms/{room_id}/messages` | メッセージを投稿 |
| GET | `/rooms/{room_id}/messages/{message_id}` | 特定メッセージを取得 |
| PUT | `/rooms/{room_id}/messages/{message_id}` | メッセージを編集 |
| DELETE | `/rooms/{room_id}/messages/{message_id}` | メッセージを削除 |
| PUT | `/rooms/{room_id}/messages/read` | メッセージを既読化 |
| PUT | `/rooms/{room_id}/messages/unread` | メッセージを未読化 |

### タスク

| メソッド | エンドポイント | 説明 |
|---------|---------------|------|
| GET | `/rooms/{room_id}/tasks` | タスク一覧を取得 |
| POST | `/rooms/{room_id}/tasks` | タスクを作成 |
| GET | `/rooms/{room_id}/tasks/{task_id}` | 特定タスクを取得 |
| PUT | `/rooms/{room_id}/tasks/{task_id}/status` | タスク完了状態を更新 |

### ファイル

| メソッド | エンドポイント | 説明 |
|---------|---------------|------|
| GET | `/rooms/{room_id}/files` | ファイル一覧を取得 |
| POST | `/rooms/{room_id}/files` | ファイルをアップロード |
| GET | `/rooms/{room_id}/files/{file_id}` | ファイル情報を取得 |

### 招待リンク

| メソッド | エンドポイント | 説明 |
|---------|---------------|------|
| GET | `/rooms/{room_id}/link` | 招待リンクを取得 |
| POST | `/rooms/{room_id}/link` | 招待リンクを作成 |
| PUT | `/rooms/{room_id}/link` | 招待リンクを更新 |
| DELETE | `/rooms/{room_id}/link` | 招待リンクを削除 |

## 使用例

### メッセージ送信
```
Chatwork APIで特定のルームにメッセージを送信するPythonコードを書いて
```

### タスク作成
```
Chatworkで複数メンバーにタスクを一括作成するコードを書いて
```

### 通知bot作成
```
エラー発生時にChatworkに通知するPython関数を書いて
```

## ガイドライン

### コード生成時の原則

1. **APIトークンは環境変数から取得**: ハードコードしない
2. **レート制限を考慮**: 300リクエスト/5分の制限あり
3. **エラーハンドリング**: 429(レート制限)、401(認証エラー)を適切に処理

### メッセージ記法

Chatwork独自の記法：
```
[info]情報ブロック[/info]
[info][title]タイトル付き[/title]本文[/info]
[To:account_id]メンション
[code]コードブロック[/code]
[hr]水平線
```

### 推奨ライブラリ

- **requests**: Python標準的なHTTPクライアント
- **pychatwork**: Python用Chatworkラッパー（非公式）

## 2025年7月の仕様変更

**重要**: 2025年7月3日以降、リクエストパラメータはbodyのみ読み込まれます。
クエリパラメータとbodyパラメータを併用していた場合は修正が必要です。

## 公式リソース

- [APIリファレンス](https://developer.chatwork.com/reference/)
- [開発者向けドキュメント](https://developer.chatwork.com/)
- [変更履歴](https://developer.chatwork.com/changelog/)
