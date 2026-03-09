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

REST API エンドポイント詳細・sqlite3 クエリ: [references/api-reference.md](references/api-reference.md)

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
