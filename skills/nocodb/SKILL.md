---
name: nocodb
description: "NocoDB（ローカル SQLite + REST API）のデータ操作スキル。テーブル一覧の確認、データの読み取り・挿入・更新・削除、テーブル作成、カラム追加、ビュー管理などを実行する。トリガー：NocoDB、nocodb、テーブル操作、データ確認、レコード追加、DB操作に関する依頼時。"
---

# NocoDB 操作ガイド

## 概要

ローカルの NocoDB に対して、**REST API**（推奨）と **sqlite3**（高速読み取り）の2経路でデータ操作を行う。

| 経路 | 用途 | メタデータ更新 |
|------|------|---------------|
| REST API | 全操作（CRUD・スキーマ変更・ビュー管理） | あり（正常） |
| sqlite3 | 高速な読み取り・大量データの一括インポート | なし |

## 接続情報

- **API ベース URL**: `http://localhost:8080/api/v2`
- **API トークン**: GCP Secret Manager `NOCODB_API_TOKEN`（project: `main-project-477501`）
- **DB パス**: `C:/Users/ninni/nocodb/noco.db`
- **ブラウザ**: http://localhost:8080

### トークン取得方法

API 操作の前にトークンを取得してシェル変数に格納する:
```powershell
$NOCODB_TOKEN = (gcloud secrets versions access latest --secret=NOCODB_API_TOKEN --project=main-project-477501)[0].Trim()
```
以降の curl/Invoke-WebRequest で `xc-token` ヘッダに `$NOCODB_TOKEN` を使用する。

**注意**: gcloud 出力は配列になるため `[0].Trim()` が必要。

**bash（Claude Code 環境）:**
```bash
NOCODB_TOKEN=$(gcloud secrets versions access latest --secret=NOCODB_API_TOKEN --project=main-project-477501)
```

## 重要な注意事項

- **読み取りは自由に実行してよい**
- **書き込み（作成・更新・削除）は必ずユーザーに確認してから実行する**
- **スキーマ変更（テーブル作成・カラム追加等）も必ずユーザーに確認してから実行する**
- レート制限: 5リクエスト/秒（超過時は HTTP 429、30秒待機）

## 使い分けの方針

| やりたいこと | 使う経路 |
|-------------|---------|
| データを読む（数百件以下） | REST API |
| データを読む（大量・集計） | sqlite3 |
| レコードを追加・更新・削除 | REST API |
| テーブル作成・カラム追加 | REST API |
| ビュー管理 | REST API |
| 大量データの一括インポート | sqlite3 |

---

## REST API 操作

curl 共通ヘッダ:
```
-H "xc-token: $NOCODB_TOKEN" -H "Content-Type: application/json"
```

### 1. ベース一覧を取得

```bash
curl -s http://localhost:8080/api/v2/meta/bases/ \
  -H "xc-token: $NOCODB_TOKEN"
```

レスポンスの `list[].id` が Base ID（`p` プレフィックス）。

### 2. テーブル一覧を取得

```bash
curl -s http://localhost:8080/api/v2/meta/bases/{baseId}/tables \
  -H "xc-token: $NOCODB_TOKEN"
```

レスポンスの `list[].id` が Table ID（`m` プレフィックス）。

### 3. レコード一覧を取得

```bash
curl -s "http://localhost:8080/api/v2/tables/{tableId}/records?limit=25&offset=0" \
  -H "xc-token: $NOCODB_TOKEN"
```

クエリパラメータ:

| パラメータ | 説明 | 例 |
|-----------|------|-----|
| `limit` | 取得件数（デフォルト10） | `limit=100` |
| `offset` | オフセット | `offset=25` |
| `where` | フィルタ条件 | `where=(Status,eq,Active)` |
| `sort` | ソート（`-`で降順） | `sort=-CreatedAt` |
| `fields` | 取得カラム指定 | `fields=Title,Status` |

フィルタ演算子: `eq`, `neq`, `gt`, `ge`, `lt`, `le`, `like`, `nlike`, `is`, `isnot`, `in`, `btw`, `nbtw`, `allof`, `anyof`

### 4. レコードを作成（要ユーザー確認）

```bash
curl -s -X POST http://localhost:8080/api/v2/tables/{tableId}/records \
  -H "xc-token: $NOCODB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"Title": "値1", "Column2": "値2"}'
```

一括作成（配列で渡す）:
```bash
-d '[{"Title": "A"}, {"Title": "B"}, {"Title": "C"}]'
```

### 5. レコードを更新（要ユーザー確認）

ID はリクエストボディに含める（パスではない）:
```bash
curl -s -X PATCH http://localhost:8080/api/v2/tables/{tableId}/records \
  -H "xc-token: $NOCODB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"Id": 1, "Title": "新しい値"}'
```

### 6. レコードを削除（要ユーザー確認）

ID はリクエストボディに含める:
```bash
curl -s -X DELETE http://localhost:8080/api/v2/tables/{tableId}/records \
  -H "xc-token: $NOCODB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"Id": 1}'
```

### 7. テーブルを作成（要ユーザー確認）

```bash
curl -s -X POST http://localhost:8080/api/v2/meta/bases/{baseId}/tables \
  -H "xc-token: $NOCODB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "テーブル名",
    "columns": [
      {"title": "Title", "uidt": "SingleLineText"},
      {"title": "Status", "uidt": "SingleSelect", "dtxp": "Active,Inactive"}
    ]
  }'
```

主な `uidt`（カラム型）:

