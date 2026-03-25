# Eagle API リファレンス

Eagle ローカル API の全エンドポイント詳細仕様。

**ベースURL**: `http://localhost:41595`
**認証**: 不要（localhost のみ）
**形式**: JSON（POST は `Content-Type: application/json`）

---

## Application

### GET /api/application/info

Eagle アプリの情報を取得。接続確認に使用。

**レスポンス例**:
```json
{
  "status": "success",
  "data": {
    "version": "3.0.0",
    "prereleaseVersion": null,
    "buildVersion": "300",
    "execPath": "C:\\Program Files\\Eagle\\Eagle.exe",
    "platform": "win32"
  }
}
```

---

## Item（アイテム操作）

### POST /api/item/addFromURL

URLから画像1件を追加。

**リクエスト**:
```json
{
  "url": "https://example.com/image.jpg",
  "name": "画像名",
  "website": "https://example.com",
  "tags": ["タグ1", "タグ2"],
  "annotation": "メモ",
  "folderId": "フォルダID（省略可）"
}
```

**レスポンス**:
```json
{
  "status": "success",
  "data": { "id": "LXXXXXXXX" }
}
```

---

### POST /api/item/addFromURLs

URLから複数画像を一括追加。

**リクエスト**:
```json
{
  "items": [
    {
      "url": "https://example.com/image1.jpg",
      "name": "画像1",
      "tags": ["タグ1"]
    },
    {
      "url": "https://example.com/image2.jpg",
      "name": "画像2",
      "tags": ["タグ2"]
    }
  ],
  "folderId": "フォルダID（省略可）"
}
```

**レスポンス**:
```json
{ "status": "success" }
```

---

### POST /api/item/addFromPath

ローカルファイル1件を追加。

**リクエスト**:
```json
{
  "path": "C:\\Users\\ninni\\Pictures\\image.png",
  "name": "画像名",
  "tags": ["タグ1"],
  "annotation": "メモ",
  "folderId": "フォルダID（省略可）"
}
```

**レスポンス**:
```json
{
  "status": "success",
  "data": { "id": "LXXXXXXXX" }
}
```

---

### POST /api/item/addFromPaths

ローカルファイルを複数一括追加。

**リクエスト**:
```json
{
  "items": [
    {
      "path": "C:\\Users\\ninni\\Pictures\\image1.png",
      "name": "画像1",
      "tags": ["タグ1"]
    }
  ],
  "folderId": "フォルダID（省略可）"
}
```

---

### POST /api/item/addBookmark

ブックマーク（URL リンク）を追加。

**リクエスト**:
```json
{
  "url": "https://example.com",
  "name": "サイト名",
  "base64": "base64エンコードのサムネイル（省略可）",
  "tags": ["タグ1"],
  "folderId": "フォルダID（省略可）"
}
```

---

### GET /api/item/info

アイテムIDで詳細情報を取得。

**クエリパラメータ**: `id=LXXXXXXXX`

**例**: `GET /api/item/info?id=LXXXXXXXX`

**レスポンス**:
```json
{
  "status": "success",
  "data": {
    "id": "LXXXXXXXX",
    "name": "画像名",
    "size": 102400,
    "ext": "jpg",
    "tags": ["タグ1", "タグ2"],
    "folders": ["フォルダID"],
    "isDeleted": false,
    "url": "https://example.com/image.jpg",
    "annotation": "メモ",
    "modificationTime": 1700000000000,
    "width": 1920,
    "height": 1080,
    "star": 0,
    "palettes": []
  }
}
```

---

### GET /api/item/thumbnail

アイテムのサムネイルファイルパスを取得。

**クエリパラメータ**: `id=LXXXXXXXX`

**例**: `GET /api/item/thumbnail?id=LXXXXXXXX`

**レスポンス**:
```json
{
  "status": "success",
  "data": "C:\\Eagle Library\\Library.library\\images\\LXXXXXXXX.info\\LXXXXXXXX_thumbnail.png"
}
```

---

### GET /api/item/list

アイテム一覧を検索・フィルタリングして取得。

**クエリパラメータ**:

| パラメータ | 型 | 説明 |
|-----------|-----|------|
| `limit` | number | 取得件数（デフォルト: 200） |
| `offset` | number | オフセット（ページング） |
| `orderBy` | string | ソート順（`CREATEDATE`/`FILESIZE`/`NAME`/`RESOLUTION`） |
| `keyword` | string | キーワード検索 |
| `ext` | string | 拡張子フィルタ（`jpg`/`png` 等） |
| `tags` | string | タグフィルタ（カンマ区切り） |
| `folders` | string | フォルダIDフィルタ（カンマ区切り） |
| `star` | number | スター数フィルタ（1〜5） |

**例**: `GET /api/item/list?limit=20&orderBy=CREATEDATE&keyword=デザイン`

