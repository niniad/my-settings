---
name: gcp
description: GCP開発環境のセットアップと管理。gcloud CLI、Python SDKのインストール、認証設定、各GCPサービス（Cloud Storage、BigQuery、Secret Manager等）の操作支援。エラー発生時は自動診断・修復を実行。トリガー：GCPリソース操作、gcloudコマンド実行、GCS/BigQueryデータ処理、Cloud Runデプロイ、Schedulerジョブ管理、GCP認証エラー対応時。
user-invocable: true
allowed-tools:
  - Bash
  - Read
---

# GCP開発環境

## クイックリファレンス

| 操作 | コマンド |
|------|---------|
| 認証確認 | `gcloud auth list` |
| プロジェクト設定 | `gcloud config set project main-project-477501` |
| バケット一覧 | `gsutil ls` |
| クエリ実行 | `bq query --use_legacy_sql=false 'SQL'` |
| シークレット取得 | `gcloud secrets versions access latest --secret=NAME` |

## クイックスタート

### セットアップ実行
```bash
bash .claude/skills/gcp/setup.sh
```

### 環境診断
```bash
bash .claude/skills/gcp/scripts/diagnose.sh
```

### 認証修復
```bash
bash .claude/skills/gcp/scripts/fix-auth.sh
```

## 環境変数

| 変数名 | 必須 | 説明 |
|--------|------|------|
| `GOOGLE_APPLICATION_CREDENTIALS_JSON` | Web版 | サービスアカウントキー（JSON） |
| `GOOGLE_APPLICATION_CREDENTIALS` | ローカル | キーファイルのパス |
| `GCP_PROJECT_ID` | いいえ | プロジェクトID |

## 利用可能サービス

| サービス | CLI | Python SDK | 詳細 |
|---------|-----|------------|------|
| Cloud Storage | `gsutil` | google-cloud-storage | [storage.md](docs/storage.md) |
| BigQuery | `bq` | google-cloud-bigquery | [bigquery.md](docs/bigquery.md) |
| Secret Manager | `gcloud secrets` | google-cloud-secret-manager | [secrets.md](docs/secrets.md) |
| Cloud Run | `gcloud run` | google-cloud-run | [cloudrun.md](docs/cloudrun.md) |
| Cloud Scheduler | `gcloud scheduler` | google-cloud-scheduler | [scheduler.md](docs/scheduler.md) |

## プロジェクト固有設定

- **プロジェクトID**: `main-project-477501`
- **リージョン**: `us-central1`（Cloud Run / Scheduler）
- **サービスアカウント**: `claude-code-dev@main-project-477501.iam.gserviceaccount.com`

## トラブルシューティング

エラー発生時は診断スクリプトを実行：
```bash
bash .claude/skills/gcp/scripts/diagnose.sh
```

詳細: [troubleshooting.md](docs/troubleshooting.md)

### よくあるエラーの即時対応

```bash
# 認証エラー
gcloud auth login && gcloud auth application-default login

# プロジェクト未設定
gcloud config set project main-project-477501

# API未有効
gcloud services enable [SERVICE].googleapis.com
```

## スクリプト

| スクリプト | 用途 |
|-----------|------|
| `setup.sh` | 環境セットアップ |
| `scripts/diagnose.sh` | 問題診断 |
| `scripts/fix-auth.sh` | 認証修復 |