| uidt | 説明 |
|------|------|
| SingleLineText | 一行テキスト |
| LongText | 複数行テキスト |
| Number | 数値 |
| Decimal | 小数 |
| Checkbox | チェックボックス |
| SingleSelect | 単一選択 |
| MultiSelect | 複数選択 |
| Date | 日付 |
| DateTime | 日時 |
| Email | メール |
| URL | URL |
| Currency | 通貨 |
| Percent | パーセント |
| Duration | 期間 |
| Rating | 評価 |
| LinkToAnotherRecord | リレーション |
| Lookup | ルックアップ |
| Rollup | ロールアップ |
| Formula | 数式 |
| Attachment | 添付ファイル |

### 8. カラムを追加（要ユーザー確認）

```bash
curl -s -X POST http://localhost:8080/api/v2/meta/tables/{tableId}/columns \
  -H "xc-token: $NOCODB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "カラム名", "uidt": "SingleLineText"}'
```

SingleSelect のカラム追加（選択肢付き）:
```bash
-d '{"title": "Status", "uidt": "SingleSelect", "dtxp": "Active,Pending,Done"}'
```

### 9. ビュー一覧を取得

```bash
curl -s http://localhost:8080/api/v2/meta/tables/{tableId}/views \
  -H "xc-token: $NOCODB_TOKEN"
```

### 10. ビューを作成（要ユーザー確認）

Grid / Form / Gallery / Kanban:
```bash
curl -s -X POST http://localhost:8080/api/v2/meta/tables/{tableId}/grids \
  -H "xc-token: $NOCODB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "ビュー名"}'
```

エンドポイント: `/grids`, `/forms`, `/galleries`, `/kanbans`

### 11. ビューの共有リンクを作成

```bash
curl -s -X POST http://localhost:8080/api/v2/meta/views/{viewId}/share \
  -H "xc-token: $NOCODB_TOKEN" \
  -H "Content-Type: application/json"
```

---

## sqlite3 操作（高速読み取り用）

### テーブル一覧（UI名 → 実テーブル名のマッピング）

```bash
sqlite3 "C:/Users/ninni/nocodb/noco.db" "
  SELECT m.title AS ui_name, m.table_name AS real_table, m.id AS table_id
  FROM nc_models_v2 m
  JOIN nc_bases_v2 b ON m.base_id = b.id
  WHERE m.type = 'table'
    AND (m.deleted IS NULL OR m.deleted = 0)
    AND b.deleted = 0
  ORDER BY b.title, m.title;
"
```

### カラム定義（ユーザーカラムのみ）

```bash
sqlite3 -header -column "C:/Users/ninni/nocodb/noco.db" "
  SELECT c.title, c.column_name, c.uidt, c.dt
  FROM nc_columns_v2 c
  JOIN nc_models_v2 m ON c.fk_model_id = m.id
  WHERE m.title = '{UI表示名}'
    AND (c.system = 0 OR c.system IS NULL)
    AND (c.deleted IS NULL OR c.deleted = 0)
  ORDER BY c.\"order\";
"
```

### データ読み取り

```bash
sqlite3 -header -csv "C:/Users/ninni/nocodb/noco.db" "SELECT * FROM {real_table} LIMIT 100;"
```

出力フォーマット:

| 目的 | オプション |
|------|-----------|
| 整形テーブル | `-header -column` |
| CSV | `-header -csv` |
| JSON | `-json` |

### Select Options（ドロップダウン選択肢）

```bash
sqlite3 -header -column "C:/Users/ninni/nocodb/noco.db" "
  SELECT so.title, so.color
  FROM nc_col_select_options_v2 so
  JOIN nc_columns_v2 c ON so.fk_column_id = c.id
  JOIN nc_models_v2 m ON c.fk_model_id = m.id
  WHERE m.title = '{テーブルUI名}' AND c.title = '{カラムUI名}'
  ORDER BY so.\"order\";
"
```

---

## ID 体系

| 種類 | プレフィックス | 取得元 |
|------|--------------|--------|
| Base ID | `p` | `/api/v2/meta/bases/` |
| Table ID | `m` | `/api/v2/meta/bases/{baseId}/tables` |
| View ID | `vw` | `/api/v2/meta/tables/{tableId}/views` |
| Column ID | 英数字 | テーブル詳細のレスポンス内 |
| Record ID | 数字 | レコード取得のレスポンス内 `Id` |

---

## バックアップ

- 自動: 毎日 3:00 にタスクスケジューラが `backup-nocodb.bat` を実行
- 手動: `sqlite3 "C:/Users/ninni/nocodb/noco.db" ".backup 'G:\マイドライブ\backup\nocodb\noco_backup.db'"`

## NocoDB の起動・停止

- 起動: `C:\Users\ninni\nocodb\start-nocodb.bat` をダブルクリック（またはユーザーに依頼）
- 停止: コマンドプロンプトウィンドウを閉じる
- ブラウザ: http://localhost:8080

## トラブルシューティング

| 症状 | 対処 |
|------|------|
| `database is locked` | NocoDB が書き込み中。数秒待って再実行 |
| テーブルが見つからない | `/api/v2/meta/bases/{baseId}/tables` でテーブル一覧を再確認 |
| NocoDB に反映されない | ブラウザをリロード（F5） |
| `AUTHENTICATION_REQUIRED` | API トークンが正しいか確認 |
| HTTP 429 | レート制限。30秒待って再実行 |
| NocoDB が起動していない | `curl http://localhost:8080/api/v1/health` で確認。起動はユーザーに依頼 |
| 日本語が文字化け | `curl -o tmp/output.json` でファイルに保存してから Python で読む |
| `/tmp/` が見つからない | プロジェクトの `tmp/` ディレクトリを使用 |
