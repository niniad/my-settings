# Cloud Scheduler

## 基本操作

### ジョブ一覧
```bash
gcloud scheduler jobs list --location=us-central1
```

### ジョブ詳細
```bash
gcloud scheduler jobs describe JOB_NAME --location=us-central1
```

### ジョブ手動実行
```bash
gcloud scheduler jobs run JOB_NAME --location=us-central1
```

### ジョブ一時停止
```bash
gcloud scheduler jobs pause JOB_NAME --location=us-central1
```

### ジョブ再開
```bash
gcloud scheduler jobs resume JOB_NAME --location=us-central1
```

### ジョブ作成（HTTP）
```bash
gcloud scheduler jobs create http JOB_NAME \
  --location=us-central1 \
  --schedule="0 10 * * *" \
  --uri="https://example.com/endpoint" \
  --http-method=POST
```

### ジョブ削除
```bash
gcloud scheduler jobs delete JOB_NAME --location=us-central1
```

## 現在のジョブ

| ジョブ名 | スケジュール | 状態 |
|---------|------------|------|
| spapi-to-gcs-daily-job | 0 10 * * * (毎日10:00 UTC) | ENABLED |
| amazon-ads-to-gcs-daily-job | 0 10 * * * (毎日10:00 UTC) | ENABLED |
| amazon-ads-v1-report-daily-job | 30 10 * * * (毎日10:30 UTC) | ENABLED |

## Cron式の例

| 式 | 説明 |
|----|------|
| `0 10 * * *` | 毎日10:00 |
| `30 10 * * *` | 毎日10:30 |
| `0 */6 * * *` | 6時間ごと |
| `0 9 * * 1-5` | 平日9:00 |
| `0 0 1 * *` | 毎月1日0:00 |

## Python SDK

```python
from google.cloud import scheduler_v1

client = scheduler_v1.CloudSchedulerClient()
parent = "projects/main-project-477501/locations/us-central1"

# ジョブ一覧
for job in client.list_jobs(parent=parent):
    print(f"{job.name}: {job.schedule}")
```

## よくあるエラー

### Job not found
```
リージョンを確認。--location=us-central1 を指定。
```

### Permission denied
```
サービスアカウントに権限を付与：
- roles/cloudscheduler.admin
```
