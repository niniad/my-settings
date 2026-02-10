# Cloud Run

## 基本操作

### サービス一覧
```bash
gcloud run services list --region=us-central1
```

### サービス詳細
```bash
gcloud run services describe SERVICE_NAME --region=us-central1
```

### ログ確認
```bash
gcloud run services logs read SERVICE_NAME --region=us-central1 --limit=50
```

### サービスデプロイ
```bash
gcloud run deploy SERVICE_NAME \
  --source . \
  --region=us-central1 \
  --allow-unauthenticated
```

### サービス削除
```bash
gcloud run services delete SERVICE_NAME --region=us-central1
```

## 現在のサービス

| サービス名 | URL |
|-----------|-----|
| amazon-ads-cm-report-to-gcs | https://amazon-ads-cm-report-to-gcs-pwrkbqemcq-uc.a.run.app |
| amazon-ads-to-gcs-daily | https://amazon-ads-to-gcs-daily-pwrkbqemcq-uc.a.run.app |
| amazon-ads-v1-report | https://amazon-ads-v1-report-pwrkbqemcq-uc.a.run.app |
| spapi-to-gcs-daily | https://spapi-to-gcs-daily-pwrkbqemcq-uc.a.run.app |

## Python SDK

```python
from google.cloud import run_v2

client = run_v2.ServicesClient()
parent = "projects/main-project-477501/locations/us-central1"

# サービス一覧
for service in client.list_services(parent=parent):
    print(service.name)
```

## よくあるエラー

### Permission denied
```
サービスアカウントに権限を付与：
- roles/run.admin（管理）
- roles/run.invoker（実行）
```

### Service not found
```
リージョンを確認。--region=us-central1 を指定。
```