**レスポンス**:
```json
{
  "status": "success",
  "data": [
    {
      "id": "LXXXXXXXX",
      "name": "画像名",
      "ext": "jpg",
      "tags": ["タグ1"],
      "folders": ["フォルダID"],
      "width": 1920,
      "height": 1080,
      "size": 102400,
      "star": 0,
      "url": "https://example.com/image.jpg",
      "annotation": "メモ",
      "modificationTime": 1700000000000
    }
  ]
}
```

---

### POST /api/item/update

アイテムのメタデータを更新。

**リクエスト**:
```json
{
  "id": "LXXXXXXXX",
  "tags": ["新タグ1", "新タグ2"],
  "annotation": "更新したメモ",
  "star": 3,
  "url": "https://new-url.com"
}
```

---

### POST /api/item/moveToTrash

アイテムをゴミ箱に移動（**削除操作: 確認必須**）。

**リクエスト**:
```json
{
  "itemIds": ["LXXXXXXXX", "LYYYYYYYY"]
}
```

---

### GET /api/item/refreshPalette

アイテムのカラーパレットを再生成。

**クエリパラメータ**: `id=LXXXXXXXX`

---

### GET /api/item/refreshThumbnail

アイテムのサムネイルを再生成。

**クエリパラメータ**: `id=LXXXXXXXX`

---

## Folder（フォルダ操作）

### POST /api/folder/create

フォルダを新規作成。

**リクエスト**:
```json
{
  "folderName": "新フォルダ名",
  "parent": "親フォルダID（省略で最上位）"
}
```

**レスポンス**:
```json
{
  "status": "success",
  "data": {
    "id": "FXXXXXXXX",
    "name": "新フォルダ名",
    "description": "",
    "children": [],
    "modificationTime": 1700000000000,
    "imageCount": 0,
    "descendantImageCount": 0
  }
}
```

---

### POST /api/folder/rename

フォルダ名を変更。

**リクエスト**:
```json
{
  "folderId": "FXXXXXXXX",
  "newName": "新しいフォルダ名"
}
```

---

### POST /api/folder/update

フォルダの設定を更新（色・説明など）。

**リクエスト**:
```json
{
  "folderId": "FXXXXXXXX",
  "newName": "フォルダ名",
  "newDescription": "説明文",
  "newColor": "red"
}
```

**color の値**: `red` / `orange` / `yellow` / `green` / `cyan` / `blue` / `purple` / `pink`

---

### GET /api/folder/list

フォルダ一覧（ツリー構造）を取得。

**例**: `GET /api/folder/list`

**レスポンス**:
```json
{
  "status": "success",
  "data": [
    {
      "id": "FXXXXXXXX",
      "name": "フォルダ名",
      "description": "",
      "children": [
        {
          "id": "FYYYYYYYY",
          "name": "サブフォルダ"
        }
      ],
      "imageCount": 42,
      "descendantImageCount": 50
    }
  ]
}
```

---

### GET /api/folder/listRecent

最近使ったフォルダ一覧を取得。

**例**: `GET /api/folder/listRecent`

---

## Library（ライブラリ操作）

### GET /api/library/info

現在開いているライブラリの情報を取得。

**レスポンス**:
```json
{
  "status": "success",
  "data": {
    "folders": [...],
    "smartFolders": [...],
    "quickAccess": [...],
    "tagsWithFolder": [...],
    "modificationTime": 1700000000000,
    "applicationVersion": "3.0.0",
    "library": {
      "path": "C:\\Eagle Library\\Library.library",
      "name": "Library"
    }
  }
}
```

---

### GET /api/library/history

過去に開いたライブラリの一覧を取得。

**レスポンス**:
```json
{
  "status": "success",
  "data": [
    {
      "path": "C:\\Eagle Library\\Library.library",
      "name": "Library"
    }
  ]
}
```

---

### POST /api/library/switch

別のライブラリに切り替え（**操作: 確認推奨**）。

**リクエスト**:
```json
{
  "libraryPath": "C:\\Eagle Library\\AnotherLibrary.library"
}
```

---

### GET /api/library/icon

ライブラリのアイコン画像を取得。

**クエリパラメータ**: `libraryPath=<URLエンコードされたパス>`

**例**: `GET /api/library/icon?libraryPath=C%3A%5CEagle%20Library%5CLibrary.library`

---

## エラーハンドリング

### Eagle が起動していない場合

```
curl: (7) Failed to connect to localhost port 41595: Connection refused
```

→ Eagle アプリを起動してから再試行。

### よくあるエラーレスポンス

```json
{ "status": "error", "message": "エラー内容" }
```

---

## Windows パス注意事項

JSON 内でのパス記述はバックスラッシュをエスケープ:
```json
{ "path": "C:\\Users\\ninni\\Pictures\\image.png" }
```

curl コマンドでは二重エスケープが必要な場合がある:
```bash
curl -X POST http://localhost:41595/api/item/addFromPath \
  -H "Content-Type: application/json" \
  -d "{\"path\": \"C:\\\\Users\\\\ninni\\\\Pictures\\\\image.png\", \"name\": \"テスト\"}"
```
