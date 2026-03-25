---
name: eagle
description: Eagle（画像管理アプリ）をAPIで操作するスキル。画像の検索・追加・タグ付け・フォルダ整理・ライブラリ管理をClaude Codeから自然言語で実行できる。トリガー：「Eagleで」「Eagleに保存」「Eagleを検索」「Eagle操作」「画像をEagleに追加」「Eagleフォルダ」「Eagleライブラリ」
user-invocable: true
allowed-tools:
  - Bash
---

# Eagle API 操作スキル

## 概要

| 項目 | 値 |
|------|-----|
| API URL | `http://localhost:41595` |
| 認証 | 不要（localhost のみ） |
| 前提 | Eagle アプリが起動していること |
| 形式 | JSON |

Eagle は起動中に自動でローカル HTTP サーバーを立ち上げる。**Eagle が起動していないと全 API が失敗する。**

詳細仕様: `C:/Users/ninni/.claude/skills/eagle/references/api-reference.md`

---

## Step 0: 接続確認（必須）

操作前に必ず疎通チェックを行う:

```bash
curl -s http://localhost:41595/api/application/info
```

**成功**: `{"status":"success","data":{...}}` → 操作を続行
**失敗** (`Connection refused`): Eagle を起動するよう案内してから中断

---

## 操作カテゴリ別ガイド

### 🔍 検索・閲覧

**アイテム一覧（最近20件）**:
```bash
curl -s "http://localhost:41595/api/item/list?limit=20&orderBy=CREATEDATE"
```

**キーワード検索**:
```bash
curl -s "http://localhost:41595/api/item/list?keyword=検索語&limit=20"
```

**タグで絞り込み**:
```bash
curl -s "http://localhost:41595/api/item/list?tags=デザイン,参考&limit=20"
```

**特定フォルダ内を検索**:
```bash
curl -s "http://localhost:41595/api/item/list?folders=FXXXXXXXX&limit=50"
```

**アイテム詳細**:
```bash
curl -s "http://localhost:41595/api/item/info?id=LXXXXXXXX"
```

---

### ➕ 追加

**URL から画像を追加**:
```bash
curl -s -X POST http://localhost:41595/api/item/addFromURL \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/image.jpg", "name": "画像名", "tags": ["タグ1"], "folderId": "FXXXXXXXX"}'
```

**複数 URL を一括追加**:
```bash
curl -s -X POST http://localhost:41595/api/item/addFromURLs \
  -H "Content-Type: application/json" \
  -d '{"items": [{"url": "https://example.com/1.jpg", "name": "画像1"}, {"url": "https://example.com/2.jpg", "name": "画像2"}], "folderId": "FXXXXXXXX"}'
```

**ローカルファイルを追加**:
```bash
curl -s -X POST http://localhost:41595/api/item/addFromPath \
  -H "Content-Type: application/json" \
  -d "{\"path\": \"C:\\\\Users\\\\ninni\\\\Pictures\\\\image.png\", \"name\": \"画像名\", \"tags\": [\"タグ1\"]}"
```

**ブックマーク（URL リンク）を追加**:
```bash
curl -s -X POST http://localhost:41595/api/item/addBookmark \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "name": "サイト名", "tags": ["参考"]}'
```

---

### ✏️ 更新（タグ・メモ・スター）

```bash
curl -s -X POST http://localhost:41595/api/item/update \
  -H "Content-Type: application/json" \
  -d '{"id": "LXXXXXXXX", "tags": ["新タグ1", "新タグ2"], "annotation": "メモ内容", "star": 3}'
```

`star` は 0〜5 の整数。

---

### 🗂️ フォルダ操作

**フォルダ一覧**:
```bash
curl -s http://localhost:41595/api/folder/list
```

**フォルダ作成**:
```bash
curl -s -X POST http://localhost:41595/api/folder/create \
  -H "Content-Type: application/json" \
  -d '{"folderName": "新フォルダ名"}'
```

**サブフォルダ作成（親フォルダ指定）**:
```bash
curl -s -X POST http://localhost:41595/api/folder/create \
  -H "Content-Type: application/json" \
  -d '{"folderName": "サブフォルダ名", "parent": "親フォルダID"}'
```

**フォルダ名変更**:
```bash
curl -s -X POST http://localhost:41595/api/folder/rename \
  -H "Content-Type: application/json" \
  -d '{"folderId": "FXXXXXXXX", "newName": "新しい名前"}'
```

**フォルダ色・説明を更新**:
```bash
curl -s -X POST http://localhost:41595/api/folder/update \
  -H "Content-Type: application/json" \
  -d '{"folderId": "FXXXXXXXX", "newColor": "blue", "newDescription": "説明文"}'
```
色: `red` / `orange` / `yellow` / `green` / `cyan` / `blue` / `purple` / `pink`

---

### 📚 ライブラリ操作

**現在のライブラリ情報**:
```bash
curl -s http://localhost:41595/api/library/info
```

**過去のライブラリ一覧**:
```bash
curl -s http://localhost:41595/api/library/history
```

---

### 🗑️ 削除（確認必須）

アイテムをゴミ箱に移動する操作は**必ずユーザーに確認してから実行**:

```bash
curl -s -X POST http://localhost:41595/api/item/moveToTrash \
  -H "Content-Type: application/json" \
  -d '{"itemIds": ["LXXXXXXXX"]}'
```

---

## 出力フォーマット

検索結果は見やすい表形式で表示する:

| ID | 名前 | タグ | 追加日 |
|----|------|------|--------|
| LXXXXXXXX | 画像名 | タグ1, タグ2 | 2026-03-16 |

- `modificationTime` は Unix ミリ秒 → 日付変換して表示
- 大量結果（20件以上）は先頭20件を表示し、件数を明示

---

## 注意事項

1. **Eagle 未起動時**: Step 0 でエラーを検出 → 「Eagleを起動してください」と案内して中断
2. **Windows パス**: JSON 内はバックスラッシュをダブルエスケープ（`\\\\`）
3. **フォルダ ID 確認**: フォルダ操作前に `folder/list` で ID を確認してから実行
4. **ライブラリ切り替え**: `library/switch` は現在の作業に影響するため確認推奨
5. **削除操作**: `moveToTrash` は実行前にアイテム名を表示してユーザー確認を取る
